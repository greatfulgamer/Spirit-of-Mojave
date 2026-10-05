# Third-Party Recommendation Audit, Round 2 — 2026-09-28
*A second set of hardware recommendations, largely for models we had never pulled.
Audited the same way as `2026-09-28-third-party-recommendation-audit.md`.*

## The headline recommendation does not exist

`ZAYA1-8B` was presented as "the one to try first," with a table of AIME'25 88.3
and HMMT'25 82.7 scores, a claim of top-1 routed MoE at 760M active params, and a
"pull this first" instruction.

```
https://ollama.com/library/zaya1/tags  ->  HTTP 404
```

**There is no such library in the Ollama registry.** Not too large, not RAM-constrained,
not a tag-name mistake — the model is not published there. Every benchmark number
attached to it is unverifiable, and it was ranked #1.

The *architecture argument* underneath it is sound, though: a sub-1B-active MoE is
exactly the right shape for a bandwidth-wall CPU, because per-token cost tracks
**active** parameters, not total size. That idea is worth chasing if a real model of
that description appears. The specific model is not one.

## A second tag that does not exist

`gemma4:26b-a4b` was recommended with a pull command. The registry returns
`MANIFEST_UNKNOWN`. The real tags carry an infix the recommendation dropped:

| Recommended | Actually published |
|-------------|-------------------|
| `gemma4:26b-a4b` | `26b-a4b-it-q4`, `-it-q8`, `-it-qat`, `-it-bf16`, `-it-mtp-q4` |
| `gemma4:e4b` | **exists** (9.6 GB) |

So the mobile variant is pullable; the "CPU sleeper" flagship is not, under the name given.

## The `gpt-oss:20b` belief

`gpt-oss:20b` was discussed at length, including a Modelfile for raising reasoning
effort, and referred to as if already in hand ("we did use gpt-oss:20b I thought").

**It is on zero of the four nodes.**

| Node | gpt-oss present? |
|------|------------------|
| mr-new-vegas | no |
| manny-vargas | no |
| corporal-betsy | no |
| craig-boone | no |

It appears in five fleet **documents** (`docs/API-MODEL-PICKS.md`,
`docs/CENTRAL-MODEL-REPO.md`, `docs/FLEET-HARDWARE-CHART.md`,
`docs/FLEET-STRATEGY-2026-08-31.md`, and the round-1 audit file). A recommendation
read as a measurement. That is the exact failure this repo exists to prevent, and it
is now the second time a "we have X" belief has traced back to a doc rather than a node.

The model is real: `gpt-oss:20b`, **13.8 GB** from the registry. On a 19.3 GiB node
that leaves roughly 5 GiB for OS, desktop and KV cache. Marginal, and the
recommendation's own "fits in 24 GB" reasoning does not apply to this hardware.

## A claim that is testable, and is false

> "Qwen3.5 0.8B, 2B, 4B, and 9B have reasoning disabled by default. If you're just
> doing `ollama run qwen3.5:4b`, you may not be getting any thinking at all."

Tested on both models with a problem that forces deliberation. **Both emit a
`thinking` field.** Reasoning is on by default here.

What *is* real, from the same test, is a different problem the recommendation
misattributed:

| Model | `num_predict` | Result |
|-------|---------------|--------|
| qwen3.5:4b | 512 | empty answer, all budget consumed by thinking |
| qwen3.5:4b | 2048 | **0.05** — correct |
| qwen3:1.7b | 2048 | never terminated, still mid-sentence |

This is the `num_predict` trap already recorded in
`2026-08-31-raul-p4-carousel-war-room.md` ("thinking-mode models eat all tokens before
response"). It is a real, known fleet gotcha. The "reasoning is off" story was a
red herring pointing at a genuine issue that had already been documented.

## The memory-bandwidth explanation is unfalsifiable from inside the box

The recommendation argues at length that this node has LPDDR5-6300 (~50 GB/s) rather
than DDR5-4800 (~77 GB/s), and that this explains the 11 tok/s measurement.

It cannot be checked here. `dmidecode` needs root, which this node does not have, and
`/sys/devices/virtual/dmi/id/memory_type` is not populated. So the SPD data is
invisible without privileges.

Worth noting anyway: **our measured whole-chip bandwidth is 32.8 GB/s**, which is
*below* both the 50 and the 77 GB/s figures in play. Neither memory story explains
the measurement. The 11.3 tok/s figure stands on its own as a direct observation and
does not require the memory story to be true.

## What did get pulled

Three recommendations were real and pullable, so they were pulled — one per node,
which also serves the one-distinct-reasoner-per-machine goal:

| Node | Model | Size | Avail RAM at pull time |
|------|-------|------|------------------------|
| manny-vargas | `gemma4:e4b` | 9.6 GB | 14 GB |
| corporal-betsy | `lfm2.5:8b` | 5.2 GB | 14 GB |
| craig-boone | `gpt-oss:20b` | 13.8 GB | 11 GB (tight) |

Registry sizes were read from the manifest API before committing RAM, not estimated
from the recommendation's tables.

## The finding that matters most, and it inverts the speed ranking

From the trap-question work, on identical hardware:

| Model | Speed | Trap question (bat and ball) |
|-------|-------|------------------------------|
| qwen3:1.7b | ~27 tok/s | **never terminated** |
| qwen3.5:4b | ~11 tok/s | **correct: 0.05**, 699 tokens |

`qwen3:1.7b` also **confabulated a colour** when asked about a fleet doctrine that
does not exist, and correctly pushed back on a false premise about CUDA cores.

So the fastest model is the weaker reasoner, and it will invent facts under
sufficient pressure. **tok/s ranking and reasoning ranking disagree on this
hardware.** Any per-machine model choice driven by the speed table will pick wrong.

## Honest caveats

1. The three new models are **pulled but not yet benchmarked**. No speed or
   reasoning number exists for any of them.
2. `gpt-oss:20b` at 13.8 GB on an 11 GB-available node may not load. If it fails,
   that is a RAM result, not a rejection on quality.
3. The `reasoning-hard` suite is slow (thinking models at ~10 tok/s against 12k
   token budgets). Its caps were raised after `qwen3.5:4b` returned empty answers
   under a 512-token cap, and the raised cap has not been re-validated end to end.
   Results from the 4-case suite are **partial**.
4. Whether the node is LPDDR5 or DDR5 remains **unverified**. Recorded as unknown,
   not as either answer.
