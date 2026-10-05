# APU Fleet Correction + Inventory — 2026-09-28
*Nodes: mr-new-vegas, manny-vargas, corporal-betsy, craig-boone. All four are the
identical machine: AMD Ryzen 7 7735U + Radeon 680M iGPU, 19GB shared DDR5, no discrete GPU.*

## HEADLINE: the fleet table overstates this hardware class by 2.3x

`2026-08-29-fleet-control-results.md` lists **mr-new-vegas at 66 tok/s** on
`qwen3:1.7b`, hardware path "GPU-accelerated", and infers real offload from it.

**Measured today on that exact node, exact model, exact control prompt:**

| Run | tok/s |
|-----|-------|
| 1 | 28.5 |
| 2 | 28.1 |
| 3 | 27.6 |
| **median** | **28.1** |

**The 66 tok/s figure is a 2.3x overstatement.** 28.1 tok/s is also exactly where
Boone landed on identical silicon (27 tok/s) — which is what the hardware predicts.
The spread is tight (27.6–28.5), so this is not a warm-up artifact.

**Verdict: CORRECTION REQUIRED.** The "GPU-accelerated" label on this node class is
false, and the number would cause bad routing — it invites sending work here on the
belief that this box is fast.

### Why the "accelerated" belief existed
`2026-08-28-boone-amd-apu.md` already recorded that Ollama *detects* the 680M over
Vulkan then **drops it by default** ("dropping integrated GPU; to enable, set
`OLLAMA_IGPU_ENABLE`"). Detection is not acceleration. A node that enumerates a GPU
looks accelerated in a journal log while doing CPU work.

## Vulkan offload: 4th independent measurement, still zero

The 08-28 note measured this 3 ways. Re-measured today with a clean A/B, same
binary, same model, 64 generated tokens, separate server instances:

| Lane | Rate |
|------|------|
| `OLLAMA_VULKAN=0` (CPU) | 13.5 tok/s |
| `OLLAMA_VULKAN=1` (Vulkan) | 13.8 tok/s |

**+2% = noise.** The 13.8 tok/s figure that got reported as "the unlock" was the
CPU number all along.

Confirmed the enumeration is real and the offload still does nothing:
```
inference compute" id=0 library=Vulkan compute=0.0 name=Vulkan0
  description="AMD Radeon Graphics (RADV REMBRANDT)" pci_id=0000:04:00.0
```

**No change to doctrine: don't tune it. Go MoE or go discrete GPU.**

## Render-node check: the Raúl-class fault is ABSENT here

`2026-08-29-raul-6700-lfm25.md` documented a silent-fallback trap: RADV can't open
`/dev/dri/renderD128`, the GPU vanishes, and `/api/ps` reports *bogus* VRAM (it
counted llvmpipe). Checked on all four APU nodes:

| Node | renderD128 perms | Can open? | RADV sees |
|------|------------------|-----------|-----------|
| mr-new-vegas | `crw-rw-rw-` | yes | RADV REMBRANDT |
| manny-vargas | `crw-rw-rw-` | yes | RADV REMBRANDT |
| corporal-betsy | `crw-rw-rw-` | yes | RADV REMBRANDT |
| craig-boone | `crw-rw-rw-` | yes | RADV REMBRANDT |

World-readable here (Raúl's was `crw-rw----` with the user outside `render`/`video`),
so that fault does not apply to this class. **Moot regardless — offload gains nothing.**

## Model inventory: two of four nodes have NO usable text reasoner

| Node | Text models | Vision models |
|------|-------------|---------------|
| craig-boone | **lfm2.5:8b, phi4-mini, qwen3:1.7b, llama3.2:3b, qwen3.5:4b, qwen3:4b, qwen3:8b, qwen2.5-coder:1.5b** | llava:7b, llama3.2-vision:11b, moondream |
| manny-vargas | qwen2.5-coder:0.5b, gemma3:4b | llama3.2-vision:11b, minicpm-v:8b, qwen3-vl:8b |
| corporal-betsy | qwen2.5-coder:0.5b, phi3:mini, gemma:2b | llama3.2-vision:11b, qwen3-vl:8b, llava:7b, moondream |
| mr-new-vegas | qwen3:1.7b, qwen3:4b, qwen3:8b, llama3.2-vision:11b, moondream | (same) |

**Every vision model tested is non-functional.** `llama3.2-vision:11b` on all three
remote nodes:
```
"error":"llama-server process has terminated: exit status 1: error loading mode"
```
That is ~26GB of models across manny + betsy that cannot load. `mllama` architecture
is not supported by the installed runtime. This is dead weight masquerading as
inventory — and it explains "we've only found one decent reasoner so far": on two of
the four nodes there is nothing else to find.

**Action: REMOVAL REPORT owed** for the vision models on CPU-only APU nodes. Per
doctrine step 4, a failure produces a removal report with evidence. This is it.

## Service defects found and fixed

**manny-vargas had no ollama service at all.** It was running from
`/tmp/start-ollama.sh` — a hand-typed script in `/tmp` that dies on reboot, with a
broken `OLLAMA_PID=` (missing `$!`). Now a persistent `ollama.service`
(`User=mvargas`, `OLLAMA_MODELS=/home/mvargas/.ollama/models`, enabled). Verified
post-change: 4 pre-existing models still visible, so the store path is correct.

**craig-boone's `ollama-fleet.service` is a hardened system unit running as
`User=boone`** with deliberate tuning: `KEEP_ALIVE=-1`, `NUM_PARALLEL=1`,
`MAX_LOADED_MODELS=1`, `KV_CACHE_TYPE=q8_0`, `HOST=127.0.0.1` (localhost-only).
**Left untouched.** This is the reference hardening for the class.

**corporal-betsy's `ollama.service` runs as ROOT with `OLLAMA_HOST=0.0.0.0`.**
Inconsistent with Boone's localhost-only posture — Betsy's inference API is exposed
on every interface. Flagging, not fixed: changing it could break whatever consumes
it. **Recommend aligning to Boone's pattern.**

## Network notes

- All four APU nodes: **IPv4 fine, IPv6 dead.** `registry.ollama.ai` returns an AAAA
  record but v6 connectivity fails, so v4 must be preferred.
- **Intermittent DNS blackhole:** two pulls died with
  `dial tcp 10.0.0.1:443: i/o timeout` against `registry.ollama.ai` on manny and
  betsy, then succeeded on retry. A blackhole address, not NXDOMAIN. Transient —
  but it will look like "the model doesn't exist" if you don't read the error.
- A dense 8B pull (`granite3.3:8b`, 4.9GB) failed twice on betsy. **Not retried** —
  the 08-28 note already measures dense 8B on this hardware at "~4 tok/s (crawl)".
  Spending bandwidth on a model doctrine has already culled is the error, not the
  network.

## Model assignment (corrected)

The first pass assigned dense models (`gemma3:4b`, `granite3.3:8b`) to the small PCs.
**That was wrong** — it contradicts the bandwidth-wall finding in the 08-28 note.
Corrected to MoE-first per the APU tier:

| Node | Model | Family | Why |
|------|-------|--------|-----|
| craig-boone | `lfm2.5:8b` | MoE, 1B active/token | fleet default, 30 tok/s proven here |
| manny-vargas | `lfm2.5:8b` | MoE | no usable reasoner present; needs the default |
| corporal-betsy | `lfm2.5:8b` | MoE | same |
| mr-new-vegas | `lfm2.5:8b` + control set | MoE | fill in the matrix's "pending" row |

Diversity for the war room must come from **model family, not from three copies of
one file**. Three identical boxes on `lfm2.5:8b` is a homogeneous room. The control
set (`qwen3:1.7b`, `llama3.2:3b`, `qwen3.5:4b`, `phi4-mini`) gives genuine family
spread on identical hardware — which is a cleaner axis of diversity than different
silicon would be.

## Honest caveats

1. `lfm2.5:8b` pulls on manny/betsy/boone had not completed when this was written.
   The 30 tok/s figure is Boone's prior measurement, not a fresh one.
2. No `fleet_score` yet — `lab.py` was only deployed during this session. The
   reasoning/toolcall/guardrail positions are unmeasured on this class.
3. Single-node measurement (mr-new-vegas) is the basis for the 2.3x correction.
   Boone's independent 27 tok/s is corroboration, not replication of the same test.
