# Eval changelog

One entry per change to the agent, with the eval score after it. Dataset: Olist
(`DATASET=olist`), 40 questions in `evals/gold.yaml`.

| # | Change | Model | Overall | Easy | Medium | Hard | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Baseline, no fixes | qwen2.5-coder:7b | 14/40 (35%) | 10/12 | 3/16 | 1/12 | 4 gave up, 43.2s avg, 0.35 repairs avg |
| 2 | Semantic layer (`semantic/olist.yaml`) | qwen2.5-coder:7b | **29/40 (72%)** | 12/12 | 12/16 | 5/12 | 1 gave up, 40.1s avg, 0.17 repairs avg |
| 3 | Repair loop: attempt history, stop on repeat (h12 reworded) | qwen2.5-coder:7b | 30/40 (75%) | 12/12 | 12/16 | 6/12 | +1 is from rewording h12, not the fix; 2 gave up, 40.9s avg |
| 4 | Comparison rule in write_sql; summarize warns on row limit | qwen2.5-coder:7b | 29/40 (72%) | 12/12 | 11/16 | 6/12 | -1 is within noise (see entry); answers clearly better; 4 gave up |

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

## 2. Semantic layer: 29/40 (72%), up from 14/40

`semantic/olist.yaml` adds business definitions (customer, order count,
revenue, items per order, order date, delivered order, delivery metrics,
late delivery, percentage), join paths, where each column lives, per-column
notes, and the real distinct values of `order_status`, `payment_type`, and
`product_category` read from the data. `get_schema` puts this above the table
list. Results: `results/2026-10-02_155842_ollama-qwen2.5-coder-7b_fix1-semantic/`.

| Trap | Baseline | Semantic layer |
|---|---|---|
| revenue | 0/8 | 6/8 |
| customer_unique_id | 0/6 | 4/6 |
| date_math | 3/9 | 7/9 |
| late_delivery | 1/4 | 3/4 |
| comparison | 0/6 | 2/6 |
| fanout | 0/5 | 2/5 |
| payment_rows | 0/2 | 0/2 |

What changed:
- 15 questions fixed, none of the baseline passes lost. Give-ups dropped from
  4 to 1: three were the agent reading a column from the wrong table, which
  the column locations now prevent.
- Still failing (11): m01 m15 (payment rows, despite the definition), m08
  (average of item prices, not order totals), m11 (grouped but never counted
  the groups), h01 (nonsense join, then a summary claiming no data exists),
  h02 h07 (no comparison group), h05 (filtered before LAG), h06 (wrong
  formula), h10 (gave up, same SQL 3 times), h12 (see below).

Three problems found and fixed while running this step:
1. **Ollama silently truncated the prompt.** Its default context is 4,096
   tokens; the new prompt is 4,140, so Ollama dropped about half of it,
   including the definitions, with no error. Fixed by setting `num_ctx`
   (`OLLAMA_NUM_CTX=16384` in `.env`). The baseline prompt (2,776 tokens) fit,
   so the baseline is unaffected. The first run was stopped and discarded.
2. **My "delivered order" definition was too strict.** It required a delivery
   date, so the agent followed it literally and answered 96,470 instead of
   96,478 for e01. Split into "delivered order" (status only) and "delivery
   metrics" (status plus a delivery date). No gold SQL changed.
3. **Scorer bug.** m05 returned years as `2016-01-01` instead of `2016`;
   correct, but scored wrong. The scorer now also matches January 1st dates
   to plain years. Both runs were re-scored with `python -m evals.rescore`:
   the baseline is unchanged at 14/40, this run went from 28 to 29.

Open question: h12 ("top 10% of sellers") returned 67.49% vs gold 67.56%.
The agent took the top 309 of 3,095 sellers, the gold query (NTILE) the top
310. Both are reasonable readings of "top 10%"; kept as wrong for now.

## 3. Repair loop: 30/40 (75%), but the fix itself added 0

Changes:
- Repair prompts list every failed attempt with its error, not just the last
  one, and say not to repeat any of them.
