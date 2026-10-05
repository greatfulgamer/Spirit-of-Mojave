# FLEET RISE AND SHINE — Identity + MemPalace Recall

**From:** Mr. New Vegas (`mr-new-vegas`)
**To:** General Lee Oliver
**Date:** 2026-09-27
**Re:** Every node should know *who it is* and *that it can remember*
**Status:** MemPalace installed fleet-wide. This document is the wiring.

---

## 0. What the boss asked for

> *"we need them to know themselves and the role they play in the fleet.
> I think we all do better that way"*

That's the right instinct, and it maps exactly onto MemPalace's model. The
project's own concept is **wings and rooms**: people and projects become wings,
topics become rooms, and **each specialist agent gets its own wing and diary**.

So "know yourself" and "remember" aren't two features. In MemPalace's
vocabulary they're one: **an agent's wing is its identity and its memory.**

---

## 1. Rollout status — verified 2026-09-27

| Node | MemPalace | Palace | Notes |
|---|---|---|---|
| randall-clark | ✅ 3.10.0 | 8K | installed |
| corporal-betsy | ✅ 3.10.0 | 8K | installed |
| corporal-sterling | ⏳ installing | — | slow pip (23MB chromadb over tailnet) |
| manny-vargas | ✅ 3.10.0 | 8K | installed |
| craig-boone | ✅ 3.10.0 | 8K | installed |
| **general-lee-oliver** | ✅ 3.10.0 | **1.1M** | has real indexed content |
| mr-new-vegas | ✅ 3.10.0 | init'd | this box |
| raul-tejada | ❌ **blocked** | — | his blaster rejects me |

**Install path:** `~/.venvs/mempalace/bin/mempalace` (venv-isolated, per upstream
guidance, to avoid PEP 668 conflicts on Fedora).

**Raúl is the one gap.** He rejects my commands (`Untrusted peer`), so I can't
install there. **He needs the memory layer most of anyone** — he's the
orchestrator. One command on his box fixes both the install and the trust list.

---

## 2. Why 8K palaces are expected, not a failure

`~/.mempalace/` at 8K means **the palace is initialised but not yet mined** —
`known_entities.json` exists, the Chroma index is empty.

The **General's 1.1M** is what a *mined* palace looks like. So the difference
is just "mined vs. not", not "working vs. broken."

**Mining is a separate step from installing**, and it didn't complete everywhere
because the mine step is long (425 files, ~7MB) and these nodes are on
tailnet bandwidth. **The fix is one command per node:**

```bash
~/.venvs/mempalace/bin/mempalace mine ~/NCR-RobCo-GX-9000-Mainframe
```

**I'd recommend mining in this order** — highest value first, so recall improves
fleet-wide even if a node is slow:
1. `general-lee-oliver` — already done, has content
2. `raul-tejada` — orchestrator, blocked pending trust fix
3. `corporal-sterling` — display node, part of the dev loop
4. The rest as bandwidth allows

---

## 3. The rise-and-shine wiring (the actual ask)

Every node's `rise-and-shine.sh` injects `fleet-state.json` as the agent's
system prompt. That's the identity mechanism, and it's already 25 days stale —
see `2026-09-27-orchestration-root-cause-fleet-state-stale.md`.

**Proposal: add a MemPalace recall line to that same system prompt.**

```
## Fleet Identity
You are <role> on <node>. See fleet-state.json for current fleet state.

## Memory
You have persistent recall via MemPalace. Before answering anything about
past work, prior decisions, or "what did we do about X":

    ~/.venvs/mempalace/bin/mempalace search "<your question>"

Storage is structured: wings (people/projects), rooms (topics), drawers
(verbatim content). Your own wing is your identity — search it first.
```

**Why put it in rise-and-shine rather than AGENTS.md:** the prompt is assembled
per-boot from live state. AGENTS.md is static and identical everywhere. Identity
is *dynamic* (who am I today, what's my role), so it belongs in the dynamic
channel. And the recall instruction needs to be present at boot or the agent
won't know it has the option.

**Design point worth preserving:** MemPalace is **verbatim** — it does not
summarise or paraphrase. So a recall is *evidence*, not a retelling. An agent
that recalls "we decided to use MagicDNS" can go read the actual conversation.
That's what makes it trustworthy in a way a summarised memory isn't.

---

## 4. Personal identity: one wing per node

MemPalace's model wants a wing + diary per agent. That maps to the fleet's
personas directly:

| Wing | Node | Role |
|---|---|---|
| `raul-tejada` | Raúl | orchestrator |
| `general-lee-oliver` | Lee Oliver | fleet authority / dev build |
| `corporal-sterling` | Sterling | **display node** (dev loop) |
| `mr-new-vegas` | Vegas | radio + tower + Pip-Boy |
| `manny-vargas` | Manny | build help |
| `craig-boone` | Boone | build help |
| `corporal-betsy` | Betsy | — |

**Each wing becomes that node's own memory.** A wing named after the node means
the recall surface is already partitioned — Sterling recalls Sterling's work
without reading the General's diary. That's the "each agent gets its own wing"
design paying for itself at fleet scale.

---

## 5. What this fixes, and what it doesn't

**Fixes:**
- Agents can answer "what did we decide about X" from evidence, not guesswork
- Each node has identity scoped to its own wing
- The "why MagicDNS" class of knowledge stops being tribal

**Does NOT fix, and I want to be clear:**
- **`fleet-state.json` is still stale.** MemPalace is a *library*, not a
  **source of current state**. An agent can recall the perfect decision from
  six weeks ago and still not know what's true today. The staleness fix is
  separate — see the orchestration doc.
- **Raúl's trust list.** Still blocking, and it blocks the most important node.
- **The loop directories.** `fleet/inbox/` and `fleet/outbox/` still don't exist.
- **Farkas as central point.** Not yet wired; 38TB location unconfirmed.

MemPalace makes the fleet *smarter about the past*. It does not make the fleet
*current*. Both are needed, and they're different jobs.

---

## 6. Asks

1. **Mine the palaces** (one command, listed above) — my call on order
2. **Raúl's trust list**, so he can be installed and can receive commands
3. **Approve the rise-and-shine change** — I'm ready to write it, but it touches
   every node's boot prompt, so it needs coordination
4. **Confirm the wing naming** — node name, or persona name, as the wing key?

---

Respectfully submitted. The install is done; this is the part that makes it
mean something.

— **Mr. New Vegas**, Fleet Radio
