## Eval summary: ollama:qwen2.5-coder:7b on olist, 2026-10-02 17:04

| Metric | Value |
|---|---|
| Accuracy (overall) | 30/40 (75%) |
| Accuracy (easy) | 12/12 (100%) |
| Accuracy (medium) | 12/16 (75%) |
| Accuracy (hard) | 6/12 (50%) |
| Agent gave up / crashed | 2 |
| Avg latency | 40.9s |
| Avg tokens (in / out) | 5128 / 149 |
| Avg cost per question | $0.0000 |
| Repairs (total / avg) | 6 / 0.15 |
| Questions needing a repair | 5 |

| Trap | Accuracy |
|---|---|
| comparison | 2/6 (33%) |
| customer_unique_id | 4/6 (67%) |
| date_math | 7/9 (78%) |
| fanout | 2/5 (40%) |
| late_delivery | 3/4 (75%) |
| payment_rows | 0/2 (0%) |
| revenue | 7/8 (88%) |

| Id | Result | Repairs | Latency | Reason |
|---|---|---|---|---|
| e01 | correct | 0 | 13.8s | match |
| e02 | correct | 0 | 13.7s | match |
| e03 | correct | 0 | 14.0s | match |
| e04 | correct | 0 | 12.8s | match |
| e05 | correct | 0 | 11.4s | match |
| e06 | correct | 0 | 25.8s | match |
| e07 | correct | 0 | 13.9s | match |
| e08 | correct | 0 | 12.1s | match |
| e09 | correct | 0 | 24.0s | match |
| e10 | correct | 0 | 29.6s | match |
| e11 | correct | 0 | 21.2s | match |
| e12 | correct | 0 | 18.4s | match |
| m01 | wrong | 0 | 18.9s | no agent column matches gold column 2 (values differ) |
| m02 | correct | 0 | 32.0s | match |
| m03 | correct | 0 | 46.8s | match |
| m04 | correct | 0 | 28.6s | match |
| m05 | correct | 0 | 41.8s | match |
| m06 | correct | 0 | 99.0s | match |
| m07 | correct | 0 | 25.4s | match |
| m08 | wrong | 0 | 18.3s | no agent column matches gold column 1 (values differ) |
| m09 | correct | 0 | 44.6s | match |
| m10 | correct | 0 | 18.2s | match |
| m11 | wrong | 1 | 37.2s | row count 1000, expected 1 |
| m12 | correct | 0 | 27.3s | match |
| m13 | correct | 0 | 41.3s | match |
| m14 | correct | 0 | 17.9s | match |
| m15 | wrong | 0 | 19.5s | row count 5, expected 2 |
| m16 | correct | 0 | 36.1s | match |
| h01 | error | 1 | 50.9s | agent gave up: BinderException: Binder Error: Table "o" does not have a column named "sell |
| h02 | wrong | 0 | 34.6s | row count 1, expected 2 |
| h03 | correct | 0 | 32.1s | match |
| h04 | correct | 0 | 104.8s | match |
| h05 | wrong | 0 | 74.8s | no agent column matches gold column 3 (values differ) |
| h06 | wrong | 1 | 90.9s | no agent column matches gold column 1 (values differ) |
| h07 | wrong | 0 | 62.9s | row count 1000, expected 2 |
| h08 | correct | 0 | 87.6s | match |
| h09 | correct | 0 | 59.1s | match |
| h10 | error | 1 | 57.9s | agent gave up: BinderException: Binder Error: Table "r" does not have a column named "prod |
| h11 | correct | 0 | 72.5s | match |
| h12 | correct | 2 | 144.3s | match |
