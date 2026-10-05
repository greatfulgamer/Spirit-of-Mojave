# GX-9000 Fleet — Master Model Test Matrix
*Source: fleet hardware census 2026-08-28 + proven measurements from boone (craig-boone) + Randall cross-check. Update this file as real numbers land.*

## Proven headline findings (measured, not estimated)

1. **MoE beats dense ~2x on bandwidth-limited nodes** — lfm2.5:8b = 30-31 tok/s vs phi4-mini 14-15 tok/s on the same CPU (Ryzen 7735U). Look for `-AxB` tags (A active of B total).
2. **GPU offload via Vulkan on AMD iGPU = zero gain** (measured 3 ways). Don't tune it; go MoE or go discrete GPU.
3. **Dedicated VRAM rules** — Randall's RTX 4050 does 67.8 tok/s on phi4-mini vs boone's 14. Route heavy/urgent inference to CUDA nodes.

## Control set (run on EVERY node)

| Model | Size | Why |
|-------|------|-----|
| qwen3:1.7b | ~1.1 GB | thinking-capable floor model |
| llama3.2:3b | ~2 GB | community baseline everyone calibrates against |
| qwen3.5:4b | ~2.5 GB | modern reference: thinking + 256K ctx + multimodal |

## Standard test protocol (same 3 tests everywhere)

- **Test A — Speed**: `"Count from 1 to 5, then explain Rayleigh scattering in one sentence."` → record eval tok/s
- **Test B — Tool calling**: `"You have a tool called 'weather' that takes a city name. What is the weather in Tokyo? Call the tool."` → structured tool call? (1-5)
- **Test C — Multi-step reasoning**: the Paris/Lyon trains problem (460km, 120 vs 100 km/h, offset start) → correct answer? shows work? (1-5)

## Node roster + primary model picks

| Node | Hardware | Path | Primary pick | Status |
|------|----------|------|--------------|--------|
| craig-boone | Ryzen 7735U, 680M, 24GB | CPU/MoE | **lfm2.5:8b** (30 tok/s ✅) | benched |
| randall-clark | AZW SER + RTX 4050 6GB | CUDA | **control set ✅** 130/84/55 + phi4-mini 67.8 — fleet speed king |
| raul-tejada (satcom) | P4 8GB + RX 6700 12GB | CUDA + Vulkan | **control set ✅** 71/49/34 (P4) + 75/33/20 (6700) dual-lane |
| radar-o-reilly | **Pixel 10, Tensor G5, 7.4GB RAM** | ARM CPU | qwen3:1.7b (13 tok/s ✅), qwen2.5-coder:1.5b (15 tok/s ✅) | benched |
| general-lee-oliver | (onboarded node) | TBD | control set | pending |
| mr-new-vegas | Ryzen 7 7735U + 680M iGPU, 19.3 GiB, **no GPU gain** | CPU/MoE | qwen3:1.7b **28.1** ✅ qwen3.5:4b **11.3** ✅ (2026-09-28) | benched |
| R730 server | 2×P100 + 2×P40, 48GB VRAM | CUDA Pascal | qwen3:14b, deepseek-r1:14b, qwen3-coder:30b-a3b (MoE ~50 tok/s on P40) | planned |
| (Gaming PC = raul-tejada — merged into row above, dual-backend proven) |
| Laptop A | RTX 4060 16GB | CUDA Ada | qwen3:14b, qwen3.5:9b | planned |
| Laptop B | GTX 1060 5GB | CUDA Pascal | phi4-mini, qwen3:1.7b | planned |
| QNAP NAS | containerd orchestrator, 32GB | CPU | lfm2.5:8b (tool-calling MoE), qwen3.5:9b | planned |
| N100 portable | 4-core, iGPU unused | CPU | qwen3:1.7b, qwen3:0.6b (router/classifier) | planned |
| Xbox Series X | 12× Zen 2, 16GB unified | ARM CPU | lfm2.5:8b, phi4-mini | planned |
| Xbox One S ×2 | 10GB unified | x86 CPU | qwen3:0.6b (router tier) | planned |

## Phone node rules (radar-o-reilly — handle with care)

1. **One model at a time** — 7.4GB RAM total, 6.3GB free
2. **Short runs + thermal pauses** — Tensor G5 throttles; sleep 30s between tests
3. **VM suspension**: Android suspends the Debian VM when backgrounded — keep Terminal app
   foreground during benchmarks; disable battery optimization for it
4. **Access doctrine**: blaster on 100.75.52.121:8190 (ALWAYS FIRST), adb tunnel
   (`ssh -o ProxyCommand="adb shell nc 10.162.43.186 22" droid@phone-vm`) as fallback
5. Models pulled: qwen2.5-coder:1.5b (15 tok/s ✅), qwen3:1.7b (pulled, test pending)

## Pull commands by tier

```bash
# control set (all nodes)
ollama pull qwen3:1.7b && ollama pull llama3.2:3b && ollama pull qwen3.5:4b
# AMD APU nodes (bandwidth-limited)
ollama pull lfm2.5:8b && ollama pull phi4-mini
# CUDA 8GB+ nodes
ollama pull qwen3:14b && ollama pull deepseek-r1:14b
# CUDA 16GB+ nodes (add)
ollama pull qwen3.5:9b && ollama pull llama3.1:8b
# ultra-light router tier
ollama pull qwen3:0.6b
```
