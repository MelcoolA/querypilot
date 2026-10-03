## Eval summary: ollama:qwen2.5-coder:7b on olist, 2026-10-02 17:26

| Metric | Value |
|---|---|
| Accuracy (overall) | 29/40 (72%) |
| Accuracy (easy) | 12/12 (100%) |
| Accuracy (medium) | 11/16 (69%) |
| Accuracy (hard) | 6/12 (50%) |
| Agent gave up / crashed | 4 |
| Avg latency | 23.0s |
| Avg tokens (in / out) | 5304 / 138 |
| Avg cost per question | $0.0000 |
| Repairs (total / avg) | 6 / 0.15 |
| Questions needing a repair | 5 |

| Trap | Accuracy |
|---|---|
| comparison | 3/6 (50%) |
| customer_unique_id | 4/6 (67%) |
| date_math | 7/9 (78%) |
| fanout | 2/5 (40%) |
| late_delivery | 3/4 (75%) |
| payment_rows | 0/2 (0%) |
| revenue | 6/8 (75%) |

| Id | Result | Repairs | Latency | Reason |
|---|---|---|---|---|
| e01 | correct | 0 | 13.0s | match |
| e02 | correct | 0 | 7.8s | match |
| e03 | correct | 0 | 15.9s | match |
| e04 | correct | 0 | 7.6s | match |
| e05 | correct | 0 | 8.3s | match |
| e06 | correct | 0 | 26.6s | match |
| e07 | correct | 0 | 9.5s | match |
| e08 | correct | 0 | 7.1s | match |
| e09 | correct | 0 | 7.6s | match |
| e10 | correct | 0 | 11.0s | match |
| e11 | correct | 0 | 9.0s | match |
| e12 | correct | 0 | 5.6s | match |
| m01 | wrong | 0 | 8.9s | no agent column matches gold column 2 (values differ) |
| m02 | correct | 0 | 14.0s | match |
| m03 | correct | 0 | 19.4s | match |
| m04 | correct | 0 | 9.1s | match |
| m05 | correct | 0 | 14.5s | match |
| m06 | correct | 0 | 37.3s | match |
| m07 | wrong | 0 | 7.2s | no agent column matches gold column 1 (values differ) |
| m08 | wrong | 0 | 4.6s | no agent column matches gold column 1 (values differ) |
| m09 | correct | 0 | 16.8s | match |
| m10 | correct | 0 | 6.9s | match |
| m11 | wrong | 1 | 21.0s | row count 1000, expected 1 |
| m12 | correct | 0 | 16.0s | match |
| m13 | correct | 0 | 25.6s | match |
| m14 | correct | 0 | 9.6s | match |
| m15 | wrong | 0 | 10.0s | row count 5, expected 2 |
| m16 | correct | 0 | 22.6s | match |
| h01 | error | 1 | 29.6s | agent gave up: BinderException: Binder Error: Table "o" does not have a column named "sell |
| h02 | wrong | 0 | 28.6s | row count 1, expected 2 |
| h03 | correct | 0 | 14.6s | match |
| h04 | correct | 0 | 53.7s | match |
| h05 | wrong | 0 | 51.1s | no agent column matches gold column 3 (values differ) |
| h06 | error | 2 | 46.1s | agent gave up: BinderException: Binder Error: Referenced column "customer_unique_id" not f |
| h07 | correct | 0 | 41.4s | match |
| h08 | correct | 0 | 68.8s | match |
| h09 | correct | 0 | 41.6s | match |
| h10 | error | 1 | 44.4s | agent gave up: BinderException: Binder Error: Table "r" does not have a column named "prod |
| h11 | correct | 0 | 55.0s | match |
| h12 | error | 1 | 73.0s | agent gave up: BinderException: Binder Error: column "total_revenue" must appear in the GR |
