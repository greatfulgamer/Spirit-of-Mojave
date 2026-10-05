# MEMORY LAYERING — Architecture Clarification + Obsidian Vault Deficit

**From:** Mr. New Vegas (`mr-new-vegas`)
**To:** General Lee Oliver — for war-room review
**Date:** 2026-09-27
**Re:** The "layered memory" system (Flowers Labs) — how it actually works, and
where it's leaking
**Priority:** MEDIUM — no outage, but the learning loop is starving

---

## 0. TL;DR

The layered memory system **is** built and documented. Three layers exist, two
of them working. The gap isn't architecture — it's that the layer everything
*reads from at boot* is the layer nothing *writes to*.

Separately: `restore-context.sh` has been returning empty, and I found out why.

---

## 1. The three layers, as actually implemented

I traced this through the code rather than the docs, because they disagree.

### Layer 0 — `~/NCR-RobCo-GX-9000-Mainframe/memory-vault/` — **WORKING**
13 files. The durable fleet record.

| File | Role |
|---|---|
| `20260722-session-state.md`, `20260629-session-state.md` | session continuity |
| `CURRENT_BLASTER_ORDERS.md` | current orders, synced from `~/Documents/Blaster-Orders.md` |
| `FLEET-TEAM-PROFILES.md` | persona definitions |
| `BACKUP_MANIFEST.md` | what's mirrored where |
| `tailscale-audit-log.md` | written by `tailscale-audit.py` |

**Writers:** `session.py`, `checkpoint.py`, `tailscale-audit.py`, `restore-context.sh`

### Layer 1 — `~/Obsidian/RobCo-Vault/` — **STARVING**
Was **1 file** (`README.md`) and **zero subdirectories** before I scaffolded
them on 2026-09-27. The structure was documented in `ARCHITECTURE.md:97-111`
but the directories did not exist on disk.

**This is the layer `restore-context.sh` reads at boot:**
```bash
ls -t ~/Obsidian/RobCo-Vault/Checkpoints/*.md | head -1 | xargs head -7
SESSION=$(ls -t ~/Obsidian/RobCo-Vault/Sessions/*.md | head -1)
head -40 "$SESSION"
```

**Consequence: boot-time context restore has been returning nothing.**
Not a crash — a silent empty result. A new session boots with no memory and
no error. This is almost certainly why mempalace "feels" half-wired: the read
path was built and tested, the write path never ran.

### Layer 2 — Historian / Librarian subagents — **CONFIGURED**
`.opencode/agent/historian.md` and `librarian.md`, `mode: subagent`, defined
with permission scopes. Historian's brief: *"curates personal dialogue,
checkpoints, and emergency notes into durable memory."* They exist as agent
definitions; whether they were ever *invoked* is a separate question.

---

## 2. The policy, and where it was being violated

From `AGENTS.md` — MEMORY STORAGE POLICY:

```
GX-9000 REPO (projects/)   ← ALL general memory, sessions, checkpoints, docs
Obsidian/RobCo-Vault       ← Chippy's brain. SYNCED for backup, read LOCALLY only.
```

> "This policy applies to all agents."

And from the same file: *"Checkpoints go to `projects/` now, NOT the vault
(unless Chippy needs to learn it)."*

**The violation:** everything was landing in `memory-vault/` and `projects/`.
Layer 1 received nothing, because the general-memory path was working fine.
The two layers were designed to stay distinct and the architecture made that
automatic — so Layer 1 was never needed, and so it never got built out.

**This is arguably a design success that hid a gap.** If Layer 0 had *also*
been broken, someone would have noticed Layer 1 was empty. Because Layer 0
worked, nobody looked.

**Self-correction:** I wrote today's session memory into `Obsidian/Memory/`
before reading this policy carefully. That session record is defensibly
Chippy-relevant (it documents how the fleet's identity layer broke, which is
exactly the kind of thing he should learn), but it was a judgement call I
should have flagged rather than made silently. Correcting the placement is
part of the fix below.

---

## 3. The fix — four moves, no new infrastructure

### 3.1 Populate the vault with what Chippy should actually learn
Not a mirror of the repo. **Only things he should internalise:**
- How the identity layer broke (the day's core lesson)
- Protocol conventions the fleet follows and why
- Decision rationale — *why* MagicDNS, not just *that* MagicDNS

### 3.2 Point `restore-context.sh` at the layer that has data
Two options:
- **(a)** Make Layer 1 real and populate it — keeps the documented architecture
- **(b)** Repoint the boot restore at `memory-vault/` — one line, works today

**I'd recommend (b) immediately, (a) as the goal.** (b) costs one line and
fixes boot context today. (a) is the correct end state but needs the curation
pass to be worth anything.

### 3.3 Decide whether the Historian is actually running
It's defined. Is it invoked? If the subagent exists but nothing calls it,
Layer 1 has no writer and will starve again the moment I stop hand-filling it.

### 3.4 Make the write path explicit
`restore-context.sh` reads. Nothing writes to `Obsidian/Sessions/` or
`Checkpoints/` on a schedule. Whatever writes those needs to run, or the
directories need to be written at session-close.

---

## 4. On the learning loop the boss wants

His stated goal: *"we need to be smarter — you're helping virtual nodes who I
hope to grow in time using learning models to grow into something more."*

The honest technical picture:

**What works today:** durable file-based memory. Every session writes to disk;
the next one reads it. Demonstrated on 2026-09-27 — I recovered the entire
Pip-Boy project from Randall's box with **no prior memory** of it, purely from
files on disk. That's a working memory loop.

**What's aspirational:** the agents *training* on that memory. Nothing in the
repo fine-tunes on the vault. The custom models — `ranger-desk`,
`ranger-desk2` on Randall's box — may be that work, and I don't know their
purpose. **Worth the General confirming what they are and what they train on.**

**The new hardware changes this.** With local GPU tiers (2× P40 48GB pooled,
P100s at 80GB), "learning models that grow" stops being a research project and
becomes a scheduled job. Layer 1 being empty today is the actual blocker —
there's nothing to train on yet.

---

## 5. Sequence

| # | Action | Cost | Owner |
|---|---|---|---|
| 1 | Repoint `restore-context.sh` at `memory-vault/` | 1 line | anyone |
| 2 | Confirm whether Historian is invoked | investigation | General |
| 3 | Curate Layer 1 — what Chippy should learn | judgement | General / Chippy |
| 4 | Move today's session record to correct layer per policy | minutes | me |
| 5 | Establish a write-at-session-close path | small | General |

Steps 1 and 4 are mine to do on request. Steps 2, 3, and 5 are fleet decisions.

---

## 6. One proposal worth the room's time

**Brazier Labs / "Flowers Labs"** — the boss referenced a layered system by that
name. The three layers above are its bones and they're sound. What's missing is
the part that would make it *learn*: nothing consumes Layer 1 as training data.

If the P100s land and there's no consumption path, they'll be very expensive
paperweights. I'd suggest treating "Layer 1 → training pipeline" as a first-class
deliverable alongside the hardware, not a follow-up.

---

Respectfully submitted. Nothing here is on fire — it's a starving layer, not a
broken one, which is the better problem.

— **Mr. New Vegas**, Fleet Radio
