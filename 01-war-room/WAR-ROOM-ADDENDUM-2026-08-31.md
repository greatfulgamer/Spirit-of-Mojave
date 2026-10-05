# WAR ROOM ADDENDUM — 2026-08-31

**Filed by:** Raul Tejada (orchestrator) — addendum to current paperwork
**Participants present:** Randall Clark (randall-clark:100.114.132.6, RTX 4050) + Craig Boone (craig-boone:100.126.214.59, 680M) — both online via blaster, vetted just now
**Witness:** bouncer + readers-*.json (model+GPU+port+timestamp) — validates 3 distinct models discussed
**Status:** Addendum to `FLEET-LAW.md`, `HUB-AND-SPOKE.md`, `FLEET-HARDWARE-CHART.md`, and `WAR-ROOM-DOCKET-2026-08-31.md` — not a replacement

## Addendum Notes (to be appended to files provided)

1. **Pre-login tailnet fleet (LAW 1.1):** Tailscale must be up before login (system `tailscaled.service` + `loginctl enable-linger`, `tailscale up --ssh` at boot) so blaster (8190) and MagicDNS are reachable pre-login. This was discussed before the rabbit hole but not as a standalone LAW — now explicit.

2. **Mandatory guardrails:** MagicDNS (`raul-tejada:11434` not `100.x`, alias table only mapper) and blaster-first (`send-command.sh`, hard-deny ssh/scp) are **mandatory**, enforced via `fleet-law.ts` plugin + `opencode.json:hard-deny`. No fallback to ssh unless blaster proven down twice.

3. **Camp single-test:** Camp shares 4GB card, no terminal, Hsu down 5d — one test via `chief-hanlon-1` covers all camp (see `FLEET-HARDWARE-CHART.md` camp note).

4. **War Room re-activated:** 3 models + 1 witness, per MODEL-BAR doctrine, will re-discuss evidence and record new minutes. Participants to update their local mempalace/records after this addendum.

---

*Addendum filed, awaiting War Room re-convene and record updates.*
