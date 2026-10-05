# Model Lab — Plan & Findings

Project home for the GX-9000 model benchmarking framework.
Tool: `tools/model-lab/` · Results: `projects/model-lab/results/`.

## Goal
Stop guessing which model/node wins. Measure it, record it, route by evidence.
"Find out what really works for us" — not for a benchmark site.

## Framework positions
See `tools/model-lab/README.md`. Core idea: score each model/node on
**speed + capacity + toolcall + reasoning + guardrail**, blended into a
single fleet-fit score. Speed alone is a trap — a fast model that can't emit
valid JSON is useless for agent work.

## How to run a matrix
1. Edit `tools/model-lab/targets.json` to match live nodes/models.
2. Run `python3 tools/model-lab/lab.py run --node <n> --model <m>` per cell.
3. Keep JSON in `results/`. Optionally compare with `lab.py report`.

## Open items / next test passes
- [ ] Baseline the P100 (this box): qwen3.6:35b-a3b vs qwen3:14b vs qwen3:8b.
- [ ] Confirm `ollama pull qwen3:14b` completed (interrupted last session).
- [ ] Test multi-GPU tensor-split on the 2×P100 R730 once populated.
- [ ] Add a cross-node llama.cpp RPC test (70B) — measure real overhead.
- [ ] Build a 2-turn tool-call case (multi-turn JSON) to catch
      models that pass 1-turn but fail multi-turn (Berkeley BFCL finding).

## Effectiveness scoring (transparent, tunable)
- Each position returns raw metrics + a 0–1 effectiveness.
- `fleet_score = Σ(weight × eff) / Σ(weight)` over positions run.
- Weights live in `lab.py` (`WEIGHTS`). Adjust when reality disagrees.

## When enough data exists
Use the results to auto-route in `chippy-router.py` / the hub-spoke relay:
smallest competent model per task, reserve big models for batch.