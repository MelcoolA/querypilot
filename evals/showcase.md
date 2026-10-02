# Showcase: 8 Olist questions, before and after

Eight questions asked by hand on the Olist dataset. Each one has the "before"
entry (baseline agent, no Phase 2 fixes) and, after every Phase 2 fix, an
"after" entry from re-running the same question.

Baseline run: 2026-10-02, `LLM_PROVIDER=ollama`, `qwen2.5-coder:7b`. Raw output
is frozen in `evals/results/baseline/`. Correct answers come from the gold SQL
in `evals/gold.yaml` (gold id shown next to each question).

| # | Question | Before |
|---|---|---|
| 1 | How many orders were delivered? | ✅ Correct |
| 2 | What is the average review score? | ⚠️ Right number, wrong explanation |
| 3 | How many orders were paid by each payment type? | ❌ Counted payment rows |
| 4 | Which 5 states have the most customers? | ❌ Counted orders, not customers |
| 5 | What are the top 5 product categories by revenue? | ❌ Wrong revenue formula |
| 6 | What is the average delivery time in days by state? | ❌ Failed after 3 repairs |
| 7 | Do late deliveries get worse reviews? | ❌ Opposite of the truth |
| 8 | Which month had the highest number of orders? | ✅ Correct |

Baseline score: 2 of 8 fully correct.

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
