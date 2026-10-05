# Third-Party Recommendation Audit — 2026-09-28
*A generic "detailed breakdown for your hardware" LLM answer was audited against this
node class. Kept because it is a clean example of why the Model Bar exists: the
recommendation was confidently specific, internally consistent, and wrong in ways that
would have cost real bandwidth and broken a node.*

## VERDICT: do not trust hardware recommendations that were not measured here

The answer opened by correctly identifying the binding constraint (memory bandwidth,
MoE > dense on integrated graphics). It then made **five factual errors about the
hardware** and **two large performance overstatements**, while presenting all of it
with the same confidence as the correct parts.

## Hardware facts — verified on the node, not read from a spec sheet

| Property | Recommendation said | **Measured / authoritative** | Verdict |
|----------|--------------------|-------------------------------|---------|
| iGPU | Radeon 780M, 12 CU | **Radeon 680M**, PCI `1002:1681` (rev 08), RDNA2 | WRONG model |
| CU count | 780M=12, 680M=8 → "you have 8" | 680M is RDNA2; the 780M is the 12-CU part. Device ID confirms **680M** | correction to the *correction* — see below |
| CPU arch | "mobile Zen 4" | **Zen 3** — `lscpu`: family 25 (0x19), model 68 (0x44) | WRONG |
| RAM | "24 GB DDR5-4800" | **19.3 GiB (20.7 GB) total** | WRONG |
| VRAM | not stated | `mem_info_vram_total` = **4 GiB** amdgpu carveout | new |

### A note on the CU count, because the corrections contradicted each other
The audit answer was corrected twice: first to "680M = 8 CU, not 12," then to
"680M actually has 12 CUs, same as 780M." **Both corrections are wrong about the CU
count, and the original device identification is the one that holds.** The PCI device
ID `1002:1681` is unambiguously "Radeon 680M," which is an **8 CU / 512 shader** RDNA2
part. The 12-CU / 768-shader part is the 780M (RDNA3). RDNA2 vs RDNA3 is the real
architectural difference between them, not the CU count.

**Neither interface available on this node reports CU count directly** (lspci gives
device ID only; amdgpu exposes VRAM and busy% but not CUs). The PCI ID is the
authoritative identifier and it settles the question. Recording this because a
three-way contradiction in a hardware claim is exactly what a results file exists to
prevent recurring.

## The headline recommendation is physically impossible here

`qwen3:30b-a3b` (~18.6 GB Q4) was the primary pick at "★★★★★ reasoning."

```
model needs   : 18.6 GB
RAM available :  7.6 GB   (11.9 GB at time of first check)
RAM total     : 20.7 GB (19.3 GiB)
VERDICT       : CANNOT FIT — short by 6.7 GB even against TOTAL RAM
```

It would have had to page or OOM. The recommendation assumed 24 GB and a light
desktop; this node has 19.3 GiB and a running desktop session. **Following the
"primary recommendation" would have produced an OOM, not a reasoning model.**

The audit's *revised* answer agreed qwen3:30b-a3b is out. That part is right.

## The performance overstatement, settled by measurement

The audit claimed `qwen3.5:4b` runs at **25–40 tok/s**. Measured on this node, same
control prompt the fleet table uses, 3 runs:

| Run | tok/s |
|-----|-------|
| 1 | 11.2 |
| 2 | 11.4 |
| 3 | 11.3 |
| **median** | **11.3** |

**Overstated by ~2.6x.** The audit later self-corrected to 11 tok/s, which matches
our measurement exactly — and matches the 08-28 Boone note (11 tok/s). Two
independent nodes, same number. That figure is now confirmed, not assumed.

This also **fills the "pending" cell** in `fleet-test-matrix.md` for mr-new-vegas.

## Memory bandwidth — measured, including a correction to my own test

The audit's revised explanation attributed 11 tok/s to ~50–60 GB/s effective
bandwidth with a 40–60% overhead factor. Measured on this node with a STREAM-triad:

