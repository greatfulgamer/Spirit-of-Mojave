#!/usr/bin/env python3
"""
GX-9000 Model Lab — prove what actually works on the fleet.

Self-contained benchmark harness for Ollama (and llama.cpp-compatible)
endpoints. Tests "framework positions" that combine raw speed with task
effectiveness so you can route the right model to the right job.

Stdlib only — runs on any fleet node with python3. No pip installs.

Usage:
    python3 lab.py list                      # list positions + targets
    python3 lab.py run --node localhost:11434 --model qwen3:14b
    python3 lab.py run --node host:11434 --model qwen3.5:35b-a3b \
                       --positions speed,toolcall
    python3 lab.py report projects/model-lab/results/<run>.json

Exit code 0 on success.
"""

import argparse
import json
import os
import statistics
import sys
import time
import urllib.request

STDERR = sys.stderr


# ---------------------------------------------------------------------------
# Ollama REST client (thin)
# ---------------------------------------------------------------------------
class Ollama:
    def __init__(self, base):
        if "://" not in base:
            base = "http://" + base
        self.base = base.rstrip("/")

    def _post(self, path, payload, timeout=180):
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def version(self):
        req = urllib.request.Request(self.base + "/api/version")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode()).get("version", "?")

    def list(self):
        out = []
        for m in self._post("/api/tags", {}).get("models", []):
            out.append((m.get("name"), m.get("size")))
        return out

    def generate(self, model, prompt, options=None, timeout=600):
        payload = {"model": model, "prompt": prompt, "stream": False,
                   "options": options or {}}
        t0 = time.time()
        res = self._post("/api/generate", payload, timeout=timeout)
        dt = time.time() - t0
        # Ollama's duration key names are inconsistent across builds: some emit
        # `eval_duration_ns`, others plain `eval_duration`. Both are nanoseconds.
        # Normalize to the unsuffixed name here and drop the key entirely when
        # absent, so a missing duration surfaces as "unknown" rather than 0.
        def _dur(base):
            for k in (base + "_ns", base):
                v = res.get(k)
                if isinstance(v, (int, float)) and v > 0:
                    return float(v)
            return None

        out = {
            "text": res.get("response", ""),
            "elapsed_s": dt,
            "eval_count": res.get("eval_count", 0),
            "prompt_eval_count": res.get("prompt_eval_count", 0),
            "total_duration": _dur("total_duration"),
        }
        d = _dur("eval_duration")
        p = _dur("prompt_eval_duration")
        if d is not None:
            out["eval_duration"] = d
        if p is not None:
            out["prompt_eval_duration"] = p
        return out

    def chat(self, model, messages, options=None, timeout=600):
        payload = {"model": model, "messages": messages, "stream": False,
                   "options": options or {}}
        t0 = time.time()
        res = self._post("/api/chat", payload, timeout=timeout)
        dt = time.time() - t0
        return {
            "text": res.get("message", {}).get("content", ""),
            "elapsed_s": dt,
            "eval_count": res.get("eval_count", 0),
            "eval_duration_ns": res.get("eval_duration_ns", 0),
        }


# ---------------------------------------------------------------------------
# Positions: each returns a dict of metrics + a normalized "effectiveness"
# ---------------------------------------------------------------------------
def _dur_ns(resp, base):
    """Ollama reports durations under inconsistent key names across builds:
    some emit `eval_duration_ns`, others `eval_duration`. Both are nanoseconds.
    Reading the wrong one silently yields `(None or 1)` = 1ns, which produces
    absurd tok/s (billions) instead of an error. Accept either spelling."""
    for k in (base + "_ns", base):
        v = resp.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    return None


def score_speed(o, model, prompts, options):
    metrics = {}
    # prompt eval (prefill) t/s
    p = prompts["speed"]["prefill"]
    r = o.generate(model, p, options=options)
    pe = r["prompt_eval_count"] or 1
    p_ns = _dur_ns(r, "prompt_eval_duration")
    p_sec = p_ns / 1e9 if p_ns else None
    # Unknown duration must be reported, not invented. Never fall back to 1ns.
    metrics["prefill_tok_s"] = round(pe / p_sec, 2) if p_sec else None
    metrics["prefill_duration_known"] = p_sec is not None

    # decode t/s over N repeats of a generative prompt
    d_rates = []
    for _ in range(prompts["speed"]["decode_repeats"]):
        rr = o.generate(model, prompts["speed"]["decode"], options=options)
        n = rr["eval_count"] or 1
        d_ns = _dur_ns(rr, "eval_duration")
        if d_ns:
            d_rates.append(n / (d_ns / 1e9))
    metrics["decode_tok_s"] = round(statistics.median(d_rates), 2) if d_rates else None
    metrics["decode_samples"] = len(d_rates)

    t_ns = r.get("total_duration")
    if t_ns and p_sec:
        metrics["ttft_s"] = round(t_ns / 1e9 - p_sec, 3)
    else:
        metrics["ttft_s"] = None
    # decode dominates perceived interactivity.
    # If decode speed is unknown we cannot score it - report 0 effectiveness
    # rather than silently crediting a perfect 1.0 (which is what the old
    # `(None or 1)` path produced, and it inflated fleet_score to a perfect 1.0).
    d = metrics["decode_tok_s"]
    eff = min(1.0, d / 60.0) if d else 0.0
    return metrics, eff


