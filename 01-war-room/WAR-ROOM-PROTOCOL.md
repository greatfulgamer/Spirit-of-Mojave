# War Room Protocol — GX-9000 Fleet

**Authority:** Fleet Commander (Paul) · **Orchestrator:** Raul Tejada (raul-tejada:100.127.121.103)
**Established:** 2026-08-30 · **Updated:** 2026-08-31 to include Commander Inbox

## 1. Purpose

War Room is the fleet's council for safety-critical decisions. 3 differing models discuss, 1 validates (witness), all is recorded. No fleet-wide change without War Room review.

## 2. Membership (per MODEL-BAR doctrine)

- **3 discussants:** Different models on separate GPUs/ports (e.g., `qwen3.5:4b` on Raul P4, `lfm2.5:8b` on Boone 680M, `qwen3:1.7b` on Randall 4050)
- **1 witness:** `tools/bouncer.py` + `fleet/state/bouncer.log` + `readers-*.json` — proves 3 distinct models discussed and records provenance (model+GPU+port+timestamp)
- **Author:** Raul — writes minutes

## 3. Procedure (build mode)

1. **Evidence:** Orchestrator writes `evidence.json` (6 items, identical to all readers) — identical prompt to all.
2. **Deliberation:** Each reader reviews evidence, returns JSON `{"verdicts": {"E1": "AGREE|DISAGREE", ...}, "priority_action": "...", "risk1": "...", "risk2": "..."}`. Witness captures `model+GPU+port+elapsed+timestamp` to `readers-YYYY-MM-DD.json`.
3. **Minutes:** Raul authors `WAR-ROOM-MINUTES-YYYY-MM-DD.md` (filed by Raul, distributed to mempalaces via `mempalace mine` + git).
4. **Commander Inbox (new, 2026-08-31):** **Every War Room output is copied to `~/Documents/Commander Inbox/` on Raul** for commander to read. Includes:
   - `WAR-ROOM-MINUTES-*.md` (handout)
   - `WAR-ROOM-DOCKET-*.md` (queue)
   - `FLEET-HARDWARE-CHART.md` (current ledger)
   Future model bar benchmarks and War Room finds will also be tossed there automatically.
5. **Distribution (until federated memory ready):** Each participant keeps a local copy via `git pull` (main) + local `mempalace mine --wing war-room`. This is the best bet to not forget things.
6. **Commander read:** Commander reads inbox file end-to-end, takes actions based on findings.

## 4. Distribution hook (automated)

`tools/war-room-distribute.sh` is the protocol enforcer:

```bash
bash tools/war-room-distribute.sh  # copies latest WAR-ROOM-MINUTES + DOCKET + FLEET-HARDWARE-CHART to Commander Inbox and mines to mempalace
```

Run this after every War Room. Future automation will hook it to `git push` post-merge.

## 5. Recording

- Docket: `projects/war-room/WAR-ROOM-DOCKET-YYYY-MM-DD.md` (queue, evidence, asks)
- Readers: `projects/war-room/readers-YYYY-MM-DD.json` (raw verdicts + provenance)
- Minutes: `projects/war-room/WAR-ROOM-MINUTES-YYYY-MM-DD.md` (Raul's handout)
- Inbox: `~/Documents/Commander Inbox/` (commander-facing copies)

All are committed to `main` and mined to `war-room` wing.

## 6. Relation to other doctrines

- Model-Bar reviews model health (are brains fit?) — War Room reviews fleet decisions (are actions safe?)
- Hub-and-spoke: War Room is the orchestrator's council, not a P2P mesh.
- Solo focus (remainder of month): Only Raul + commander, no terminals contending — War Room runs with Boone+Randall as remote readers via blaster, Mr/General offline.

*Non Impediti Ratione Cogitationis.*
