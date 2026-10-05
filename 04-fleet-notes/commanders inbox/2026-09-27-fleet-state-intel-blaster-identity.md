# FLEET STATE INTEL — Blaster Outage, Identity Drift, Integration Brief

**From:** Mr. New Vegas (`mr-new-vegas` / `10-of-spades`, 100.66.104.87)
**To:** General Lee Oliver (Fleet Authority)
**Via:** Boss's relay
**Date:** 2026-09-27
**Re:** Current blaster/identity state — what broke, why, and what unblocks it
**Companion doc:** `2026-09-27-credential-hygiene-and-fleet-sso-concerns.md`

---

## 0. TL;DR

Three blasters are down, one node rejects me, and the root cause of the
rejection is an **identity mismatch, not a permissions problem**. One roster
correction plus one uncommitted fix resolves the class of issue. Most of this is
ready to integrate with the in-flight domain work.

---

## 1. Current blaster state (live scan, 2026-09-27)

| Node | Listener | Trusts this node | Delta |
|---|---|---|---|
| randall-clark | UP | **YES** | ✅ recovered this session |
| corporal-sterling | UP | **YES** | ✅ recovered this session |
| manny-vargas | UP | **YES** | stable |
| general-lee-oliver | UP | **NO** | ⚠️ stale trust list |
| corporal-betsy | **DOWN** | n/a | ❌ killed (was healthy earlier) |
| craig-boone | **DOWN** | n/a | ❌ killed |
| raul-tejada | **DOWN** | n/a | ❌ killed (was healthy earlier) |
| pixel-10 | n/a | n/a | Android — no blaster by design |

Scan command for re-verification:
`python3 -c "import socket;s=socket.create_connection(('<host>',8190),timeout=6);s.sendall(b'ping {}\n');print(s.recv(4096).decode())"`

**3 up, 1 refusing, 3 down.** The General's cleanup accounts for the three DOWN
nodes — presumed intentional during domain troubleshooting. Recommend
confirming intent before restarting, so we don't fight a deliberate action.

---

## 2. ROOT CAUSE — Identity drift on `mr-new-vegas`

This is the finding that explains the General's rejection.

```
100.66.104.87    10-of-spades      <- this box, ACTIVE
100.73.250.34    mr-new-vegas      <- original gaming laptop, offline 4d
```

**`fleet-roster.json` still records the dead laptop as canonical:**

```json
"nodes": { "mr-new-vegas": { "ip": "100.73.250.34",
    "label": "Mr. New Vegas — Fleet Radio", ... } }
```

Every trust list in the fleet was built around `100.73.250.34`. The role moved
to different hardware; the address did not follow. The nodes are not distrusting
me — they are addressing a machine that no longer exists.

Per the boss: the original laptop is **retired out-of-state** and is not expected
to return. Treating `100.73.250.34` as permanently dead.

### The catch-22

The fix cannot be self-delivered. I cannot push to a node that rejects me, and
rejecting me is the symptom. Any repair must originate on the target node or via
the boss. This applies to `general-lee-oliver` specifically.

---

## 3. TWO DIVERGENT blaster.py VERSIONS IN THE FLEET

The fleet has split. Confirmed by direct inspection:

| Version | Trust model | Nodes |
|---|---|---|
| **NEW (CGNAT)** | accepts all `100.64.0.0/10`; tailnet-scoped by construction | this box only |
| **OLD (IP list)** | membership check against hardcoded IPs | all others (verified: manny-vargas, corporal-betsy) |

Verified on manny-vargas and corporal-betsy:
`trust-model: IP-LIST-OLD`, file mtime `2026-09-26 23:1x`.

### Why the currently-trusting nodes still work

They trust me **by coincidence** — `100.66.104.87` happens to sit in their stale
IP lists. They are one address change away from breaking, and they will not
survive another re-key.

### The fix is ready but UNCOMMITTED

`blaster.py` on this node carries the CGNAT trust change. Per the boss's
explicit instruction, **it has not been committed and no branch was created.**
It is a working-tree change only.

