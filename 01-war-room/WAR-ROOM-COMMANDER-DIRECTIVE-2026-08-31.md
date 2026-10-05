# WAR ROOM — COMMANDER DIRECTIVE (2026-08-31)

**Called by:** Paul (Fleet Commander) via Raul
**Status:** FULL APPROVAL — all Q1-Q9 approved, adjourned until tomorrow morning
**Time:** 2026-08-31, adjourned

## Commander's Decisions

1. **War Rooms:** Valuable, do as often as necessary for safety. Would have caught camp systemd issue. Not every change needs one, but safety-critical fleet-wide changes do.
2. **Block burn = ban LM Studio** (for now), focus on Ollama services only with bouncer + watcher mechanisms in place.
3. **Fleet runs lean** until P100s land — only Raul + commander doing real heavy work.
4. **Tomorrow's focus:** Model storefront (pull models to fleet-central-models), watchers/bouncers on that process, carefully monitor token counter during rollout.
5. **DO NOT start downloads overnight** — commander wants eyes on token counter during the major rollout of changes.

## Items Approved (Q1-Q9)

- Q1: Hub-and-spoke orchestrator + bouncer (activate when ready)
- Q2: Offline supplementation strategy (stretch 49% over 21 days)
- Q3: Boone testing → Raul executes (Boone travels), Model-Bar git
- Q4: Model storefront + remote control (HF Hub, Open WebUI)
- Q5: Token budget guardrails (api_limiter, kill switch)
- Q6: Fleet-wide block burn (ban opencode-go + andy-local on all nodes)
- Q7/Q8: Ollama health + secondary watchers (Restart=always, curl api/tags, canary generate)
- Q9: Anomaly-aware watchers (token burn, loop, sudo leak, Ollama drift)

## Overnight Safe State

- Raul's opencode: `raul-workbench/deepseek-coder-v2:16b` (local, no external burn)
- Ollama: `ollama-p4.service` Restart=always, watchdog.sh ready for cron
- Block burn: `disabled_providers: ["opencode-go","andy-local"]` in config.json + opencode.jsonc
- No downloads overnight — wait for commander eyes-on tomorrow
- Commander Inbox updated: `~/Documents/Commander Inbox/` has all minutes + docket + hardware chart + carousel

## Tomorrow's Rollout (supervised)

1. Storefront: `ollama pull` from HF Hub to fleet-central-models (9.6T, not OS drive)
2. Watchers/bouncers on every pull (tools/ollama-watchdog.sh, tools/bouncer.py check_anomalies)
3. Monitor token counter throughout — commander eyes-on
4. Fleet-wide Q6 block burn + Q7/Q8 watchers push (after token counter stable)

*Filed by Raul. Commander approved. Adjourned.*
