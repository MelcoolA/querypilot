## Eval summary: ollama:qwen2.5-coder:7b on olist (snowflake), 2026-10-02 23:02

| Metric | Value |
|---|---|
| Accuracy (overall) | 30/40 (75%) |
| Accuracy (easy) | 12/12 (100%) |
| Accuracy (medium) | 13/16 (81%) |
| Accuracy (hard) | 5/12 (42%) |
| Agent gave up / crashed | 4 |
| Avg latency | 18.7s |
| Avg tokens (in / out) | 5894 / 129 |
| Avg cost per question | $0.0000 |
| Repairs (total / avg) | 5 / 0.12 |
| Questions needing a repair | 4 |

| Trap | Accuracy |
|---|---|
| comparison | 2/6 (33%) |
| customer_unique_id | 3/6 (50%) |
| date_math | 5/9 (56%) |
| fanout | 3/5 (60%) |
| late_delivery | 4/4 (100%) |
| payment_rows | 0/2 (0%) |
| revenue | 7/8 (88%) |

| Id | Result | Repairs | Latency | Reason |
|---|---|---|---|---|
| e01 | correct | 0 | 5.2s | match |
| e02 | correct | 0 | 4.3s | match |
| e03 | correct | 0 | 4.8s | match |
| e04 | correct | 0 | 3.9s | match |
| e05 | correct | 0 | 4.3s | match |
| e06 | correct | 0 | 12.9s | match |
| e07 | correct | 0 | 4.7s | match |
| e08 | correct | 0 | 6.2s | match |
| e09 | correct | 0 | 8.6s | match |
| e10 | correct | 0 | 9.0s | match |
| e11 | correct | 0 | 9.2s | match |
| e12 | correct | 0 | 5.5s | match |
| m01 | wrong | 0 | 13.7s | no agent column matches gold column 2 (values differ) |
| m02 | correct | 0 | 11.5s | match |
| m03 | correct | 0 | 18.8s | match |
| m04 | correct | 0 | 9.2s | match |
| m05 | correct | 0 | 15.3s | match |
| m06 | correct | 0 | 35.6s | match |
| m07 | correct | 0 | 13.7s | match |
| m08 | correct | 0 | 7.3s | match |
| m09 | correct | 0 | 15.9s | match |
| m10 | correct | 0 | 5.9s | match |
| m11 | error | 1 | 10.6s | agent gave up: ProgrammingError: 000904 (42000): SQL compilation error: error line 2 at po |
| m12 | correct | 0 | 21.2s | match |
| m13 | correct | 0 | 18.5s | match |
| m14 | correct | 0 | 6.7s | match |
| m15 | wrong | 0 | 8.7s | row count 5, expected 2 |
| m16 | correct | 0 | 17.4s | match |
| h01 | error | 1 | 26.9s | agent gave up: ProgrammingError: 000904 (42000): SQL compilation error: error line 8 at po |
| h02 | correct | 0 | 35.2s | match |
| h03 | correct | 0 | 12.8s | match |
| h04 | correct | 0 | 54.3s | match |
| h05 | wrong | 0 | 38.9s | no agent column matches gold column 3 (values differ) |
| h06 | error | 1 | 22.2s | agent gave up: ProgrammingError: 000904 (42000): SQL compilation error: error line 5 at po |
| h07 | wrong | 0 | 30.6s | no agent column matches gold column 1 (values differ) |
| h08 | correct | 0 | 46.3s | match |
| h09 | error | 2 | 50.1s | agent gave up: ProgrammingError: 000904 (42000): SQL compilation error: error line 3 at po |
| h10 | wrong | 0 | 49.5s | no agent column matches gold column 1 (values differ) |
| h11 | wrong | 0 | 34.6s | no agent column matches gold column 1 (values differ) |
| h12 | correct | 0 | 36.5s | match |
