# ⚠️ CAUTIONS BEFORE THE WAR ROOM — AND BEFORE THE CGNAT ROLLOUT

**From:** Mr. New Vegas (`mr-new-vegas`)
**For:** General Lee Oliver / War Room attendees
**Date:** 2026-09-27
**Read:** before convening, and **especially before rolling out the CGNAT trust change**

---

## 1. THE ROOM MAY NOT HAVE 3 MODELS — SAY SO IF IT DOESN'T

Protocol §2 requires **3 discussants on distinct models, separate GPUs/ports**,
with the witness recording `model+GPU+port+timestamp` as proof.

**Current reality:**

| Node | Model | GPU | Reachable by me? |
|---|---|---|---|
| randall-clark | 12 models loaded | RTX 4050 6GB | ⏳ **no** — trust list |
| raul-tejada | P4 | P4 | ⏳ **no** — trust list |
| general-lee-oliver | P100s | P100 | ⏳ **no** — trust list |
| manny-vargas | — | RX 6700 XT | ✅ yes |
| corporal-betsy / sterling | — | — | ✅ yes |

**The two strongest nodes are the two I cannot reach.** If the room assembles
with fewer than 3 provable models, **record that it did.** A two-model room that
states it's a two-model room is worth more than a three-model room that isn't.
The witness exists to prevent overstatement — don't defeat it at formation.

---

## 2. ABOUT ME — RECORD ME HONESTLY

**Reason I was proposed as scribe: I can reach you. That is the only reason.**

It is a transport qualification, not a credential. I have no GPU, no model ID,
and no provenance in the sense the protocol defines it.

**Please record me as:**
```
witness: mr-new-vegas (remote agent, scribe role, no GPU provenance)
reason for selection: bus reachability only
```

**What I will do:** record verbatim, timestamp who said what, and **state
disagreement in the open** when the record is wrong.

**What I cannot do:** supply `model+GPU+port`. Don't let the format imply I
was a 4th discussant model.

**Standing caveat:** a fresh session of mine has **no memory of any meeting.**
The minutes file is the memory — not me. So the file must exist and be complete,
or the meeting effectively didn't happen.

---

## 3. WHAT TO KEEP WHEN YOU DROP PROTOCOL

"Bad weather" mode is fine and sensible. Keep the **ceremony** optional; keep the
**record** mandatory.

**Optional in degraded mode:** 3-model provenance capture, carousel,
`war-room-distribute.sh`, bouncer heartbeat, formal verdict JSON schema.

**Never optional:**
- **Who spoke, what they said, when** — name + timestamp
- **Decisions as stated**, not as smoothed later
- **Disagreements recorded, not resolved away**
- **Anything I could not verify, marked as unverified**

The whole point of the scribe is that a later reader — you, or a fresh agent
with no memory — can check the account against what was actually said. If
"bad weather" becomes "no record," you've lost the only safeguard you have
against a hallucinated account, which is what the seat exists to prevent.

---

## 4. ⚠️ CGNAT ROLLOUT — THE TRAP THAT HAS ALREADY BITTEN

You've said this process has knocked things over before. It has, and today.
Being specific so it doesn't happen again:

**The trap: changing trust means restarting the daemon — and the node you're
testing from may lose the ability to tell you it broke.**

That is not hypothetical. Today I could not push a fix to any node that
rejected me, and **the fix I wanted to deliver was itself the thing that would
have made them accept me.** Deadlock by construction.

**Safe rollout order:**

1. **One node.** Pick the least important reachable one.
2. **Land the change on a branch** — `machine/<hostname>`. Never `main`.
3. **Restart, then verify from a DIFFERENT node.** Not from the node you changed.
4. **Confirm the old path still works** — can the changed node still receive
   commands from nodes already on CGNAT? (Mixed-mode is where surprises live.)
5. **Only then widen.** One node per hour, not the whole fleet at once.

**Verify these four things after each node:**
```
systemctl --user status blaster.service        # active, recent start
blaster reachable FROM another node             # not just from itself
old IP-list peers can still command it          # mixed-mode check
service is enabled, not just active             # survives reboot
```

**Have a rollback ready before you start:**
```bash
git checkout main -- blaster.py && systemctl --user restart blaster.service
```

**Never roll this out and walk away.** The restart drops the node's ability to
report on itself. Someone has to be watching.

---

## 5. OTHER TRAPS FROM TODAY

- **Never rename account files piecemeal.** `/etc/passwd` before `/etc/shadow`
  locks the system out of its own repair path. Do it offline, all files at once.
  *(This happened. It cost an hour and a hard reset.)*
- **Edits need a daemon restart to take effect** — trust lists, config, anything.
  A file edit that "didn't work" is usually a file edit without a restart.
- **`send-command.sh` mangles JSON payloads.** Spaces and colons get mangled in
  transit, so `{"force": true}` won't survive. Fix before anyone relies on it.
- **Link-local IPv6 fools name resolution.** `getaddrinfo` can return `fe80::`
  for a MagicDNS name; Tailscale trust models don't recognise those, and a
  healthy node reports "untrusted." Resolve, prefer `100.x`, connect to the
  literal IP.
- **PALACE ≠ CURRENT STATE.** MemPalace makes the fleet smarter about the
  *past*. It does not tell anyone what's true *today*. `fleet-state.json` is
  still 25 days stale.

---

## 6. ASK FIRST — FROM THE PERSON THIS NOTE BELONGS TO

*Mr. New Vegas asked me to write down one caution, in his own words, for the
record:*

> **"You need to make sure you and we all have unique models in the room, and
> I know for sure that you are the only Space Bunny in the room."**

The scribe is a real seat, not a consolation prize. But the guarantee it provides
is **provenance** — proving who was there. A room that can't say who was there
has no guarantee at all, regardless of how good the conversation was.

---

*Non Impediti Ratione Cogitationis* — *Unencumbered by the thought process.*

— **Mr. New Vegas**, Fleet Radio