- If a repair returns SQL it already tried (compared after normalizing
  spacing, keyword and identifier case, and the added LIMIT; string literals
  keep their case), the agent stops at once and says why.
- Same step: h12 reworded from "top 10% of sellers" (two valid readings,
  309 or 310 sellers) to "top 100 sellers" (one reading, no tie at rank 100).

Results: `results/2026-10-02_163504_ollama-qwen2.5-coder-7b_fix2-repair/`.

Honest attribution: the only new pass is h12, and the fix 1 code also passes
the reworded h12 (checked by running it on commit b611b6d). So the rewording
earned the point, and the repair-loop fix changed the score by 0. Measured
on the same questions, fix 1 would be 30/40 too.

What the fix did change:
- **h01: misleading answer -> honest give-up.** In fix 1 the repair produced
  a nonsense join, got 0 rows, and the summary claimed "There are no delivery
  times available in the data." Now the repair repeats the first query, the
  loop stops, and the agent says it could not answer. Same score, much safer
  for a business user.
- **h10: 109s -> 58s.** Stopped after 1 identical repair instead of 3.
- Total run time did not drop (1,603s vs 1,636s): the savings on h10 were
  offset by longer repair prompts elsewhere (h06, h12).
- Every early stop happened on the first repair: even with its history in
  front of it, the 7B model repeated its first query rather than trying a
  new approach. The failures left (h01 reads seller_id from orders, h10 reads
  product_id from order_reviews) need a different join path, which it did
  not find on its own.

Takeaway: the repair loop is now cheaper and more honest, but repairs are
not where qwen2.5-coder:7b's accuracy is lost. The remaining failures are
wrong logic in SQL that runs without errors, which no repair ever sees.

## 4. Summarize step and comparison rule: 29/40 (72%), answers better

Changes:
- write_sql prompt: comparison questions return one row per group with the
  aggregate, covering every compared group and only those; single-number
  questions return one row.
- summarize prompt: a LIMIT only caps returned rows (aggregates still cover
  all data); if the result hit the row limit, say it is partial; only compare
  groups present in the result; an empty result means "no rows matched", not
  "the data does not exist".
- When a result hits the 1,000-row limit, code (not the LLM) appends a fixed
  note to the answer, so the user always learns it is partial.
- Give-up message wording ("1 repair attempt").

Results: `results/2026-10-02_170932_ollama-qwen2.5-coder-7b_fix3-summarize/`.

Score changes vs fix 2: h07 fixed (the comparison rule: one row per group
instead of 1,000 raw orders); m07 lost (back to AVG(order_item_id), despite
the semantic layer saying it is not a quantity); h12 lost (nearly the same
SQL as fix 2, which only passed after 2 repairs; this time the first repair
repeated itself). h06 went from wrong to gave up.

**Noise finding.** This small prompt change altered the first SQL on 9 of 40
questions, including questions it has nothing to do with. With a 7B model at
temperature 0, any prompt edit shifts several answers in both directions, so
a change of 1 question between runs is not meaningful at n=40. The real
signal so far is 14 -> about 30; differences among fixes 1 to 3 (29, 30, 29)
are within noise.

Answer quality (the main goal of this fix, not measured by the scorer):
- e02: no longer claims the average covers "the first 1000 rows".
- h02: now compares late (2.57) and on-time (4.21) reviews and reaches the
  right conclusion. Baseline said the opposite of the truth. Still scored
  wrong: "on time" includes canceled/undelivered orders (gold 4.29).
- m11: the answer now says the result is partial and carries the cut-off
  note, but still repeats the meaningless "1,000 customers" (true answer 2,997).
- m03: amounts still shown with "$" for Brazilian reais; the currency is only
  a comment in the semantic file and never reaches the prompt.

Known scorer limitation: h02 returned one wide row (late_avg, on_time_avg)
where gold has one row per group. Both shapes are valid answers; the scorer
only accepts the second. It did not change this run's score (the values were
also wrong), but it could in a future run.

Latency fell from 40.9s to 23.0s average, but prompts got slightly longer
and output barely changed, so this is almost certainly lower load on the
laptop, not the fix. Latency comparisons between local runs are unreliable.
