# Eval changelog

One entry per change to the agent, with the eval score after it. Dataset: Olist
(`DATASET=olist`), 40 questions in `evals/gold.yaml`.

| # | Change | Model | Overall | Easy | Medium | Hard | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Baseline, no fixes | qwen2.5-coder:7b | 14/40 (35%) | 10/12 | 3/16 | 1/12 | 4 gave up, 43.2s avg, 0.35 repairs avg |

## 0. Gold set created

40 questions (12 easy, 16 medium, 12 hard), each with hand-written gold SQL.
Starts with the 8 questions tested by hand, then adds 32 more that target the
same traps: customer_unique_id vs customer_id, orders vs payment rows, revenue
definition, late delivery, group comparisons, date math, and join fan-out.
Business definitions the gold SQL follows are listed at the top of
`gold.yaml`. Every gold query was checked to run, pass the SQL validator, and
have no ties at its top-N cutoff.

## 1. Baseline: 14/40 (35%)

`qwen2.5-coder:7b` via Ollama, agent exactly as built in Phase 1. Results
frozen in `results/baseline/2026-10-02_145705_ollama-qwen2.5-coder-7b/`.

Every one of the 26 failures was checked by hand against the gold result;
none is a scorer formatting issue. Causes:

| Cause | Count | Questions |
|---|---|---|
| Business definition wrong (customer, revenue, order counts, category names) | 18 | e03 e08 m01 m02 m03 m05 m07 m08 m09 m11 m12 m13 m14 m15 h06 h08 h10 h11 |
| Gave up: wrong table for a column, all 3 repairs returned the same SQL | 4 | m06 h01 h04 h12 |
| Comparison answered with raw rows instead of group averages | 2 | h02 h07 |
| Window / date logic | 2 | h05 h09 |

Notable patterns:
- Revenue was computed as `price * freight_value` in 5 of the 6 revenue
  questions that returned results (m03 m05 m13 h08 h11); the sixth (m08) used
  `price + freight_value`. One definition should fix all six.
- Accuracy by trap: customer_unique_id 0/6, revenue 0/8, fanout 0/5,
  comparison 0/6, payment_rows 0/2.
- The 4 give-ups cost 609s of the 1,728s total run time, with zero benefit
  from repairs.
- Two failures are definition calls rather than plain errors: m08 included
  freight in order value, m14 counted one late order that is not in
  `delivered` status (7,827 vs 7,826). Both are wrong under the stated
  definitions, which is what the semantic layer will make explicit.
