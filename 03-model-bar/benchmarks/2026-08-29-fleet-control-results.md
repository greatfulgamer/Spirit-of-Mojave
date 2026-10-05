# Fleet Control-Set Results — 2026-08-29
*Same prompt on every node: "Count from 1 to 5, then explain Rayleigh scattering in one sentence." Q4 quant, ollama.*

## The fleet table

| Node | Hardware path | qwen3:1.7b | llama3.2:3b | qwen3.5:4b | phi4-mini | lfm2.5:8b |
|------|--------------|-----------|-------------|------------|-----------|-----------|
| randall-clark | RTX 4050 (CUDA) | **130** | **84** | **55** | 67.8 ✅user | — |
| mr-new-vegas | **CORRECTED 2026-09-28** — was "GPU-accelerated 66/40". Not GPU accelerated. Re-measured: **28.1** ✅ / (llama3.2:3b not re-measured) | **11.3** ✅ | — | — | see `2026-09-28-apu-fleet-correction-and-inventory.md` |
| raul-tejada P4 | Tesla P4 (CUDA) | 71 | **49** | **34** | — | — |
| raul-tejada RX6700 | RX 6700 (Vulkan) | **75** | 33 | 20 | — | — |
| craig-boone | Ryzen 7735U CPU | 27 | 17 | 11 | 14-15 | **30-31** |
| radar-o-reilly | Pixel 10 ARM | **13** | — | — | — | — |

## Findings

1. **Randall's 4050 is the fleet speed king** — 130 tok/s on the floor model. All agent
   fast-path traffic should default there.
2. ~~**Vegas runs GPU-accelerated inference** (66 tok/s on 1.7B confirms offload)~~
   **RETRACTED 2026-09-28.** The 66 tok/s figure was a 2.3x overstatement; re-measured
   at 28.1 tok/s median (27.6/28.1/28.5), which is where identical hardware (Boone,
   27 tok/s) lands. The "confirms offload" inference was wrong — Ollama *detects* the
   680M over Vulkan then drops it by default, so enumeration in a log is not
   acceleration. iGPU offload on this class gives zero gain (CPU 13.5 vs Vulkan 13.8
   tok/s, re-measured). Do not route work here expecting speed.
3. **Raul = dual inference lanes**: P4-CUDA :11434 + RX6700-Vulkan :11435 concurrently.
   CUDA scales better with model size; Vulkan's RDNA2 wins at the lightest tier.
4. **MoE rule holds**: lfm2.5:8b (30 tok/s CPU) beats every dense model on CPU-only nodes.
5. **Phone tier**: 13-15 tok/s on ARM — viable for light agent duty, handle gently.

## Node access cheatsheet (blaster first, always)

| Node | blaster | user |
|------|---------|------|
| randall-clark | randall-clark:8190 | bazzite (sudo=bazzite) |
| raul-tejada | 100.127.121.103:8190 — **use IP, DNS flakes** | bazzite (sudo=bazzite) |
| mr-new-vegas | mr-new-vegas:8190 | mr.newvegas (sudo: see .secrets.local) |
| radar-o-reilly | 100.75.52.121:8190 | droid |
| craig-boone | localhost:8190 | boone (sudo: see .secrets.local) |
| general-lee-oliver | oliver:8190 (flaky — skip when unresponsive) | biron |

## Pending

- general-lee-oliver: control set (blaster flaky all day)
- mr-new-vegas qwen3.5:4b: pull in progress
- Heavy nodes (R730 4×GPU, gaming rig 14B, laptops, Xboxes): hardware surveyed, benches queued