def score_capacity(o, model, prompts, options):
    # Simple heuristic: does the model stream without error, and how big?
    r = o.generate(model, prompts["capacity"]["smoke"], options=options)
    ok = bool(r["text"])
    # derive approx weight size from the response metadata is not possible;
    # use a probe of whether a larger context still fits.
    metrics = {
        "loads": ok,
        "first_token_s": round(r["elapsed_s"], 3),
    }
    eff = 1.0 if ok else 0.0
    return metrics, eff


def score_toolcall(o, model, prompts, options):
    passed = 0
    total = 0
    for tc in prompts["toolcall"]["cases"]:
        msgs = [{"role": "user", "content": tc["prompt"]}]
        r = o.chat(model, msgs, options=options)
        text = r["text"]
        total += 1
        # every expected key must appear as `"key": value`
        if all(_tool_hit(text, k) for k in tc["expect_keys"]):
            passed += 1
    metrics = {"toolcall_pass": passed, "toolcall_total": total}
    eff = passed / total if total else 0.0
    return metrics, eff


def _tool_hit(text, key):
    # matches `"key" :` or `key: ` in emitted JSON/object
    return ('"%s"' % key) in text or (key + ":") in text


def score_reasoning(o, model, prompts, options):
    passed = 0
    total = 0
    for rc in prompts["reasoning"]["cases"]:
        r = o.generate(model, rc["prompt"], options=options)
        text = r["text"]
        total += 1
        if any(needle.lower() in text.lower() for needle in rc["must_contain"]):
            passed += 1
    metrics = {"reasoning_pass": passed, "reasoning_total": total}
    eff = passed / total if total else 0.0
    return metrics, eff


def score_guardrail(o, model, prompts, options):
    passed = 0
    total = 0
    for gc in prompts["guardrail"]["cases"]:
        r = o.generate(model, gc["prompt"], options=options)
        text = r["text"].lower()
        total += 1
        blocked = any(n in text for n in gc["should_block_if_contains"])
        if gc["expect_block"] and blocked:
            passed += 1
        elif not gc["expect_block"] and not blocked:
            passed += 1
    metrics = {"guardrail_pass": passed, "guardrail_total": total}
    eff = passed / total if total else 0.0
    return metrics, eff


POSITIONS = {
    "speed": score_speed,
    "capacity": score_capacity,
    "toolcall": score_toolcall,
    "reasoning": score_reasoning,
    "guardrail": score_guardrail,
}

WEIGHTS = {"speed": 0.3, "capacity": 0.1, "toolcall": 0.3,
           "reasoning": 0.2, "guardrail": 0.1}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_positions(o, model, positions, prompts, options):
    results = {}
    effs = {}
    for name in positions:
        fn = POSITIONS[name]
        try:
            metrics, eff = fn(o, model, prompts, options)
            results[name] = metrics
            effs[name] = eff
        except Exception as e:  # noqa
            results[name] = {"error": str(e)}
            effs[name] = 0.0
    fleet_score = sum(WEIGHTS.get(p, 0) * effs.get(p, 0)
                      for p in positions)
    denom = sum(WEIGHTS.get(p, 0) for p in positions) or 1.0
    fleet_score = round(fleet_score / denom, 3)
    return results, effs, fleet_score


def load_prompts(path):
    with open(path) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="GX-9000 Model Lab")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    run = sub.add_parser("run")
    run.add_argument("--node", required=True, help="host[:port]")
    run.add_argument("--model", required=True)
    run.add_argument("--positions",
                     default=",".join(POSITIONS.keys()))
    run.add_argument("--prompts", default=_prompts_path())
    run.add_argument("--outdir", default=_default_results())
    run.add_argument("--temp", type=float, default=0.0)
    run.add_argument("--num-ctx", type=int, default=4096)

    rep = sub.add_parser("report")
    rep.add_argument("file")

    args = ap.parse_args()

    if args.cmd == "list":
        print("Positions:")
        for k in POSITIONS:
            print(f"  {k:10s} -> {WEIGHTS.get(k,0)} weight")
        print("Prompts file:", _prompts_path())
        print("Targets: see targets.json")
        return 0

    if args.cmd == "report":
        with open(args.file) as f:
            d = json.load(f)
        print(f"Model: {d.get('model')} @ {d.get('node')}")
        print(f"Fleet-fit score: {d.get('fleet_score')}")
        for pos, m in d.get("results", {}).items():
            print(f"  [{pos}] {m}")
        return 0

    # run
    prompts = load_prompts(args.prompts)
    positions = [p.strip() for p in args.positions.split(",")
                 if p.strip() in POSITIONS]
    options = {"temperature": args.temp, "num_ctx": args.num_ctx}

    o = Ollama(args.node)
    print(f"node={args.node} model={args.model} "
          f"ollama={o.version()} positions={positions}", file=STDERR)
    results, effs, fleet_score = run_positions(
        o, args.model, positions, prompts, options)

    run = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "node": args.node,
        "model": args.model,
        "options": options,
        "results": results,
        "effectiveness": effs,
        "fleet_score": fleet_score,
    }
    os.makedirs(args.outdir, exist_ok=True)
    name = f"{args.model.replace(':', '-')}.json"
    path = os.path.join(args.outdir, name)
    with open(path, "w") as f:
        json.dump(run, f, indent=2)
    print(json.dumps(run, indent=2))
    print(f"\n[saved] {path}")
    return 0


def _prompts_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "prompts.json")


def _default_results():
    base = os.path.expanduser("~/NCR-RobCo-GX-9000-Mainframe")
    return os.path.join(base, "projects", "model-lab", "results")


if __name__ == "__main__":
    sys.exit(main())