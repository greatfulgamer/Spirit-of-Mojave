# Fleet Model Benchmarks — Boone Node
*Measured 2026-08-28 · hardware: AZW SER mini-PC · Ryzen 7 7735U (8C/16T) · Radeon 680M iGPU (no discrete GPU) · 24GB shared DDR5*

## The headline finding

**MoE models double throughput on AMD APUs.** Memory bandwidth is the wall for dense
models on integrated graphics — Mixture-of-Experts models that activate only a fraction
of their parameters per token sidestep it entirely.

| Model | Size | Measured | Notes |
|-------|------|----------|-------|
| **lfm2.5:8b** | 5.2 GB | **30-31 tok/s** | 8B-class MoE, only 1B active/token, native thinking. **Fleet default.** |
| phi4-mini | 2.5 GB | 14-15 tok/s | dense 3.8B — responsive, best-in-class reasoning per GB |
| qwen3.5:4b | 3.4 GB | ~pull only | thinking + 256K ctx + multimodal — not yet benchmarked |
| qwen3:8b | 5.2 GB | ~4 tok/s ("crawl") | dense 8B — unusable interactively on this hardware |

## GPU offload findings (measured, not estimated)

| Path | phi4-mini rate |
|------|---------------|
| CPU only | 14-15 tok/s |
| OLLAMA_VULKAN=1 | 14 tok/s — no gain |
| OLLAMA_VULKAN=1 + OLLAMA_IGPU_ENABLE=1 | 15 tok/s — no gain |

Ollama 0.32.14 detects the 680M via Vulkan then **drops it by default** ("dropping
integrated GPU; to enable, set OLLAMA_IGPU_ENABLE"). Enabling it changed nothing —
the 680M's shared-RAM bandwidth cannot beat the CPU path for dense models this size.
The "Vulkan doubles your speed" projections circulating online do not survive
contact with this hardware. MoE does.

## Reference hardware comparison

| Machine | GPU | phi4-mini rate |
|---------|-----|---------------|
| randall-clark (AZW SER + RTX 4050 mobile) | 6GB GDDR6 + CUDA | **67.8 tok/s** |
| craig-boone (AZW SER, iGPU only) | Radeon 680M shared | 14-15 tok/s |

 Randall is the fleet's fast-inference node; iGPU-only nodes should run MoE models.

## Fleet model ranking (rise-and-shine Local AI phase)

```
1. lfm2.5:8b      — 30 tok/s, thinking, 8B quality (MoE)
2. qwen3.5:4b     — thinking, 256K ctx, multimodal
3. phi4-mini      — 14 tok/s dense fallback
4. qwen3:4b / qwen3:8b — legacy
```

## Config touchpoints

- `~/.config/opencode/opencode.json` → provider.ollama.models (picker entries)
- `tools/rise-and-shine.sh` → 11b Local AI readiness phase (ranked preload)
- Service: systemd user unit, OLLAMA_HOST=0.0.0.0:11434 (tailnet-reachable)

## Gotchas discovered

- **Git sync race**: fleet-wide git-auto-sync cycles overwrite uncommitted working-tree
  changes — commit to machine branch IMMEDIATELY after editing shared repo files.
- **Tailscale ACL blocks port 8899** between nodes — use Taildrop (`tailscale file cp/get`,
  needs operator/sudo) or blaster chunk-push for fleet file moves.
- **ollama library tag lookups**: query `https://ollama.com/library/<model>/tags` —
  bare tags like `lfm2.5:8b-a1b` 404 while `lfm2.5:8b-a1b-q4_K_M` exists.

## Control set completion (2026-08-29, same hardware/prompt)

| Model | Size | Rate | Notes |
|-------|------|------|-------|
| qwen3:1.7b | 1.1 GB | **27 tok/s** | fastest control model; thinking-capable |
| llama3.2:3b | 2.0 GB | **17 tok/s** | fastest dense; quality holds |
| qwen3.5:4b | 3.4 GB | **11 tok/s** | slower than phi4-mini (256K ctx overhead); thinking + multimodal |

**Complete boone ranking (this prompt, Q4, CPU):** lfm2.5:8b 31 > qwen3:1.7b 27 > llama3.2:3b 17 > phi4-mini 14-15 > qwen3.5:4b 11 > qwen3:8b ~4
