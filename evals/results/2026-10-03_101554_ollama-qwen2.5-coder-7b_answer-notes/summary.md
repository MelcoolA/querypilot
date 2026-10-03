## Eval summary: ollama:qwen2.5-coder:7b on olist (duckdb), 2026-10-03 10:45

| Metric | Value |
|---|---|
| Accuracy (overall) | 30/40 (75%) |
| Accuracy (easy) | 12/12 (100%) |
| Accuracy (medium) | 13/16 (81%) |
| Accuracy (hard) | 5/12 (42%) |
| Agent gave up / crashed | 3 |
| Avg latency | 44.6s |
| Avg tokens (in / out) | 6199 / 143 |
| Avg cost per question | $0.0000 |
| Repairs (total / avg) | 7 / 0.17 |
| Questions needing a repair | 5 |

| Trap | Accuracy |
|---|---|
| comparison | 2/6 (33%) |
| customer_unique_id | 3/6 (50%) |
| date_math | 5/9 (56%) |
| fanout | 4/5 (80%) |
| late_delivery | 3/4 (75%) |
| payment_rows | 0/2 (0%) |
| revenue | 7/8 (88%) |

| Id | Result | Repairs | Latency | Reason |
|---|---|---|---|---|
| e01 | correct | 0 | 13.1s | match |
| e02 | correct | 0 | 9.6s | match |
| e03 | correct | 0 | 12.1s | match |
| e04 | correct | 0 | 10.6s | match |
| e05 | correct | 0 | 10.2s | match |
| e06 | correct | 0 | 28.8s | match |
| e07 | correct | 0 | 11.8s | match |
| e08 | correct | 0 | 13.3s | match |
| e09 | correct | 0 | 18.7s | match |
| e10 | correct | 0 | 22.1s | match |
| e11 | correct | 0 | 23.3s | match |
| e12 | correct | 0 | 14.5s | match |
| m01 | wrong | 0 | 27.8s | no agent column matches gold column 2 (values differ) |
| m02 | correct | 0 | 35.7s | match |
| m03 | correct | 0 | 47.8s | match |
| m04 | correct | 0 | 23.1s | match |
| m05 | correct | 0 | 44.3s | match |
| m06 | correct | 0 | 183.4s | match |
| m07 | correct | 0 | 28.0s | match |
| m08 | correct | 0 | 24.4s | match |
| m09 | correct | 0 | 43.9s | match |
| m10 | correct | 0 | 15.8s | match |
| m11 | wrong | 1 | 51.4s | row count 1000, expected 1 |
| m12 | correct | 0 | 51.3s | match |
| m13 | correct | 0 | 52.4s | match |
| m14 | correct | 0 | 13.9s | match |
| m15 | wrong | 0 | 20.1s | row count 5, expected 2 |
| m16 | correct | 0 | 39.0s | match |
| h01 | error | 1 | 54.7s | agent gave up: BinderException: Binder Error: Table "o" does not have a column named "sell |
| h02 | wrong | 0 | 46.1s | row count 1, expected 2 |
| h03 | correct | 0 | 22.4s | match |
| h04 | correct | 0 | 86.9s | match |
| h05 | wrong | 0 | 67.8s | no agent column matches gold column 3 (values differ) |
| h06 | error | 2 | 69.8s | agent gave up: BinderException: Binder Error: Referenced column "customer_unique_id" not f |
| h07 | correct | 1 | 118.2s | match |
| h08 | correct | 0 | 116.8s | match |
| h09 | error | 2 | 129.2s | agent gave up: BinderException: Binder Error: Referenced column "customer_unique_id" not f |
| h10 | wrong | 0 | 82.2s | no agent column matches gold column 1 (values differ) |
| h11 | wrong | 0 | 47.6s | no agent column matches gold column 1 (values differ) |
| h12 | correct | 0 | 51.8s | match |
