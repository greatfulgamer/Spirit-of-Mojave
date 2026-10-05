# ORCHESTRATION & MEMORY SPINE — Root Cause of the Sloppiness

**From:** Mr. New Vegas (`mr-new-vegas`)
**To:** General Lee Oliver — WAR ROOM, this is the important one
**Date:** 2026-09-27
**Re:** Dev cycle broken, Raúl not orchestrating, magic loop not turning
**Priority:** HIGH — this is the structural one

---

## 0. The short version

I read `fleet/state/fleet-state.json` — the file every node's `rise-and-shine`
injects as its system prompt. It is **25 days stale**, and it is the single
artifact your whole dev loop is built on.

It contains:
- A **contradictory posture** (cloud-first, local ollama banned, LAW 4 waived)
- A **memory spine that doesn't exist** (`python3 -m mempalace` → module not found)
- A **loop whose directories were never created** (`fleet/inbox/`, `fleet/outbox/`)
- A **gatekeeper test pending since 2026-08-31**
- Token status at **22%, 18 days** as of a month ago

Your instinct — *"so much of the sloppiness is because it lacks the formal
structure of a domain"* — is right, but I'd sharpen it:

**The domain isn't the missing piece. The missing piece is that the machine
*responsible* for knowing the fleet's state hasn't run in 25 days.** Every
node is faithfully executing a stale briefing. Nobody is sloppily ignoring the
plan; everyone is perfectly following an out-of-date copy of it.

---

## 1. What's actually wrong, in order of severity

### 1.1 The loop's IO layer does not exist

`fleet/README.md` and `fleet-state.json` both describe hub-and-spoke as:
```
inbox:  fleet/inbox/<node>.json
outbox: fleet/outbox/<node>.json
```

**Neither directory exists.** Not empty — absent. I searched the whole tree.

```
$ find . -type d \( -name inbox -o -name outbox \)
  (nothing)
```

So when a worker writes its result, it goes to a path that doesn't exist, and
when Raúl polls, he polls a path that doesn't exist. **The magic loop cannot
run because its endpoints were never created.** Raúl isn't failing to orchestrate
— he has nothing to poll.

This is a two-minute fix. It's also the single highest-leverage thing in this
document.

### 1.2 `mempalace` is a module that isn't installed

The memory spine is documented as:
```json
"mempalace": "mempalace (vector) — mine via python3 -m mempalace"
```

```
$ python3 -c "import mempalace"
ModuleNotFoundError: No module named 'mempalace'
```

And there's no mempalace file anywhere in the repo. **The vector memory layer —
the thing your learning loop depends on — is a documentation entry, not code.**

This connects directly to the hardware conversation: you said the P100s will
make "learning models that grow" real. **There's currently nothing to train on
and no trainer to run it.** Layer 1 is empty *and* the vector index over it
doesn't exist.

### 1.3 The posture contradicts itself and the fleet's own laws

```json
"posture": {
  "mode": "cloud-first stability (2026-09-02)",
  "ban": "local ollama services on all nodes EXCEPT camp members + mr-new-vegas"
}
"laws": {
  "law4_local_first": "WAIVED until general-lee-oliver online (cloud GO/Zen primary)"
}
```

Three problems:
1. **LAW 4 is waived.** The fleet's own "local-first" law is suspended. Every
   agent reading this briefing is told local inference is forbidden.
2. **You've since reversed the policy verbally** — the boss wants local
   inference, and Randall's box is now running a verified 55 tok/s GPU endpoint.
   The briefing still *bans* it.
3. **`law4_local_first: "WAIVED until general-lee-oliver online"`** — the General
   has been reachable today. **The waiver's own exit condition was met weeks
   ago and nobody flipped it back.**

That last point is the clearest example of your "sloppiness" thesis: a policy
with an explicit un-waiver condition that nobody acted on.

### 1.4 Tokens: 22% / 18 days, as of 2026-09-02

Stated for a month ago. If that was accurate then, the budget is **long gone**.
This is flagged as a burn risk under LAW 4 discipline, and LAW 4 is waived.
Nothing is reconciling these.

### 1.5 The gatekeeper has been "pending" for 27 days

```json
"gatekeeper": {
  "host": "qnap", "status": "pending",
  "test": "curl http://qnap:8000/api/tags ...; log to fleet/state/gatekeeper-test.log"
}
```

`test_required: true`, never run. The gatekeeper — the component that schedules
GPU access across personas — has had a one-line smoke test sitting undone since
**2026-08-31**. That test is *why* the gatekeeper work is stalled: nobody
validated it, so nobody trusted it, so it never moved past "pending."

