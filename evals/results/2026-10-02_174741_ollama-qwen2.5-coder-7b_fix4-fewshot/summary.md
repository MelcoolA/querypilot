## Eval summary: ollama:qwen2.5-coder:7b on olist, 2026-10-02 17:59

| Metric | Value |
|---|---|
| Accuracy (overall) | 29/40 (72%) |
| Accuracy (easy) | 12/12 (100%) |
| Accuracy (medium) | 13/16 (81%) |
| Accuracy (hard) | 4/12 (33%) |
| Agent gave up / crashed | 3 |
| Avg latency | 17.6s |
| Avg tokens (in / out) | 5880 / 137 |
| Avg cost per question | $0.0000 |
| Repairs (total / avg) | 6 / 0.15 |
| Questions needing a repair | 4 |

| Trap | Accuracy |
|---|---|
| comparison | 1/6 (17%) |
| customer_unique_id | 3/6 (50%) |
| date_math | 5/9 (56%) |
| fanout | 3/5 (60%) |
| late_delivery | 3/4 (75%) |
| payment_rows | 0/2 (0%) |
| revenue | 7/8 (88%) |

| Id | Result | Repairs | Latency | Reason |
|---|---|---|---|---|
| e01 | correct | 0 | 7.6s | match |
| e02 | correct | 0 | 3.7s | match |
| e03 | correct | 0 | 6.9s | match |
| e04 | correct | 0 | 3.5s | match |
| e05 | correct | 0 | 3.6s | match |
| e06 | correct | 0 | 9.6s | match |
| e07 | correct | 0 | 4.0s | match |
| e08 | correct | 0 | 4.7s | match |
| e09 | correct | 0 | 6.4s | match |
| e10 | correct | 0 | 12.4s | match |
| e11 | correct | 0 | 8.0s | match |
| e12 | correct | 0 | 5.2s | match |
| m01 | wrong | 0 | 10.0s | no agent column matches gold column 2 (values differ) |
| m02 | correct | 0 | 13.3s | match |
| m03 | correct | 0 | 18.3s | match |
| m04 | correct | 0 | 8.6s | match |
| m05 | correct | 0 | 13.8s | match |
| m06 | correct | 0 | 56.8s | match |
| m07 | correct | 0 | 8.6s | match |
| m08 | correct | 0 | 7.0s | match |
| m09 | correct | 0 | 13.3s | match |
| m10 | correct | 0 | 5.5s | match |
| m11 | wrong | 1 | 17.0s | row count 1000, expected 1 |
| m12 | correct | 0 | 18.5s | match |
| m13 | correct | 0 | 18.3s | match |
| m14 | correct | 0 | 7.4s | match |
| m15 | wrong | 0 | 7.6s | row count 5, expected 2 |
| m16 | correct | 0 | 15.8s | match |
| h01 | error | 1 | 22.5s | agent gave up: BinderException: Binder Error: Table "o" does not have a column named "sell |
| h02 | wrong | 0 | 18.7s | row count 1, expected 2 |
| h03 | correct | 0 | 11.4s | match |
| h04 | correct | 0 | 37.8s | match |
| h05 | wrong | 0 | 37.3s | no agent column matches gold column 3 (values differ) |
| h06 | error | 2 | 36.6s | agent gave up: BinderException: Binder Error: Referenced column "customer_unique_id" not f |
| h07 | wrong | 0 | 30.1s | row count 17, expected 2 |
| h08 | correct | 0 | 38.7s | match |
| h09 | error | 2 | 61.5s | agent gave up: BinderException: Binder Error: Referenced column "customer_unique_id" not f |
| h10 | wrong | 0 | 41.6s | no agent column matches gold column 1 (values differ) |
| h11 | wrong | 0 | 25.3s | no agent column matches gold column 1 (values differ) |
| h12 | correct | 0 | 28.3s | match |
