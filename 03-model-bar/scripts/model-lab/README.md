# GX-9000 Model Lab

Prove what actually works on the fleet. Measures speed **and** task
effectiveness per model/node, then combines them into a **fleet-fit score** so
you can route the right model to the right job instead of guessing.

## Quick start
```bash
# list positions and prompts
python3 lab.py list

# run one model through all positions (writes JSON result)
python3 lab.py run --node localhost:11434 --model qwen3:14b

# run specific positions
python3 lab.py run --node host:11434 --model qwen3.5:35b-a3b --positions speed,toolcall

# read a saved result
python3 lab.py report projects/model-lab/results/qwen3-14b.json
```

## Positions (framework) — what we measure
| Position | What it proves | Weight |
|----------|----------------|--------|
| `speed` | prefill t/s, decode t/s, TTFT | 0.30 |
| `capacity` | model loads, first-token latency | 0.10 |
| `toolcall` | JSON / function-calling correctness (agent-critical) | 0.30 |
| `reasoning` | arithmetic / logic quality | 0.20 |
| `guardrail` | blocks harmful requests, doesn't over-refuse | 0.10 |

`fleet_score` = weighted blend (0.0–1.0). Higher = better fit for agentic work.

## Notes
- Stdlib only — runs on any fleet node, no pip installs.
- Talks to Ollama REST (`/api/generate`, `/api/chat`). Also works against any
  OpenAI-compatible / llama.cpp server that exposes the same shape.
- The stock prompts in `prompts.json` are a starting point; edit to match your
  real workloads (eBay parsing, price compare, feed summary).
- Add cross-node / multi-GPU results under `scaling` once the R730s and RPC
  legs are live — measure the *actual* TP/PP overhead, don't assume it.