| Test | Result |
|------|--------|
| 8-thread, whole-chip | **32.8 GB/s** |
| single-thread | **~20–22 GB/s** |

**Correction to my own work:** the first bandwidth test I ran was single-threaded and
came out at ~20 GB/s. I was about to call that a refutation of the 50–60 GB/s claim.
It is not — a single-core figure and a whole-chip figure are different quantities.
The fair comparison is 32.8 GB/s whole-chip, which is **1.7x below** the claimed
effective figure. The likely cause is that this board is not running DDR5-4800
dual-channel at full rated throughput; that is unverified.

**What survives:** LLM decode is largely single-threaded per layer, so the ~20–22
GB/s single-core path is the relevant ceiling. At ~2.5 GB read per token that gives a
~9 tok/s ceiling, and we measured 11.3 — i.e. *above* the naive estimate, because not
every weight is re-read from DRAM each token. The 11 tok/s figure is internally
consistent with the measured hardware. The audit's revision to 11 is correct.

## Revised pick in the audit vs the pick this fleet has already proven

The audit's revised primary is `gpt-oss:20b` (~13 GB, MoE, 3.6B active, projected
10–14 tok/s).

**It has not been tested here, and there is a RAM problem the audit missed again:**

```
gpt-oss:20b needs ~13 GB
this node has  19.3 GiB total, 7.6 GB available right now
```

13 GB on 19.3 GiB leaves ~6 GiB for OS, desktop, and KV cache. It is marginal, and
**the audit marked it "✅ Fits" using the same wrong 24 GB assumption it had already
been corrected on once.** This is a live risk of the same error recurring.

Against the model this fleet has actually measured on this exact silicon:

| Model | Size | Measured | Note |
|-------|------|----------|------|
| **lfm2.5:8b** | 5.2 GB | **30 tok/s** (Boone, 08-28) | MoE, 1B active/token |
| qwen3:1.7b | 1.1 GB | 28.1 tok/s (this node, today) | |
| llama3.2:3b | 2.0 GB | 17 tok/s (Boone) | |
| qwen3.5:4b | 3.4 GB | 11.3 tok/s (this node, today) | |
| phi4-mini | 2.5 GB | 14–15 tok/s (Boone) | |
| gpt-oss:20b | ~13 GB | **untested** | RAM-marginal on 19.3 GiB |
| qwen3:30b-a3b | ~18.6 GB | **cannot fit** | −6.7 GB |

**lfm2.5:8b remains the primary pick on this hardware class** — 5.2 GB, 30 tok/s
measured, comfortable RAM headroom, MoE. `gpt-oss:20b` is a legitimate *candidate to
test* for reasoning quality, but it is not obviously better than a proven 30 tok/s
model, and it is 2.5x the RAM. Test it before promoting it; do not promote it on a
projection.

## Standing rule this audit reinforces

1. **Never accept a hardware spec or a tok/s figure that was not measured on the node.**
   Five of seven hardware claims here were wrong. All were stated confidently.
2. **A recommendation that survives its own correction is still not verified.** The
   audit self-corrected twice and was wrong again on the CU count and on the RAM fit.
3. **Projected speeds are not benchmarks.** `benchmarks/` exists so that a number has a
   node, a model, a prompt, and a date attached to it, or it is not a number.

## Honest caveats

1. `gpt-oss:20b` remains **untested**. The fit assessment is arithmetic on measured
   RAM, not a load attempt. It may work if the desktop is closed; it was not tried.
2. The 1.7x whole-chip bandwidth gap is **unexplained**. "Board is not running rated
   DDR5" is a hypothesis, not a finding. `dmidecode` was unavailable (no sudo on this
   node) so actual DIMM speed and configuration are unconfirmed.
3. The CU count was settled by PCI device ID, not by reading a CU register. That is
   authoritative for identifying the part but is not a direct CU readout.
4. `lfm2.5:8b` pulls on manny/betsy had not completed when this was written. The
   30 tok/s figure is Boone's prior measurement, not a fresh one on those two nodes.
