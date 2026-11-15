-- Monthly acquisition cohorts and how many of each cohort come back in later months.
-- Reuses the Olist database built in project 01 (SQLite syntax).
-- customer_id is per ORDER in Olist, so customers are identified by customer_unique_id.
-- PostgreSQL: replace the strftime/substr arithmetic with DATE_TRUNC + AGE or EXTRACT.
WITH orders_clean AS (
  SELECT c.customer_unique_id,
         strftime('%Y-%m', o.order_purchase_timestamp) AS order_month
  FROM orders o
  JOIN customers c ON c.customer_id = o.customer_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
),
first_order AS (
  SELECT customer_unique_id, MIN(order_month) AS cohort_month
  FROM orders_clean
  GROUP BY customer_unique_id
),
activity AS (
  SELECT DISTINCT customer_unique_id, order_month
  FROM orders_clean
)
SELECT f.cohort_month,
       (CAST(substr(a.order_month, 1, 4) AS INTEGER) - CAST(substr(f.cohort_month, 1, 4) AS INTEGER)) * 12
       + CAST(substr(a.order_month, 6, 2) AS INTEGER) - CAST(substr(f.cohort_month, 6, 2) AS INTEGER) AS month_index,
       COUNT(DISTINCT a.customer_unique_id) AS customers
FROM first_order f
JOIN activity a USING (customer_unique_id)
GROUP BY f.cohort_month, month_index
ORDER BY f.cohort_month, month_index;
