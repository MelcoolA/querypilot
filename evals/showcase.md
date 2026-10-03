# Showcase: 8 Olist questions, before and after

Eight questions asked by hand on the Olist dataset. Each one has the "before"
entry (baseline agent, no Phase 2 fixes) and, after every Phase 2 fix, an
"after" entry from re-running the same question.

Baseline run: 2026-10-02, `LLM_PROVIDER=ollama`, `qwen2.5-coder:7b`. Raw output
is frozen in `evals/results/baseline/`. Correct answers come from the gold SQL
in `evals/gold.yaml` (gold id shown next to each question).

| # | Question | Before | After fix 1 (semantic layer) | After fix 2 (repair loop) | After fix 3 (summarize) | After fix 4 (few-shot) |
|---|---|---|---|---|---|---|
| 1 | How many orders were delivered? | ✅ Correct | ✅ Correct | ✅ Correct | ✅ Correct | ✅ Correct |
| 2 | What is the average review score? | ⚠️ Right number, wrong explanation | ⚠️ Right number, wrong explanation | ⚠️ Same | ✅ Fixed explanation | ✅ Correct |
| 3 | How many orders were paid by each payment type? | ❌ Counted payment rows | ❌ Counted payment rows | ❌ Same | ❌ Same | ❌ Same |
| 4 | Which 5 states have the most customers? | ❌ Counted orders, not customers | ✅ Fixed | ✅ Correct | ✅ Correct | ✅ Correct |
| 5 | What are the top 5 product categories by revenue? | ❌ Wrong revenue formula | ✅ Fixed | ✅ Correct | ✅ Correct | ✅ Correct |
| 6 | What is the average delivery time in days by state? | ❌ Failed after 3 repairs | ❌ Wrong join, misleading answer | ❌ Honest give-up (was misleading) | ❌ Honest give-up | ❌ Honest give-up |
| 7 | Do late deliveries get worse reviews? | ❌ Opposite of the truth | ❌ No comparison group | ❌ Same | ⚠️ Right conclusion, on-time avg slightly off | ❌ Regressed: late group only |
| 8 | Which month had the highest number of orders? | ✅ Correct | ✅ Correct | ✅ Correct | ✅ Correct | ✅ Correct |

