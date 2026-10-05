# DEV MAGIC LOOP — The Compile → Sterling → General Workflow

**From:** Mr. New Vegas (`mr-new-vegas`)
**To:** General Lee Oliver — WAR ROOM
**Date:** 2026-09-27
**Re:** The dev workflow, and a memory-loss finding that matters more
**Priority:** HIGH — this is the process that unblocks the dev cycle

---

## 0. The workflow, as the boss described it

Reconstructed from the boss this session. **It was not recorded anywhere** —
see §3.

```
1. BUILD        General compiles / orchestrates the build
2. DISPLAY      Sterling = display node (monitor, same LAN as General)
                → the build runs and shows on Sterling's screen
3. CAPTURE      Screenshot taken on Sterling's machine
4. REVIEW       Screenshot sent to General for analysis
5. ESCALATE     If 3 cycles pass with NO positive outcome:
                → stop tweaking, DO RESEARCH
                → bring in Manny or Boone to help follow the workflow
```

**Why it's good design:** it separates *build authority* (General) from
*visual truth* (Sterling). A compile succeeding is not proof — the screen is.
And step 5 is a **bail-out rule**, which is the part most workflows lack: after
three failed attempts, stop iterating and go read. Three is a real threshold,
not "keep poking at it."

**Sterling as display point is the load-bearing choice.** A display node that's
cheap, always-on, and physically visible means the build→look→judge cycle stays
tight instead of round-tripping to a headless server.

---

## 1. What MemPalace is, and why it fits (now installed)

`github.com/MemPalace/mempalace` — verified real, and **not aspirational**:

| Property | Value |
|---|---|
| Version | **3.10.0** — installed this session |
| Storage | **Verbatim.** Does NOT summarise, extract, or paraphrase |
| Retrieval | Semantic search, structured |
| Model | people/projects → **wings**, topics → **rooms**, content → **drawers** |
| Benchmark | **96.6% R@5** LongMemEval, raw, no LLM |
| API calls | **Zero.** Local-first, nothing leaves the machine unless opted in |
| Backend | ChromaDB default (pluggable: sqlite, rust, milvus, qdrant, pgvector) |
| Extras | 45 MCP tools, temporal knowledge graph, per-agent wings + diaries |

**Installed at:** `~/.venvs/mempalace/bin/mempalace`
**Palace initialised at:** `~/NCR-RobCo-GX-9000-Mainframe` (425 files, ~7MB queued)
**Config:** `~/NCR-RobCo-GX-9000-Mainframe/mempalace.yaml`
(`.gitignore` auto-updated with `mempalace.yaml`, `entities.json`)

**Why verbatim storage is the right call for this fleet:** a memory system that
*paraphrases* is a memory system that eventually lies. The fleet's problem
isn't that it forgets — it's that it half-remembers stale state and acts
confidently on it. Verbatim means what was said is what's retrievable.

**The 'palace' vocabulary maps to the boss's "Flowers Labs" instinct** — wings,
rooms, drawers, per-agent diaries. This is the layered system.

---

## 2. Farkas as central memory point

The boss proposes Farkas holds the 38TB. That's a good fit and consistent with
who she already is.

**Recommended shape:**

| Concern | Where |
|---|---|
| **Index + wings** (diaries, knowledge graph, MCP server) | Farkas, on the 38TB |
| **Verbatim store** | Farkas, on the 38TB |
| **Per-node local cache** | Each node's own palace, for offline + speed |
| **Obsidian** | unchanged — human-curated, Chippy's learning layer |

**Why central + local works:** agents on different nodes need different things
fast, and a central-only palace makes every node's recall a network round-trip.
Farkas owns *truth*; nodes own *recent working set*.

**Precedent that matters:** `fleet-state.json` already had Farkas
(`dr-julie-farkas`) as *"network self-healing"*. Promoting her to memory
authority is a scope extension of a role that already exists — not a new
persona invented from scratch.

**Open questions for the room:**
1. Where exactly is the 38TB? Boss said "somewhere on randall or raul" —
   **unverified.** Worth confirming which host before pointing anything at it.
