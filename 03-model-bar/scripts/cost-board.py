#!/usr/bin/env python3
"""
cost-board.py — Fleet model cost board + top-N cheapest recommendation.

Polls the (researched) model cost board and recommends the cheapest models.
Zen bills per 1M tokens (USD). Some models (DeepSeek V4) have PEAK/OFF-PEAK
rates that change through the day — this tool applies the rate for the current
period.

Costs are read from COSTS below (sourced from opencode.ai/zen + docs.z.ai,
2026-09). Refresh by editing COSTS or by pointing COST_URL at a live board.

Usage:
  python3 cost-board.py              # show board + top-3 cheapest
  python3 cost-board.py --top 5      # top 5 cheapest
  python3 cost-board.py --blend 0.7  # blend input:output share for the effective rate
"""
import argparse, datetime, sys

# $ per 1M tokens, model -> (input, output, cached). PEAK/OFF-PEAK variants use
# a dict {"peak": (in,out), "offpeak": (in,out)} where applicable.
COSTS = {
  "gpt-5-nano":            {"peak": (0.05, 0.40),  "offpeak": (0.05, 0.40)},
  "deepseek-v4-flash":     {"peak": (0.44, 1.32),  "offpeak": (0.22, 0.66)},
  "deepseek-v4-flash-low": (0.14, 0.28),   # legacy simple rate
  "gpt-5.6-luna":          {"peak": (0.20, 1.20),  "offpeak": (0.20, 1.20)},
  "qwen3.5-plus":          (0.20, 1.20),
  "deepseek-v4-pro":       {"peak": (1.32, 3.96),  "offpeak": (0.66, 1.98)},
  "qwen3.6-plus":          (0.50, 3.00),
  "minimax-m3":            (0.30, 1.20),
  "gemini-3.5-flash-lite": (0.30, 2.50),
  "kimi-k2.5":             (0.60, 3.00),
  "glm-5":                 (1.00, 3.20),
  "glm-5.2":               (1.40, 4.40),
  "claude-haiku-4.5":      (1.00, 5.00),
  "qwen3.7-plus":          (0.40, 1.60),
}

# DeepSeek peak window (times vary; set to your region's peak hours, 24h). Default:
# off-peak at night/weekend, peak otherwise. Tune PEAK_HOURS to match the provider.
PEAK_HOURS = range(8, 23)   # 08:00-22:59 = peak, 23:00-07:59 = off-peak


def rate(model):
    v = COSTS[model]
    return v if isinstance(v, dict) else {"peak": v, "offpeak": v}


def current_rates():
    now = datetime.datetime.now()
    peak = now.hour in PEAK_HOURS and now.weekday() < 5
    return peak


def blended(r, in_share=0.5):
    return r[0] * in_share + r[1] * (1 - in_share)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--blend", type=float, default=0.5, help="input share of effective cost (0-1)")
    args = ap.parse_args()
    if not (0 <= args.blend <= 1):
        print("--blend must be 0..1", file=sys.stderr); return 1

    now = datetime.datetime.now()
    peak = current_rates()
    print(f"Fleet model cost board ({now:%Y-%m-%d %H:%M} — {'PEAK' if peak else 'OFF-PEAK'})")
    print(f"{'model':<20} {'$in/1M':>8} {'$out/1M':>8} {'$eff/1M':>8}   note")
    print("-" * 64)
    eff = {}
    for m, spec in COSTS.items():
        r = rate(m)
        rates = r["peak"] if peak else r["offpeak"]
        e = blended(rates, args.blend)
        eff[m] = (e, rates)
        note = ""
        if r["peak"] != r["offpeak"]:
            note = "peak/off-peak varies"
        print(f"{m:<20} {rates[0]:>8.2f} {rates[1]:>8.2f} {e:>8.2f}   {note}")

    print("\nTop %d cheapest (blend input=%0.0f%%):" % (args.top, args.blend * 100))
    for i, (m, (e, _)) in enumerate(sorted(eff.items(), key=lambda kv: kv[1][0])[:args.top], 1):
        print(f"  {i}. {m}  ${e:.2f}/1M")
    return 0


if __name__ == "__main__":
    sys.exit(main())