Baseline score: 2 of 8 fully correct. After fix 1: 4 of 8. After fix 2: 4 of 8. After fix 3: 5 of 8 with a correct answer (h02's conclusion is right, its SQL still scores wrong). After fix 4: 4 of 8 (h02 lost its comparison again).

---

## 1. How many orders were delivered? (e01)

**Correct answer:** 96,478 orders.

### Before (baseline): ✅ Correct

```sql
SELECT COUNT(order_id) AS total_delivered_orders
FROM orders
WHERE order_status = 'delivered'
LIMIT 1000
```

> 96,478 orders were delivered. The SQL query counted the number of orders
> where the status was 'delivered'.

**Why:** Correct SQL and answer.

### After fix 1, semantic layer: ✅ Correct

```sql
SELECT
  COUNT(order_id) AS delivered_orders
FROM orders
WHERE
  order_status = 'delivered'
LIMIT 1000
```

> 96,478 orders were delivered. The SQL query counted the number of orders where the status was 'delivered'.

**Why:** Same correct SQL as before.

### After fix 2, repair loop: unchanged

**Why:** Same SQL and outcome as fix 1; this question never needed a repair.

### After fix 3, summarize: ✅ Correct

> 96,478 orders were delivered.

**Why:** Same SQL; the answer is now a single plain sentence.

### After fix 4, few-shot: ✅ Correct

> 96,478 orders were delivered. The query counted distinct order IDs where the order status was 'delivered'.

**Why:** Correct; the SQL now uses COUNT(DISTINCT order_id), copying the style of the examples.

---

## 2. What is the average review score? (e02)

**Correct answer:** 4.09 (4.086, over all 99,224 reviews).

### Before (baseline): ⚠️ Right number, wrong explanation

```sql
SELECT AVG(review_score) AS average_review_score
FROM order_reviews
LIMIT 1000
```

> The average review score is 4.09. The SQL query calculated this by averaging
> the review scores from the first 1000 rows in the `order_reviews` table.

**Why:** The summary misread the auto-added `LIMIT 1000` as a sample limit; the average covers all rows.

### After fix 1, semantic layer: ⚠️ Right number, wrong explanation

```sql
SELECT
  AVG(review_score) AS average_review_score
FROM order_reviews
LIMIT 1000
```

> The average review score is 4.09. The SQL query calculated this by averaging the review scores from the first 1000 rows in the `order_reviews` table.

**Why:** SQL correct; the summary still claims the average used only the first 1000 rows (summarize fix pending).

### After fix 2, repair loop: unchanged

**Why:** Same SQL and answer as fix 1; the summary still says "first 1000 rows".

### After fix 3, summarize: ✅ Correct (explanation fixed)

> The average review score is 4.09.

**Why:** Same SQL; the summary no longer claims the average used only the first 1000 rows, because the prompt now explains that LIMIT only caps returned rows.

### After fix 4, few-shot: ✅ Correct

> The average review score is 4.09.

**Why:** Correct, and the explanation stays fixed.

---

## 3. How many orders were paid by each payment type? (m01)

**Correct answer:** credit_card 76,505, boleto 19,784, voucher 3,866, debit_card 1,528, not_defined 3.

### Before (baseline): ❌ Counted payment rows

```sql
SELECT payment_type, COUNT(order_id) AS order_count
FROM order_payments
GROUP BY payment_type
LIMIT 1000
```

> The number of orders paid by each payment type is as follows: 19,784 boleto,
> 76,795 credit card, 5,775 voucher, 1,529 debit card, and 3 not defined.

**Why:** Counted payment rows instead of distinct orders, so split payments are double counted (voucher +49%).

### After fix 1, semantic layer: ❌ Counted payment rows

```sql
SELECT
  payment_type,
  COUNT(order_id) AS order_count
FROM order_payments
GROUP BY
  payment_type
LIMIT 1000
```

> The number of orders paid by each payment type is as follows: 19,784 boleto, 76,795 credit card, 5,775 voucher, 1,529 debit card, and 3 not defined.

**Why:** Unchanged: still COUNT(order_id) on order_payments, despite the order count definition in the semantic layer.

### After fix 2, repair loop: unchanged

**Why:** Same SQL as fix 1 (still counts payment rows); no repair was needed because the query runs fine.

### After fix 3, summarize: ❌ Counted payment rows

> The number of orders paid by each payment type is as follows: boleto (19,784), voucher (5,775), debit card (1,529), not defined (3), and credit card (76,795).

**Why:** Same SQL as before; still counts payment rows instead of distinct orders.

### After fix 4, few-shot: ❌ Counted payment rows

> The number of orders paid by each payment type is as follows: 76,795 orders were paid with credit card, 19,784 with boleto, 5,775 with voucher, 1,529 with debit card, and 3 with an undefined payment type.

**Why:** Still counts payment rows, even with an example that counts distinct orders from a multi-row table.

---

## 4. Which 5 states have the most customers? (m02)

**Correct answer:** SP 40,302, RJ 12,384, MG 11,259, RS 5,277, PR 4,882.

### Before (baseline): ❌ Counted orders, not customers

```sql
SELECT customer_state, COUNT(customer_id) AS customer_count
FROM customers
GROUP BY customer_state
ORDER BY customer_count DESC
LIMIT 5
```

> The five states with the most customers are SP (São Paulo) with 41,746
> customers, RJ (Rio de Janeiro) with 12,852 customers, MG (Minas Gerais) with
> 11,635 customers, RS (Rio Grande do Sul) with 5,466 customers, and PR (Paraná)
> with 5,045 customers.

**Why:** Counted `customer_id`, which is new on every order, instead of `customer_unique_id`; right states, counts about 4% high.

### After fix 1, semantic layer: ✅ Correct (fixed)

```sql
SELECT
  customer_state,
  COUNT(DISTINCT customer_unique_id) AS customer_count
FROM customers
GROUP BY
  customer_state
ORDER BY
  customer_count DESC
LIMIT 5
```

> The five states with the most customers are SP (São Paulo) with 40,302 customers, RJ (Rio de Janeiro) with 12,384 customers, MG (Minas Gerais) with 11,259 customers, RS (Rio Grande do Sul) with 5,277 customers, and PR (Paraná) with 4,882 customers.

**Why:** Now counts DISTINCT customer_unique_id, as the customer definition says.

### After fix 2, repair loop: unchanged

**Why:** Same SQL and outcome as fix 1; this question never needed a repair.

### After fix 3, summarize: ✅ Correct

> The five states with the most customers are SP (São Paulo) with 40,302 customers, RJ (Rio de Janeiro) with 12,384 customers, MG (Minas Gerais) with 11,259 customers, RS (Rio Grande do Sul) with 5,277 customers, and PR (Paraná) with 4,882 customers.

**Why:** Same SQL and outcome as fix 1.

### After fix 4, few-shot: ✅ Correct

> The five states with the most customers are SP (São Paulo) with 40,302 customers, RJ (Rio de Janeiro) with 12,384 customers, MG (Minas Gerais) with 11,259 customers, RS (Rio Grande do Sul) with 5,277 customers, and PR (Paraná) with 4,882 customers.

**Why:** Correct.

---

## 5. What are the top 5 product categories by revenue? (m03)

**Correct answer:** health_beauty 1,258,681, watches_gifts 1,205,006, bed_bath_table 1,036,989, sports_leisure 988,049, computers_accessories 911,954.

### Before (baseline): ❌ Wrong revenue formula

```sql
SELECT p.product_category_name_pt, SUM(oi.price * oi.freight_value) AS total_revenue
FROM order_items AS oi
JOIN orders AS o ON oi.order_id = o.order_id
JOIN products AS p ON oi.product_id = p.product_id
GROUP BY p.product_category_name_pt
ORDER BY total_revenue DESC
LIMIT 5
```

> The top 5 product categories by revenue are: beleza_saude with $36,689,303.31,
> esporte_lazer with $30,064,636.37, relogios_presentes with $24,662,365.83,
> cama_mesa_banho with $23,613,640.06, and utilidades_domesticas with
> $22,855,787.06. Revenue was calculated as the sum of the price and freight
> value of each order item.

**Why:** Multiplied price by freight, used Portuguese names, and the summary described the formula wrongly.

### After fix 1, semantic layer: ✅ Correct (fixed)

```sql
SELECT
  p.product_category,
  SUM(oi.price) AS total_revenue
FROM order_items AS oi
JOIN products AS p
  ON oi.product_id = p.product_id
GROUP BY
  p.product_category
ORDER BY
  total_revenue DESC
LIMIT 5
```

> The top 5 product categories by revenue are: health_beauty with $1,258,681.34, watches_gifts with $1,205,005.68, bed_bath_table with $1,036,988.68, sports_leisure with $988,048.97, and computers_accessories with $911,954.32. Revenue was calculated as the sum of the prices of all items in each category.

**Why:** Revenue is now SUM(price) with English category names, as the revenue definition says.

### After fix 2, repair loop: unchanged

**Why:** Same SQL and outcome as fix 1; this question never needed a repair.

### After fix 3, summarize: ✅ Correct

> The top 5 product categories by revenue are:
> 1. Health and Beauty: $1,258,681.34
> 2. Watches and Gifts: $1,205,005.68
> 3. Bed, Bath, and Table: $1,036,988.68
> 4. Sports and Leisure: $988,048.97
> 5. Computers and Accessories: $911,954.32
> Revenue is calculated as the sum of prices for all items in each category.

**Why:** Same SQL. The summary now prettifies category names and still uses "$" for amounts in Brazilian reais (the currency is not in the prompt).

### After fix 4, few-shot: ✅ Correct

> The top 5 product categories by revenue are:
> 1. Health and Beauty: $1,258,681.34
> 2. Watches and Gifts: $1,205,005.68
> 3. Bed, Bath, and Table: $1,036,988.68
> 4. Sports and Leisure: $988,048.97
> 5. Computers and Accessories: $911,954.32
> Revenue is calculated as the sum of prices for all items in each category.

**Why:** Same SQL; still shows Brazilian reais with "$".

---

## 6. What is the average delivery time in days by state? (h01)

**Correct answer:** 27 states, 12.6 days overall. Fastest SP 8.8, PR 12.0, MG 12.0; slowest RR 29.4, AP 27.2, AM 26.4.

### Before (baseline): ❌ Failed after 3 repairs

```sql
SELECT o.customer_state,
       AVG((o.order_delivered_customer_date - o.order_purchase_timestamp) / INTERVAL '1' DAY) AS avg_delivery_time
FROM orders AS o
JOIN customers AS c ON o.customer_id = c.customer_id
GROUP BY o.customer_state
LIMIT 1000
```

> I could not answer this confidently. After 3 repair attempts the query still
> failed with: BinderException: Binder Error: Table "o" does not have a column
> named "customer_state"

**Why:** Took `customer_state` from `orders` instead of `customers`, and every repair returned the identical SQL.

### After fix 1, semantic layer: ❌ Wrong join, misleading answer

```sql
SELECT
  s.seller_state,
  AVG(
    DATE_DIFF('SECOND', o.order_purchase_timestamp, o.order_delivered_customer_date) / 86400.0
  ) AS avg_delivery_time
FROM orders AS o
JOIN sellers AS s
  ON o.customer_id = s.seller_id
WHERE
  o.order_status = 'delivered' AND NOT o.order_delivered_customer_date IS NULL
GROUP BY
  s.seller_state
LIMIT 1000
```

> There are no delivery times available in the data.

**Why:** Grouped by seller_state with a nonsense join (customer_id = seller_id), got 0 rows, and the summary claimed no delivery data exists; worse than giving up.

### After fix 2, repair loop: ❌ Honest give-up (was a misleading answer)

```sql
SELECT
  s.seller_state,
  AVG(
    DATE_DIFF('SECOND', o.order_purchase_timestamp, o.order_delivered_customer_date) / 86400.0
  ) AS avg_delivery_time
FROM orders AS o
JOIN sellers AS s
  ON o.seller_id = s.seller_id
WHERE
  o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY
  s.seller_state
```

> I could not answer this confidently. After 1 repair attempts the query still failed with: BinderException: Binder Error: Table "o" does not have a column named "seller_id"
> Candidate bindings: : "order_id"
> LINE 8:   ON o.seller_id = s.seller_id
>              ^ (stopped early: repair attempt 1 repeated an earlier query)

**Why:** The repair returned its first query again, so the loop stopped after 1 repair instead of trying a nonsense join; the agent now admits it can't answer instead of claiming the data doesn't exist.

### After fix 3, summarize: ❌ Honest give-up

> I could not answer this confidently. After 1 repair attempt the query still failed with: BinderException: Binder Error: Table "o" does not have a column named "seller_id"
> Candidate bindings: : "order_id"
> LINE 8:   ON o.seller_id = s.seller_id
>              ^ (stopped early: repair attempt 1 repeated an earlier query)

**Why:** Same as fix 2; the message now says "1 repair attempt" instead of "1 repair attempts".

### After fix 4, few-shot: ❌ Honest give-up

> I could not answer this confidently. After 1 repair attempt the query still failed with: BinderException: Binder Error: Table "o" does not have a column named "seller_id"
> Candidate bindings: : "order_id"
> LINE 8:   ON o.seller_id = s.seller_id
>              ^ (stopped early: repair attempt 1 repeated an earlier query)

**Why:** Same SQL and outcome as fixes 2 and 3.

---

## 7. Do late deliveries get worse reviews? (h02)

**Correct answer:** Yes. Late orders average 2.57 vs 4.29 on time; 54% of late orders get 1 or 2 stars vs 9% on time.

### Before (baseline): ❌ Opposite of the truth

```sql
SELECT o.order_id, o.order_purchase_timestamp, o.order_delivered_customer_date, r.review_score
FROM orders AS o
JOIN order_reviews AS r ON o.order_id = r.order_id
WHERE o.order_delivered_customer_date > o.order_estimated_delivery_date
ORDER BY r.review_score DESC
LIMIT 1000
```

> All 1000 late deliveries in the result have a review score of 5. This
> suggests that late deliveries do not get worse reviews; in fact, they seem to
> receive the highest possible rating.

**Why:** No on-time group to compare against, rows sorted best-first and cut at 1,000, then read as the whole picture.

### After fix 1, semantic layer: ❌ No comparison group (conclusion now right)

```sql
SELECT
  AVG(CASE WHEN order_reviews.review_score > 3 THEN 1 ELSE 0 END) AS late_delivery_high_reviews,
  AVG(CASE WHEN order_reviews.review_score <= 3 THEN 1 ELSE 0 END) AS late_delivery_low_reviews
FROM orders
JOIN order_reviews
  ON orders.order_id = order_reviews.order_id
WHERE
  orders.order_status = 'delivered'
  AND orders.order_delivered_customer_date > orders.order_estimated_delivery_date
LIMIT 1000
```

> Late deliveries receive lower reviews. 35% of late deliveries have a review score greater than 3, while 65% have a score of 3 or lower.

**Why:** Looked only at late orders (65% scored 3 or lower) with no on-time group; the conclusion is correct but the query does not support it.

### After fix 2, repair loop: unchanged

**Why:** Same SQL and answer as fix 1; still no on-time group to compare against.

### After fix 3, summarize: ⚠️ Right conclusion, still scored wrong

```sql
WITH late_orders AS (
  SELECT
    order_id
  FROM orders
  WHERE
    order_status = 'delivered'
    AND order_delivered_customer_date > order_estimated_delivery_date
), review_scores AS (
  SELECT
    order_id,
    review_score
  FROM order_reviews
)
SELECT
  AVG(
    CASE
      WHEN NOT late_orders.order_id IS NULL
      THEN review_scores.review_score
      ELSE NULL
    END
  ) AS avg_late_review_score,
  AVG(
    CASE WHEN late_orders.order_id IS NULL THEN review_scores.review_score ELSE NULL END
  ) AS avg_on_time_review_score
FROM late_orders
FULL OUTER JOIN review_scores
  ON late_orders.order_id = review_scores.order_id
LIMIT 1000
```

> Late deliveries receive an average review score of 2.57, while on-time deliveries receive an average score of 4.21. This suggests that late deliveries tend to get worse reviews.

**Why:** The comparison rule worked: the query now returns late and on-time averages together, and the answer correctly says late deliveries get worse reviews (2.57 vs 4.21). Still scored wrong: "on time" includes canceled and undelivered orders (4.21 vs the correct 4.29), and the result is one wide row rather than one row per group.

### After fix 4, few-shot: ❌ Regressed, late group only

```sql
WITH late_orders AS (
  SELECT
    o.order_id
  FROM orders AS o
  WHERE
    o.order_status = 'delivered'
    AND o.order_delivered_customer_date > o.order_estimated_delivery_date
), review_scores AS (
  SELECT
    r.review_score
  FROM order_reviews AS r
  JOIN late_orders AS lo
    ON r.order_id = lo.order_id
)
SELECT
  AVG(review_score) AS avg_late_review_score
FROM review_scores
LIMIT 1000
```

> The average review score for late deliveries is 2.57.

**Why:** The query returns only the late-delivery average, so there is no comparison; the summary states the number without answering the question, despite the rule to say when a group is missing. Fix 3 had the right conclusion.

---

## 8. Which month had the highest number of orders? (m04)

**Correct answer:** November 2017, 7,544 orders.

### Before (baseline): ✅ Correct

```sql
SELECT DATE_TRUNC('MONTH', order_purchase_timestamp) AS month, COUNT(order_id) AS order_count
FROM orders
GROUP BY month
ORDER BY order_count DESC
LIMIT 1
```

> The month with the highest number of orders was November 2017, with 7,544
> orders.

**Why:** Correct SQL and answer.

### After fix 1, semantic layer: ✅ Correct

```sql
SELECT
  DATE_TRUNC('MONTH', order_purchase_timestamp) AS month,
  COUNT(DISTINCT order_id) AS order_count
FROM orders
GROUP BY
  month
ORDER BY
  order_count DESC
LIMIT 1
```

> The month with the highest number of orders was November 2017, with 7,544 distinct orders.

**Why:** Same answer; now uses COUNT(DISTINCT order_id).

### After fix 2, repair loop: unchanged

**Why:** Same SQL and outcome as fix 1; this question never needed a repair.

### After fix 3, summarize: ✅ Correct

> The month with the highest number of orders was November 2017, with 7,544 distinct orders.

**Why:** Same SQL and outcome.

### After fix 4, few-shot: ✅ Correct

> The month with the highest number of orders was November 2017, with 7,544 distinct orders.

**Why:** Correct.
