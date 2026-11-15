-- Q10. Repeat-customer rate. customer_id is per ORDER, so use customer_unique_id.
WITH per_customer AS (
  SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS orders
  FROM orders o
  JOIN customers c ON c.customer_id = o.customer_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY c.customer_unique_id
)
SELECT COUNT(*)                                            AS customers,
       SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END)       AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct
FROM per_customer;
