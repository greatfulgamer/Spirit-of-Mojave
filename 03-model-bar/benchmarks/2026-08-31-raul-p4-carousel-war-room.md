# Model-Bar — 2026-08-31 Raul P4 Carousel (War Room Test)

## Test Context
- **Hardware:** Tesla P4 8GB (CUDA), 127.0.0.1:11434
- **Evidence:** WR-2026-08-31-AGGRESSIVE (E1-E7, fleet enforcement proposals)
- **Prompt:** War Room review (300 words max, JSON verdicts per evidence item)
- **Token status:** 51% left, 21 days remaining — this carousel validates which models can actually function for fleet work

## Results

| Model | Size | Family | Response | Verdict | Notes |
|-------|------|--------|----------|---------|-------|
| llama3.2:3b | 3.2B | Meta/LLaMA | Substantive (12.6s) | E1 AGREE, E2 DISAGREE, E3 AGREE, E4 AGREE, E5 DISAGREE, E6 AGREE, E7 AGREE | Works well on P4, good for War Room text |
| moondream:latest | 1B | Phi2/Vision | Brief (2.6s) | E1 AGREE, E7 AGREE | Vision model, not text specialist — wrong tool for War Room |
| deepseek-coder-v2:16b | 15.7B | DeepSeek/Coder | TIMEOUT 60s, JSON error | N/A | Too heavy for single P4 8GB load — fails under weight |

## Key Findings (many models can't function effectively)

1. **3B is the practical ceiling for War Room on P4** — llama3.2:3b was the only model that gave structured, multi-item verdicts
2. **Vision models don't do War Room** — moondream is for image analysis, not text reasoning
3. **16B is too heavy for P4 alone** — deepseek-coder-v2:16b needs multi-GPU (P100 cluster) to load and reason
4. **Thinking-mode models (qwen3/qwen3.5) eat all tokens thinking before responding** — can't be disabled via options, `num_predict` consumed by reasoning chain before answer arrives
5. **Carousel validates the fleet chart testing protocol** — we need to know what works where before fleet-wide deployment
6. **This is why we need the P100s** — 4×P100 = 80GB unlocks qwen3.5:9b/35b-a3b and larger reasoning models for War Room

## Carousel Pattern (standard until P100s land)
- Cycle 3 distinct model families on P4, record responses per model+GPU+port+elapsed
- Distribute to Commander Inbox per War Room Protocol
- Re-run with P100 cluster when available

## Failed models (cannot function for fleet work)
- **Thinking-mode (qwen3, qwen3.5):** can't disable thinking, tokens consumed before response
- **Vision-only (moondream):** too brief for text reasoning
- **16B+ single-GPU:** too heavy for P4 alone, needs multi-GPU
- **Very small (<1B):** no multi-turn tool calls (Berkeley BFCL), can't maintain fleet context
