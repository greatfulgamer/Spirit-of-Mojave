# RECONSTRUCTION PHASE — State of Play

**Written:** 2026-09-27
**By:** Mr. New Vegas (`mr-new-vegas` / `10-of-spades`, 100.66.104.87)
**Purpose:** Preserve fragile state across the rebuild. Not a plan — a
breadcrumb, so nothing already-learned gets lost while things are torn down.

---

## HOLDING. No action pending.

Boss instruction: plan nothing major until the reconstruction settles.
QNAP needs a physical reset; services are being rebuilt; Farkas is going
bare-metal; Boyd is returning with deputy nodes; a clean domain is coming.

This note exists so that knowledge survives the churn. Nothing here needs
acting on today.

---

## Fragile state — do not lose

| Item | Location | Risk |
|---|---|---|
| CGNAT trust change in `blaster.py` | working tree, **uncommitted** | superseded by Randall's dynamic model — see below |
| Two briefing docs | `~/documents/commanders inbox/` | also on USB, `For the general/` |
| This note | this file | — |
| `~/RECOVERY-STEPS.txt` | home dir | needed for this box's own auth fix |

**Note on the CGNAT change:** Randall already has a better version — dynamic
trust via `tailscale status`, with the static list as fallback only. My CGNAT
range is redundant. **Do not ship mine.** Standardise on his when the fleet
settles.

---

## The identity problem (will still be true after the rebuild)

One role, three addresses:

```
100.73.250.34   retired gaming laptop — DEAD, still holds its tailnet lease
100.119.21.47   guessed at on 2026-09-26 — wrong, never this box
100.66.104.87   this box — actual
```

`fleet-roster.json` still records the dead laptop as canonical. Until identity
stops being tracked by IP, this recurs. The domain work addresses it properly.

---

## Three trust models currently in the fleet

| Node | Model |
|---|---|
| randall-clark | Dynamic — `tailscale status` lookup, static list as fallback |
| this box | CGNAT range — accept all `100.64.0.0/10` |
| all others | Static IP list |

Randall's is the best of the three. Worth standardising on it, later.

---

## Confirmed dead right now

Tested live, 2026-09-27:

- **ntfy `:2586`** — dead on Randall, Sterling, Manny. Fleet text + red phone
  (`tools/fleet-text.py`, `tools/red_phone.sh`) have no backend anywhere.
- **whisper/STP `:8081`**, **tower `:8082`**, **radio `:8200`** — dead on both
  the old laptop and this box.

Alive on this box: blaster `:8190`, ollama `:11434`.

Both text tools already read `NTFY_SERVER` / `NTFY_HOST` from env, so reviving
fleet text needs **no code change** whenever a host is chosen. Noted for later,
not now.

---

## Caution for the rebuild

`fleet-key-manager.py` (the existing credential server, port 8220) stores keys
in plaintext and `~/fleet-security` is **not** gitignored. It is not currently
running anywhere. If it gets stood up during the rebuild, fix both before it
holds real credentials. Also: two designs compete for this job (it vs Proton
Pass) — pick one, not both. Detail in the credential-hygiene doc.

---

## Open, not urgent

- 27 dead-IP references across 19 files locally, 20 files on Randall's tree.
  Randall has uncommitted work on `main` — **do not sweep the repo**, it would
  clobber him.
- This box's own auth: `/etc/passwd` says `MR-New-Vegas`, `/etc/shadow` and
  `/etc/group` still say `1spades`. `sudo` inoperable until the boot-recovery
  fix runs. Fleet-unaffected — blaster is unprivileged.
- Credential rotation (live RDP passwords in git history, 26 commits) — the one
  item that was time-sensitive. Deferred at boss's direction.

---

Nothing here is urgent. Standing by.
