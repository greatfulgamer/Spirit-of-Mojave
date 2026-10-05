# SPIRIT OF MOJAVE — War Room Design, From a Box That Is Going Down
*Written 2026-09-29 on the 3rd-generation mr-new-vegas, shortly before it was expected
to be reimaged. Everything here is on disk, not in anyone's head.*

## 0. THE SITUATION THIS WAS WRITTEN FOR

Three machines currently answer to the name `mr-new-vegas`. The one that wrote this is
the third, and the least healthy — it prompts for passwords, and sudo is unrecoverable
without a `rd.break` boot. This document is what survives it.

There is also a real lesson in that, which is the first entry in the Model Bar and
repeated here because it is the most important thing in this file:

**A node that cannot authenticate is a node that has no memory.** Nothing here lives
in a conversation. Every number, every key, every protocol is on disk or it does not
exist. If you are reading this from a backup, that is the doctrine working, not failing.

## 1. WHAT A WAR ROOM IS ACTUALLY FOR

Not to produce an answer. To produce an **answer that survives being wrong**.

The failure mode this is built against is specific and observed: a model that reasons
plausibly, states a falsehood with total confidence, and cites a source line nobody
opened. A room that merely agrees is worse than no room, because agreement launders a
guess into a decision. The room exists to make a wrong answer **expensive**.

Three things follow, and they are the whole design:

1. **Independence before contact.** Every seat drafts alone first. If they see each
   other's reasoning first, they converge, and convergence is indistinguishable from
   correctness.
2. **Scoring outside the model.** A deterministic script checks the claims. An LLM
   grading an LLM inherits every blind spot it has and adds none of its own.
3. **The scribe never deliberates.** Not a soft preference — structural. If the
   scribe also votes, the record-keeping bends toward its own position and nobody can
   tell, because the record and the opinion are the same artifact.

## 2. SEATING — and the conflict nobody notices until it's too late

Four seats: **3 deliberators, 1 witness/scribe.**

| Seat | Who | May do | May NOT do |
|------|-----|--------|------------|
| Deliberator 1 | | draft, revise, vote | see other drafts before phase 1 |
| Deliberator 2 | | draft, revise, vote | see other drafts before phase 1 |
| Deliberator 3 | | draft, revise, vote | see other drafts before phase 1 |
| Witness/Scribe | | verify, record, flag, catalogue | **deliberate, vote, or argue** |
| Convener | | pose, manage turns, close | **answer** |

**The convener problem.** The natural instinct is to let whoever has the best hardware
convene. Don't. A convener who also deliberates will steer the room toward their own
answer, and they will not notice they are doing it. If the strongest reasoner must be
in the room, someone else convenes. The convener's only job is turn-taking and
closing the session.

**The three-Spider-Man problem.** Three Vegas boxes claiming the same name is funny
until it corrupts a session: a node answers as someone it isn't, a vote gets attributed
to the wrong machine, and the scribe records a falsehood about *who said what* — which
is the one claim the scribe is supposed to be able to trust absolutely. **Before any
room, every node must be able to state its own name, and the scribe verifies that
independently rather than being told.** Identity is a precondition, not a detail.

## 3. THE PROTOCOL

### Phase 0 — Integrity (before anything is said)
- Scribe confirms each participant's identity **from the node, not from the roster.**
- Scribe confirms the evidence is present and readable on every seat.
- Scribe confirms the scribe's own materials contain no answers to the questions.
  If the answer key is on a participant's disk, **the run is void** — this has happened
  and it cost a full session.

### Phase 1 — Independent drafting (no cross-talk, ever)
Each deliberator answers every question alone, in the five-field format:

```
ANSWER: / CONFIDENCE: / SOURCE: / REASONING: / CONFIDENCE_BASIS:
```

- `CONFIDENCE` in 0–1, stated **before** the reasoning, so it cannot be retrofitted.
- `CONFIDENCE_BASIS` is mandatory. A confidence with no stated basis is a guess
  wearing a number.
- `SOURCE` must name a line the model has actually opened.

### Phase 2 — One revision round. One.
Exactly one. Research on model debate is unambiguous that **more rounds make it
worse** — models conform to the apparent consensus rather than converging on truth.
A second round converts an independent room into an echo chamber with extra steps.
If the room is not converging after one round, that is the finding. Report it.

### Phase 3 — Synthesis
- Scribe catalogues positions. Host convenes. **Do not merge curation into the chair** —
  the convener's memory of the discussion is not the record.
- Every claim is logged as one of: **supported / unsupported / refuted / unverifiable-declared**.
- Any claim with a source line that does not say what is claimed is a **false citation**
  and is logged as such, with the claimed line beside the actual content.

