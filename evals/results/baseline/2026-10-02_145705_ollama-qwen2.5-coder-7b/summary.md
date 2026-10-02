## Eval summary: ollama:qwen2.5-coder:7b on olist, 2026-10-02 15:25

| Metric | Value |
|---|---|
| Accuracy (overall) | 14/40 (35%) |
| Accuracy (easy) | 10/12 (83%) |
| Accuracy (medium) | 3/16 (19%) |
| Accuracy (hard) | 1/12 (8%) |
| Agent gave up / crashed | 4 |
| Avg latency | 43.2s |
| Avg tokens (in / out) | 4117 / 175 |
| Avg cost per question | $0.0000 |
| Repairs (total / avg) | 14 / 0.35 |
| Questions needing a repair | 5 |

| Trap | Accuracy |
|---|---|
| comparison | 0/6 (0%) |
| customer_unique_id | 0/6 (0%) |
| date_math | 3/9 (33%) |
| fanout | 0/5 (0%) |
| late_delivery | 1/4 (25%) |
| payment_rows | 0/2 (0%) |
| revenue | 0/8 (0%) |

| Id | Result | Repairs | Latency | Reason |
|---|---|---|---|---|
| e01 | correct | 0 | 13.5s | match |
| e02 | correct | 0 | 12.5s | match |
| e03 | wrong | 0 | 12.2s | no agent column matches gold column 1 (values differ) |
| e04 | correct | 0 | 12.0s | match |
| e05 | correct | 0 | 11.2s | match |
| e06 | correct | 0 | 24.3s | match |
| e07 | correct | 0 | 13.3s | match |
| e08 | wrong | 0 | 15.0s | no agent column matches gold column 1 (values differ) |
| e09 | correct | 0 | 19.1s | match |
| e10 | correct | 0 | 17.8s | match |
| e11 | correct | 0 | 18.1s | match |
| e12 | correct | 0 | 15.9s | match |
| m01 | wrong | 0 | 17.9s | no agent column matches gold column 2 (values differ) |
| m02 | wrong | 0 | 26.8s | no agent column matches gold column 2 (values differ) |
| m03 | wrong | 0 | 49.9s | no agent column matches gold column 1 (values differ) |
| m04 | correct | 0 | 19.8s | match |
| m05 | wrong | 0 | 38.2s | no agent column matches gold column 2 (values differ) |
| m06 | error | 3 | 96.8s | agent gave up: BinderException: Binder Error: Table "o" does not have a column named "sell |
| m07 | wrong | 0 | 16.2s | no agent column matches gold column 1 (values differ) |
| m08 | wrong | 0 | 19.4s | no agent column matches gold column 1 (values differ) |
| m09 | wrong | 0 | 30.4s | no agent column matches gold column 2 (values differ) |
| m10 | correct | 0 | 15.7s | match |
| m11 | wrong | 0 | 11.0s | row count 0, expected 1 |
| m12 | wrong | 0 | 28.4s | no agent column matches gold column 2 (values differ) |
| m13 | wrong | 0 | 45.4s | no agent column matches gold column 2 (values differ) |
| m14 | wrong | 0 | 17.4s | no agent column matches gold column 1 (values differ) |
| m15 | wrong | 0 | 20.3s | row count 5, expected 2 |
| m16 | correct | 0 | 27.2s | match |
| h01 | error | 3 | 61.6s | agent gave up: BinderException: Binder Error: Table "o" does not have a column named "cust |
| h02 | wrong | 0 | 24.9s | row count 1000, expected 2 |
| h03 | correct | 0 | 22.0s | match |
| h04 | error | 3 | 224.4s | agent gave up: BinderException: Binder Error: Table "o" does not have a column named "cust |
| h05 | wrong | 0 | 67.8s | no agent column matches gold column 2 (values differ) |
| h06 | wrong | 0 | 28.1s | no agent column matches gold column 1 (values differ) |
| h07 | wrong | 0 | 70.7s | row count 1000, expected 2 |
| h08 | wrong | 0 | 98.8s | no agent column matches gold column 1 (values differ) |
| h09 | wrong | 2 | 91.0s | no agent column matches gold column 1 (values differ) |
| h10 | wrong | 0 | 74.8s | no agent column matches gold column 1 (values differ) |
| h11 | wrong | 0 | 72.7s | no agent column matches gold column 1 (values differ) |
| h12 | error | 3 | 225.8s | agent gave up: BinderException: Binder Error: Referenced table "s" not found! |
