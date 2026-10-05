# Raul Tejada (satcom) — Dual-GPU Benchmarks
*2026-08-29 · AZW-class box · Ryzen 20-thread · 31GB RAM · Tesla P4 8GB (CUDA Pascal) + Radeon RX 6700 12GB (RDNA2 Vulkan)*

## Head-to-head: qwen3:1.7b / llama3.2:3b / qwen3.5:4b (Q4, same prompt)

| Model | Tesla P4 (CUDA) | RX 6700 (Vulkan) |
|-------|-----------------|-------------------|
| qwen3:1.7b | 71 tok/s | **75 tok/s** |
| llama3.2:3b | **49 tok/s** | 33 tok/s |
| qwen3.5:4b | **34 tok/s** | 20 tok/s |

## Findings

1. **Both cards are production-viable.** Two ollama instances (CUDA :11434, Vulkan :11435)
   give parallel inference lanes on one box.
2. **CUDA wins as models grow** — P4's dequant-to-FP32 path handles Q4 K/M cleanly.
3. **Vulkan edges the lightest model** — RDNA2 6700 at 75 tok/s on 1.7B.
4. This node IS the "gaming PC (P4 + RX 6700 XT)" from the fleet census — same silicon.
5. Control-set context: P4's 49 tok/s on llama3.2:3b vs boone CPU's 17 — ~3x.
   Randall's 4050 remains fleet speed king (67.8 on phi4-mini).

## Setup notes

- ollama installed via install.sh (auto-CUDA for the P4)
- Second instance: `OLLAMA_HOST=127.0.0.1:11435 OLLAMA_VULKAN=1 ollama serve`
- RX 6700 = Navi 22 gfx1031 — works via Vulkan without HSA overrides (discrete ≠ iGPU drop)
