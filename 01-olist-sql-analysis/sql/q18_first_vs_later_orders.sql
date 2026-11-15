-- Q18. Are customers' later orders bigger than their first order?
WITH order_value AS (
  SELECT o.order_id, c.customer_unique_id, o.order_purchase_timestamp AS ts, SUM(oi.price) AS value
  FROM orders o
  JOIN customers c ON c.customer_id = o.customer_id
  JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY o.order_id
),
numbered AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY ts) AS order_number
  FROM order_value
)
SELECT CASE WHEN order_number = 1 THEN 'first order' ELSE 'later order' END AS order_type,
       COUNT(*) AS orders,
       ROUND(AVG(value), 2) AS avg_order_value
FROM numbered
GROUP BY 1;