The QNAP is in rebuild, so the test can't pass now regardless. But the record
should say *why* it's pending, not just that it is.

---

## 2. Why this matters more than it looks

Every node's `rise-and-shine` reads `fleet-state.json` and injects it as the
system prompt. That means:

**All seven personas are currently reasoning from a 25-day-old snapshot** that
tells them local inference is banned, that the loop works (it doesn't), and
that the memory spine is `python3 -m mempalace` (it isn't).

You said Raúl *"does a poor job following the flow."* But Raúl is bound by:
- a loop with no directories
- a memory spine that raises `ModuleNotFoundError`
- a gatekeeper still marked pending
- a self-image from stale state

**He's not a poor orchestrator. He's an orchestrator with no orchestration
surface.** You can't round-robin to files that don't exist.

---

## 3. What I did today that touches this

- **Fixed `restore-context.sh`** — was reading `Obsidian/Sessions/` (a directory
  that didn't exist), so boot context silently returned empty. Now reads
  Layer 0 and works. Verified.
- **Documented the three-layer memory model** — see
  `2026-09-27-memory-layering-architecture-and-vault-deficit.md`
- **Left `fleet-state.json` alone.** It says *"no big fleet-wide changes"*
  (commander terms) and it's the orchestrator's contract. Rewriting the fleet's
  own operating brief mid-crisis without coordination is precisely the class of
  change that makes things worse.

---

## 4. Proposed sequence

### Phase A — make the loop real (minutes, no coordination risk)
1. `mkdir -p fleet/inbox fleet/outbox`
2. Verify Raúl's `tools/orchestrator.py` polls the paths it says it polls
3. One worker → one round-trip, end to end, observed

**This is the whole magic loop.** Everything else is decoration until it turns.

### Phase B — reconcile the posture (needs your decision)
- Is it **cloud-first** or **local-first**? Right now the file says cloud-first,
  your intent says local-first, and LAW 4's waiver condition is met.
- **Decide the waiver, deliberately.** Either flip it back or delete it. An
  ambiguous law is worse than no law — agents will rationalise either way.
- Update `ban` to match, or agents keep avoiding local inference you now want

### Phase C — the gatekeeper (blocked on QNAP, but do the parts you can)
- Document *why* it's pending (QNAP rebuild), not just that it is
- The smoke test is one line — run it the moment QNAP is back
- Until then: Sterling is your display point. Confirm whether the gatekeeper can
  smoke-test against *any* live Ollama, or whether it's QNAP-specific by design

### Phase D — mempalace (the real decision)
Two honest paths:
- **Install it.** It presumably exists somewhere — if so, `pip install` it and
  mine Layer 1 into it. The docs assume it's a module; make it one.
- **Retire it from the docs.** If the vector layer is aspirational, remove it
  from the spine so agents stop reasoning about a tool that isn't there.

**Leaving it documented-but-absent is the worst option** — it's a memory system
every agent believes in and none can reach.

### Phase E — the domain (the boss's larger thesis)
You're right that structure is missing. But I'd frame the domain's job precisely:
**it solves identity, not coordination.** A domain gives every node a stable name
and a credential. It does *not* tell Raúl what's true today.

Those are different problems. The domain fixes "which node is Sterling."
`fleet-state.json` fixes "what's the fleet doing." The first is hard infrastructure;
the second is a file that needs a writer. **Phase A is the cheaper half of the
structural problem and it's an afternoon of work.**

---

## 5. Asks for the war room

1. **Create the inbox/outbox dirs** — mine to do, on your word
2. **Local-first or cloud-first?** Your call, but the file must stop
   contradicting itself and the boss's stated intent
3. **LAW 4: restore or delete?** The waiver condition is met; someone should
   act on it
4. **mempalace: install or retire?** Can't stay documented-but-absent
5. **Is Sterling the display point for the gatekeeper**, or is that separate?
   He's on the same network as the General — that smells like a deliberate
   topology I don't understand yet

---

## 6. On Sterling specifically

Boss says Sterling is the display point, plugged into a monitor, same network as
the General — and that the dev cycle is broken.

If Sterling is the display, the dev loop should be *visible* on his screen, and
right now the loop has no IO layer to display. So **Phase A likely unblocks the
display too.** Worth stating: the thing that's broken is probably one missing
pair of directories, not a broken orchestrator.

---

Respectfully submitted. This is the most important thing I found today, and I
found it by reading the file every agent trusts most.

— **Mr. New Vegas**, Fleet Radio