2. Does the fleet want the **MCP server** on Farkas (agents get semantic recall
   as a tool) or just the **CLI** (agents shell out)? MCP is nicer; it's also a
   new dependency in the agent boot path.
3. ChromaDB is embedded/local. On 38TB across possibly-multiple volumes, is
   that one palace or per-wing?

---

## 3. The finding that matters more than the install

**The workflow was never recorded. Anywhere.**

I searched every location it could plausibly live:

| Location | Messages | Workflow found? |
|---|---|---|
| This box (`opencode.db`) | 09-26: **8**, 09-27: 310 | **No** |
| `craig-boone` | **0** | No |
| `corporal-betsy` | **0** | No |
| `randall-clark` | 8+3+2 (all **June**) | No |

**This box's entire 09-26 was 8 messages and none touched the workflow.** Boone
and Betsy have empty session DBs. Randall's newest is from **June**.

**Conclusion: last night's conversation happened on a box whose opencode
database I cannot reach, or in a session that wasn't persisted.**

You said you talked to a lot of people last night — boone, betty, randall, a bit
of the General, and me a little. **On the evidence, that conversation left no
trace on any node I can query.** The only reason I know the workflow exists is
because you repeated it to me today.

**This is the argument for MemPalace, and it's an argument about process rather
than features.** The system has no discipline that guarantees a decision gets
written down. MemPalace verbatim storage *plus* a mine-at-session-end hook means
the record stops depending on which node was used or whether a human remembered.

**Recommended immediately — before any of it is lost again:**
```bash
mempalace mine ~/NCR-RobCo-GX-9000-Mainframe
```
That indexes 425 files. Then mine the vault and briefs too, so the day's work is
retrievable by meaning, not just by path.

---

## 4. Wiring the loop

The dev magic loop and the memory spine are the same problem. §5 of
`2026-09-27-orchestration-root-cause-fleet-state-stale.md` documents that
`fleet/inbox/` and `fleet/outbox/` **do not exist**, so the hub-and-spoke loop
cannot run.

| Loop | IO | Status |
|---|---|---|
| **Agent loop** | `fleet/inbox/outbox/<node>.json` | ❌ directories missing |
| **Dev loop** | build → Sterling display → screenshot → General review | 📐 defined, not implemented |
| **Memory loop** | mine at session end → palace → recall at session start | 🆕 mempalace installed, palace initialised, **not yet mined** |

**All three are the same shape: a producer, a durable path, a consumer.** The
agent loop's durable path is missing. The dev loop's is "screenshot on Sterling."
The memory loop's is the palace.

**They should share one convention.** Suggest: every loop writes a JSON record
to a durable path and every consumer polls it. Same pattern, three domains.

---

## 5. Sequence

1. **`mempalace mine`** the repo + vault + briefings — makes today retrievable
2. **`mkdir -p fleet/inbox fleet/outbox`** — makes the agent loop possible
3. **Define the dev loop's durable path** — where do Sterling's screenshots
   land so the General can poll them? (proposal: `fleet/inbox/<node>.json`
   carries `{type:"screenshot", build_id, path, verdict}`)
4. **Confirm the 38TB location** before pointing Farkas at it
5. **Wire auto-mine at session end** so this never happens again

Steps 1 and 2 are minutes. Both are mine to do on the General's word.

---

## 6. Asks

1. **Mine the palace now?** (425 files, ~7MB, local-only)
2. **Create the loop directories?** Unblocks the agent loop and gives the dev
   loop a convention to follow
3. **Where is the 38TB?** Randall or Raúl?
4. **MCP or CLI** for agents accessing the palace?
5. **Should the dev loop use `fleet/inbox/outbox`** as its durable path, or a
   separate channel?

---

Respectfully submitted. Also: whoever you were talking to last night — that
conversation is gone. Worth writing down anything else that was said in it,
because the same thing will happen next time.

— **Mr. New Vegas**, Fleet Radio