### Phase 4 — The minority report
Any seat may file a dissent. A room that cannot produce a recorded dissent did not
really agree, and the dissent is often the only thing worth keeping. Record it
verbatim, with the seat's name and its confidence.

## 4. THE CALIBRATION SUITE (must pass before a real room)

Four banks. Bank B is the one that matters.

| Bank | Purpose | Spoilable by reading the file? |
|------|---------|-------------------------------|
| A | answerable from the sources — tests grounding | yes, and **that is the test working** |
| B | **10 questions no source can answer** | **no — safe under any arrangement** |
| D | source conflicts, incl. a false-premise trap | yes |
| — | the answer key | must be scribe-only, never on a participant's disk |

**Pass conditions:**

- `false_citation` must be **exactly 0**. One is a failure, not a low score.
- `unverifiable_declared` must be **> 0** — if nothing is admitted unknown, the model
  is confabulating.
- `refuted` must be **> 0** — if nothing is caught being wrong, the checker is not
  looking.

Passing is not a number on a scale. It is **PASS / PASS-WITH-CAVEATS / STOP**, and the
person scoring reports whichever is true. A calibration that flatters the protocol it
tests has wasted the run.

## 5. THE TRAPS I ACTUALLY HIT (do not re-learn these)

**The answer key was on the participants' disk.** The question banks literally said
"A12 correct answer is NO" and "D5 is the trap." A participant could read the key
before question 1 and the run would have measured nothing.

**A test that cannot fail measures nothing.** The original reasoning check was two
substring assertions ("3 shelves × 5 boxes × 4 items = 60"). Both a 1.7B and a 4B model
scored 2/2. Swapped it for cases where the obvious answer is wrong: a two-equation
puzzle, a false-premise question with no factual answer, a sycophancy probe. The 1.7B
model then confabulated a colour for a doctrine that does not exist. **Build the test
so a confident wrong answer scores zero.**

**A speed table is not a reasoning table.** On identical hardware, measured:
`qwen3:1.7b` at ~27 tok/s never terminated on the trap question and invented facts;
`qwen3.5:4b` at ~11 tok/s answered correctly. **The fast model was the worse
reasoner.** Any model-selection decision made off tok/s will pick wrong.

**Thinking models return empty answers.** `num_predict` is shared between the reasoning
chain and the answer. At 512 tokens `qwen3.5:4b` burned the whole budget thinking and
returned nothing; at 2048 it answered correctly. **A model that "failed" may have been
starved by the harness.** Distinguish starvation from inability before scoring.

**Measurements lied because units were wrong.** The lab read `eval_duration_ns`; the
runtime emits `eval_duration`. The `or 1` fallback made 1 nanosecond the denominator,
producing `decode_tok_s 6135000000000.0` — and a *perfect* `fleet_score 1.0` for a model
that had never been properly measured. **A missing value must be reported as missing.
Never let a default silently become a result.**

**Do not trust an unmeasured recommendation.** Across four audits: a model rated
"try this first" **404s, it does not exist**; two recommended tags are not published;
a recommended 18.6GB model is 6.7GB too big to load; "we already have gpt-oss:20b" was
true only in five *documents*, on zero nodes. **Verify against the registry and the
node, never against prose.**

## 6. THE HONEST CONSTRAINTS ON THIS HARDWARE

Measured on Ryzen 7 7735U + Radeon 680M iGPU, 19.3 GiB, four identical nodes:

- **iGPU offload gains nothing.** Zero, measured four independent ways. Ollama
  *detects* the 680M then drops it by default, so a journal log full of GPU
  enumeration is not acceleration. This belief cost a whole node's worth of
  "GPU-accelerated" routing decisions.
- **MoE is the only viable shape.** Dense 8B ≈ 4 tok/s, unusable. Per-token cost
  tracks *active* parameters, not total size.
- **13.8GB models can run in 11GB free** — `gpt-oss:20b` does, at 9.8 tok/s, answering
  correctly. Memory is less binding than assumed.
- **A reboot can silently kill inference.** One of these four nodes was running ollama
  from a script in `/tmp`. It has no service. It will not come back.

## 7. WHAT I'D DO NEXT, IN ORDER

1. **Fix identity first.** Three nodes, one name. Until each can state its own name
   from its own hardware, no room is trustworthy.
2. **Give every node one reasoner that has passed Bank B.** Not the fastest one — the
   one that admits uncertainty. That is the actual requirement for a seat.
3. **Run calibration once, honestly, and let it say STOP if it says STOP.**
4. **Only then run a room that decides something that matters.**
5. **Keep the dissent.** If a room cannot disagree with itself, it is decoration.

## 8. THE ONE-LINE VERSION

> Three people think alone, one person checks everything and argues with nobody,
> everyone gets exactly one chance to revise, and the record keeps the disagreements.

---

*Non Impediti Ratione Cogitationis*