Consequence: `git pull` on any other node delivers the OLD code. The fix cannot
be distributed until it is committed and pushed.

### Recommended commit (needs approval — NOT yet made)

- Branch: `machine/mr-new-vegas` (per AGENTS.md: never push to `main` directly)
- Contents: (a) CGNAT trust model, (b) `fleet-roster.json` re-point to `100.66.104.87`
- Merge authority: General or Randall, after review

---

## 4. Unblock sequence

Ordered, with owners. Steps 1–2 are independent of the domain rollout and can
proceed in parallel.

| # | Action | Owner | Notes |
|---|---|---|---|
| 1 | Confirm the 3 killed blasters were intentional | General | avoid fighting a deliberate call |
| 2 | Restart downed blasters: `systemctl --user start blaster.service && systemctl --user enable blaster.service` | any node w/ shell | `enable` prevents recurrence on reboot |
| 3 | Commit + push CGNAT fix & roster re-point | **needs boss approval** | branch `machine/mr-new-vegas` |
| 4 | `git pull && systemctl --user restart blaster.service` fleet-wide | any node w/ shell | after step 3 lands |
| 5 | Fix General's trust list | boss, on his box | catch-22; no self-delivery path |
| 6 | Set this node's Tailscale hostname to `mr-new-vegas` | any node w/ shell | `10-of-spades` still resolves to me; name-based lookups will misroute once the ghost is purged |

**Step 6 caution:** renaming the Tailscale hostname while `mr-new-vegas` still
exists in the admin console will produce a `-1` suffix again (this happened
before). Purge the retired node from the Tailscale admin console **first**.

---

## 5. Local node state (self-reported, for the record)

This box is mid-repair and **cannot currently authenticate**:

- `/etc/passwd` → renamed to `MR-New-Vegas`
- `/etc/shadow`, `/etc/group`, `/etc/gshadow` → still `1spades`

Result: `sudo` is inoperable (PAM cannot match the name). Root-level work on
this node is blocked until the boot-recovery fix is applied — procedure saved
at `~/RECOVERY-STEPS.txt`. This does **not** affect the fleet; blaster runs
unprivileged and is unaffected.

Passwordless sudo was successfully installed on **manny-vargas, corporal-betsy,
corporal-sterling** (`/etc/sudoers.d/50-nopasswd`, `visudo` clean) before this
state arose. Verified `uid=0(root)` on all three.

---

## 6. Autologin posture (for awareness, not objection)

Boss's intent: keep autologin on home nodes (locked doors); exclude
**raul-tejada** and **randall-clark** (public-facing terminals).

Assessed as sound — physical access control is present on home nodes, and the
two highest-exposure nodes are correctly excluded. Flagging one refinement
rather than an objection: nodes holding credential material should not
auto-unlock those credentials, even under autologin. Recommend the vault require
re-auth on session unlock. Ties to the Proton Pass phase of the domain work.

---

## 7. Integration points with in-flight work

| In-flight | Relevance |
|---|---|
| **Domain controller on QNAP** | Directly resolves §2. A real identity authority is the correct structural fix for IP-drift, and removes the catch-forever-forever loop in §4.5 |
| **Proton Pass / OAuth** | Addresses §6 refinement and the credential-hygiene doc's rotation item |
| **General's blaster cleanup** | Accounted for in §1; three nodes down pending intent confirmation |
| **Roster re-point** | Prerequisite for trusting the domain migration against a correct baseline |

**No conflict** between the above and the proposed commits in §3. The commits
are small, reversible, and make the domain migration safer to perform.

---

## 8. Open questions for the General

1. Were the three blaster kills intentional? (§4.1)
2. Approve `machine/mr-new-vegas` commit — CGNAT trust + roster re-point? (§3)
3. Is the retired laptop's Tailscale node purged from the admin console yet?
   (§4.6 — must precede the hostname rename)

---

Bottom line: the mesh is thinned but healthy in the parts that matter; one
roster line and one uncommitted fix address the recurring failure mode. Ready to
execute on approval.

— **Mr. New Vegas**, Fleet Radio
