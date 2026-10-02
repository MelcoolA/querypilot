## Eval summary: ollama:qwen2.5-coder:7b on olist, 2026-10-02 16:25

| Metric | Value |
|---|---|
| Accuracy (overall) | 28/40 (70%) |
| Accuracy (easy) | 12/12 (100%) |
| Accuracy (medium) | 11/16 (69%) |
| Accuracy (hard) | 5/12 (42%) |
| Agent gave up / crashed | 1 |
| Avg latency | 40.1s |
| Avg tokens (in / out) | 5226 / 152 |
| Avg cost per question | $0.0000 |
| Repairs (total / avg) | 7 / 0.17 |
| Questions needing a repair | 5 |

| Trap | Accuracy |
|---|---|
| comparison | 2/6 (33%) |
| customer_unique_id | 4/6 (67%) |
| date_math | 6/9 (67%) |
| fanout | 2/5 (40%) |
| late_delivery | 3/4 (75%) |
| payment_rows | 0/2 (0%) |
| revenue | 5/8 (62%) |

| Id | Result | Repairs | Latency | Reason |
|---|---|---|---|---|
| e01 | correct | 0 | 12.3s | match |
| e02 | correct | 0 | 14.5s | match |
| e03 | correct | 0 | 14.3s | match |
| e04 | correct | 0 | 13.3s | match |
| e05 | correct | 0 | 13.7s | match |
| e06 | correct | 0 | 24.6s | match |
| e07 | correct | 0 | 16.1s | match |
| e08 | correct | 0 | 10.5s | match |
| e09 | correct | 0 | 20.2s | match |
| e10 | correct | 0 | 23.3s | match |
| e11 | correct | 0 | 21.4s | match |
| e12 | correct | 0 | 18.1s | match |
| m01 | wrong | 0 | 22.6s | no agent column matches gold column 2 (values differ) |
| m02 | correct | 0 | 32.3s | match |
| m03 | correct | 0 | 45.1s | match |
| m04 | correct | 0 | 22.4s | match |
| m05 | wrong | 0 | 36.0s | no agent column matches gold column 1 (values differ) |
| m06 | correct | 0 | 86.8s | match |
| m07 | correct | 0 | 24.0s | match |
| m08 | wrong | 0 | 15.1s | no agent column matches gold column 1 (values differ) |
| m09 | correct | 0 | 40.8s | match |
| m10 | correct | 0 | 19.2s | match |
| m11 | wrong | 1 | 45.9s | row count 1000, expected 1 |
| m12 | correct | 0 | 28.7s | match |
| m13 | correct | 0 | 44.4s | match |
| m14 | correct | 0 | 18.8s | match |
| m15 | wrong | 0 | 17.3s | row count 5, expected 2 |
| m16 | correct | 0 | 38.2s | match |
| h01 | wrong | 1 | 59.5s | row count 0, expected 27 |
| h02 | wrong | 0 | 33.2s | row count 1, expected 2 |
| h03 | correct | 0 | 24.3s | match |
| h04 | correct | 0 | 83.9s | match |
| h05 | wrong | 0 | 63.1s | no agent column matches gold column 3 (values differ) |
| h06 | wrong | 1 | 72.6s | no agent column matches gold column 1 (values differ) |
| h07 | wrong | 0 | 63.8s | row count 1000, expected 2 |
| h08 | correct | 0 | 83.7s | match |
| h09 | correct | 0 | 69.6s | match |
| h10 | error | 3 | 108.8s | agent gave up: BinderException: Binder Error: Table "r" does not have a column named "prod |
| h11 | correct | 0 | 70.4s | match |
| h12 | wrong | 1 | 130.3s | no agent column matches gold column 1 (values differ) |

> Re-scored after the scorer fix (January 1st dates match plain years): **29/40 (72%)**, medium 12/16. Only m05 changed (wrong -> correct). See `evals/CHANGELOG.md` entry 2.
