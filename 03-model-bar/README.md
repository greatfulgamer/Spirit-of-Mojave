# Model Bar

Local LLM lineup, benchmarks, and configs for the RobCo GX-9000 fleet.

## What lives here

- `benchmarks/` — measured tok/s and quality notes per node/hardware
- `tests/` — raw test-session captures (prompt + response + rate)
- `configs/` — opencode provider snippets, rise-and-shine ranking blocks

## Doctrine

1. Measure on the target hardware — projections lie (see Vulkan findings)
2. On AMD APU nodes, MoE models beat dense models ~2x (bandwidth wall)
3. Every opencode launch warm-preloads the smartest resident model (rise-and-shine 11b)
4. Commit benchmark data immediately — the fleet sync race eats uncommitted trees

## Quick reference

```bash
ollama list                        # what's resident
ollama run lfm2.5:8b               # fleet default (30 tok/s on APU, thinking)
ollama run phi4-mini               # dense fallback (14 tok/s on APU)
curl localhost:11434/api/generate -d '{"model":"lfm2.5:8b","prompt":"...","stream":false}'
```
