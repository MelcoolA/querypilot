## Eval summary: anthropic:claude-sonnet-5-5 on olist, 2026-10-02 18:18

| Metric | Value |
|---|---|
| Accuracy (overall) | 35/40 (88%) |
| Accuracy (easy) | 12/12 (100%) |
| Accuracy (medium) | 14/16 (88%) |
| Accuracy (hard) | 9/12 (75%) |
| Agent gave up / crashed | 0 |
| Avg latency | 3.9s |
| Avg tokens (in / out) | 3662 / 316 |
| Avg cost per question | $0.0105 |
| Repairs (total / avg) | 0 / 0.00 |
| Questions needing a repair | 0 |

| Trap | Accuracy |
|---|---|
| comparison | 5/6 (83%) |
| customer_unique_id | 6/6 (100%) |
| date_math | 5/9 (56%) |
| fanout | 4/5 (80%) |
| late_delivery | 4/4 (100%) |
| payment_rows | 2/2 (100%) |
| revenue | 4/8 (50%) |

| Id | Result | Repairs | Latency | Reason |
|---|---|---|---|---|
| e01 | correct | 0 | 3.6s | match |
| e02 | correct | 0 | 3.1s | match |
| e03 | correct | 0 | 2.4s | match |
| e04 | correct | 0 | 3.2s | match |
| e05 | correct | 0 | 2.5s | match |
| e06 | correct | 0 | 3.4s | match |
| e07 | correct | 0 | 2.8s | match |
| e08 | correct | 0 | 3.2s | match |
| e09 | correct | 0 | 3.2s | match |
| e10 | correct | 0 | 3.3s | match |
| e11 | correct | 0 | 3.5s | match |
| e12 | correct | 0 | 2.6s | match |
| m01 | correct | 0 | 3.8s | match |
| m02 | correct | 0 | 3.6s | match |
| m03 | correct | 0 | 3.0s | match |
| m04 | correct | 0 | 3.7s | match |
| m05 | wrong | 0 | 4.5s | no agent column matches gold column 2 (values differ) |
| m06 | correct | 0 | 4.6s | match |
| m07 | correct | 0 | 3.0s | match |
| m08 | wrong | 0 | 3.9s | no agent column matches gold column 1 (values differ) |
| m09 | correct | 0 | 3.7s | match |
| m10 | correct | 0 | 2.2s | match |
| m11 | correct | 0 | 3.8s | match |
| m12 | correct | 0 | 3.7s | match |
| m13 | correct | 0 | 4.1s | match |
| m14 | correct | 0 | 3.2s | match |
| m15 | correct | 0 | 4.7s | match |
| m16 | correct | 0 | 5.0s | match |
| h01 | correct | 0 | 4.5s | match |
| h02 | correct | 0 | 4.9s | match |
| h03 | correct | 0 | 3.0s | match |
| h04 | correct | 0 | 4.4s | match |
| h05 | wrong | 0 | 5.1s | no agent column matches gold column 3 (values differ) |
| h06 | correct | 0 | 4.4s | match |
| h07 | correct | 0 | 5.6s | match |
| h08 | wrong | 0 | 5.2s | no agent column matches gold column 2 (values differ) |
| h09 | correct | 0 | 5.4s | match |
| h10 | correct | 0 | 5.0s | match |
| h11 | wrong | 0 | 5.6s | no agent column matches gold column 1 (values differ) |
| h12 | correct | 0 | 4.4s | match |
