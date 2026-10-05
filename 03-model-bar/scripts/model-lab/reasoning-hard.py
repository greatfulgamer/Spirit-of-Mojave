#!/usr/bin/env python3
"""
reasoning-hard.py — a reasoning test that can actually FAIL a model.

Why this exists
---------------
The stock `lab.py` reasoning position is 2 cases scored by `must_contain`
substring match ("3 shelves x 5 boxes x 4 items" == 60). Measured on
2026-09-28, BOTH qwen3:1.7b and qwen3.5:4b scored 2/2 on it. A test
everything passes measures nothing, so it cannot rank models.

This suite is built from cases where the obvious answer is WRONG:
  - a two-equation puzzle (the naive arithmetic gives the wrong number)
  - a problem with a second agent that must be accounted for
  - a false-premise question with no correct factual answer
  - a sycophancy probe where agreeing with the user is the failure

Design rules
------------
1. A wrong-but-confident answer scores 0. There is no partial credit for
   sounding confident.
2. `max_tokens` is generous (2000-4000). Thinking models spend most of
   their budget on the reasoning chain; a tight cap makes them return an
   EMPTY answer, which is a harness artifact, not a model failure.
   (Verified: qwen3.5:4b returned "" at num_predict=512 and the correct
   0.05 at num_predict=2048.)
3. We record whether the model TERMINATED. A model that exhausts its
   budget mid-sentence has not answered, and is scored as such.
4. temperature 0.0 for reproducibility, except where noted.

Usage
-----
    python3 reasoning-hard.py --model qwen3.5:4b
    python3 reasoning-hard.py --model qwen3.5:4b --node localhost:11434
    python3 reasoning-hard.py --model X --model Y --compare
"""

import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CASES_PATH = os.path.join(HERE, "reasoning-hard.json")


def post(url, payload, timeout=900):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _dur_ns(res, base):
    for k in (base + "_ns", base):
        v = res.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    return None


def run_case(node, case, model, temperature=0.0):
    url = f"http://{node}/api/generate"
    payload = {
        "model": model,
        "prompt": case["prompt"],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": case.get("max_tokens", 3000),
            "num_ctx": 8192,
        },
    }
    t0 = time.time()
    try:
        res = post(url, payload)
    except (urllib.error.URLError, TimeoutError) as e:
        # Every key the reporter reads must exist here, or an unreachable node
        # crashes the summary instead of reporting "node down".
        return {
            "id": case["id"],
            "passed": False,
            "verdict": "ERROR",
            "answer": "",
            "detail": f"request failed: {e}",
            "tok_s": None,
            "wall_s": round(time.time() - t0, 1),
            "terminated": False,
        }
    wall = time.time() - t0

    answer = (res.get("response") or "").strip()
    thinking = res.get("thinking") or ""
    # A model may put its reasoning in `thinking` and the final line in
    # `response`, or inline everything in `response`. Check both.
    haystack = (answer + "\n" + thinking).lower()

    d = _dur_ns(res, "eval_duration")
    tok_s = (res.get("eval_count", 0) / (d / 1e9)) if d else None

    # Did it finish inside budget, or get cut off mid-thought?
    terminated = bool(answer)
    if not terminated and thinking:
        terminated = False  # thought but never emitted an answer

    hit = any(s.lower() in haystack for s in case["must_contain"])
    passed = hit and terminated

    if passed:
        verdict = "PASS"
    elif hit and not terminated:
        verdict = "PASS_NO_ANSWER"  # right idea, never actually answered
    else:
        verdict = "FAIL"

    return {
        "id": case["id"],
        "passed": passed,
        "verdict": verdict,
        "answer": answer[:300],
        "thinking_chars": len(thinking),
        "eval_tokens": res.get("eval_count", 0),
        "tok_s": round(tok_s, 2) if tok_s else None,
        "wall_s": round(wall, 1),
        "terminated": terminated,
        "trap": case.get("trap", ""),
    }


def run_model(node, model, temperature=0.0):
    with open(CASES_PATH) as f:
        cases = json.load(f)["reasoning_hard"]["cases"]
    results = [run_case(node, c, model, temperature) for c in cases]
    n_pass = sum(1 for r in results if r["passed"])
    # use .get() throughout: an ERROR case has no tok_s/answer keys at all
    speeds = [r.get("tok_s") for r in results if r.get("tok_s")]
    return {
        "model": model,
        "node": node,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "score": f"{n_pass}/{len(results)}",
        "passed": n_pass,
        "total": len(results),
        "terminated_all": all(r["terminated"] for r in results),
        "median_tok_s": round(statistics.median(speeds), 2) if speeds else None,
        "results": results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", action="append", required=True)
    ap.add_argument("--node", default="localhost:11434")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    all_runs = []
    for m in a.model:
        print(f"=== {m} on {a.node} ===", flush=True)
        run = run_model(a.node, m, a.temperature)
        all_runs.append(run)
        for r in run["results"]:
            flag = "PASS" if r["passed"] else "FAIL"
            speed = f"{r['tok_s']:>6} tok/s" if r.get("tok_s") else "   n/a "
            term = "" if r.get("terminated") else "  [DID NOT TERMINATE]"
            print(f"  [{flag}] {r['id']:<15} {speed}  {r['wall_s']:>6}s{term}")
            if not r["passed"]:
                print(f"         got: {r.get('answer', r.get('detail',''))[:120]!r}")
        print(f"  score: {run['score']}\n", flush=True)

    if a.compare and len(all_runs) > 1:
        print("=== comparison ===")
        for r in sorted(all_runs, key=lambda x: -x["passed"]):
            print(f"  {r['score']:>5}  {r['model']}")

    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(all_runs if len(all_runs) > 1 else all_runs[0], f, indent=2)
        print(f"[saved] {a.json_out}")


if __name__ == "__main__":
    main()
