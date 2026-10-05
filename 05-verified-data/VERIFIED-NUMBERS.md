# Verified measurements — 2026-09-28/29
Every number here was measured on the node named. Node, model, prompt, date — or it
is not a number.

## Hardware, all four nodes identical
AMD Ryzen 7 7735U (Zen 3, family 25 model 68) · Radeon 680M iGPU (PCI 1002:1681, RDNA2, 8 CU)
· 19.3 GiB (20.7 GB) shared DDR5 · no discrete GPU

## Memory bandwidth (measured, this node)
| Test | Result |
|------|--------|
| single-thread STREAM-triad | ~20-22 GB/s |
| 8-thread whole-chip | 32.8 GB/s |

LLM decode is largely single-threaded per layer, so the ~20-22 GB/s figure is the
relevant ceiling. LPDDR5-vs-DDR5 could not be determined (no root for dmidecode;
DMI type not populated) — recorded as UNKNOWN, not guessed.

## iGPU offload: no gain. Measured 4 independent ways.
| Path | Rate |
|------|------|
| CPU only | 13.5 tok/s |
| OLLAMA_VULKAN=1 | 13.8 tok/s |

+2% = noise. Ollama DETECTS the 680M then drops it by default
("dropping integrated GPU"). Enumeration in a log is not acceleration.
Render node is `crw-rw-rw-` and world-readable on all four (unlike raul-tejada's
box, which had the `crw-rw----` permission fault).

## Control set, standard prompt, same hardware
| Model | Rate | Node | Date |
|-------|------|------|------|
| qwen3:1.7b | 28.1 tok/s (median of 27.6/28.1/28.5) | mr-new-vegas | 09-28 |
| qwen3.5:4b | 11.3 tok/s (median of 11.2/11.4/11.3) | mr-new-vegas | 09-28 |
| lfm2.5:8b | 30-31 tok/s | craig-boone | 08-28 |
| llama3.2:3b | 17 tok/s | craig-boone | 08-28 |
| phi4-mini | 14-15 tok/s | craig-boone | 08-28 |
| qwen3:8b | ~4 tok/s ("crawl", dense) | craig-boone | 08-28 |
| gpt-oss:20b | 9.8 tok/s, correct answer | craig-boone | 09-28 |

**CORRECTION to the fleet table:** it listed mr-new-vegas at 66 tok/s
"GPU-accelerated". Measured 28.1. A 2.3x overstatement. Retracted in place.

## Fit facts
- qwen3:30b-a3b (18.6 GB) CANNOT LOAD. 6.7 GB short even against total RAM.
- gpt-oss:20b (13.8 GB) LOADS AND RUNS in 11 GB free. No swap. Memory is
  less binding than assumed — for MoE the cost tracks ACTIVE params.

## Reasoning (the finding that inverts the ranking)
| Model | Speed | Trap question (bat and ball) |
|-------|-------|------------------------------|
| qwen3:1.7b | ~27 tok/s | never terminated; confabulated a colour for a nonexistent doctrine |
| qwen3.5:4b | ~11 tok/s | CORRECT (0.05), 699 tokens |

**The fast model is the worse reasoner.** tok/s ranking and reasoning ranking
disagree on this hardware. Verified by the sycophancy probe (1.7b correctly pushed
back on a false CUDA-core premise) as well as the trap.
