-- Q11. Cumulative (running) revenue by month.
WITH monthly AS (
  SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month, SUM(oi.price) AS revenue
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
    AND o.order_purchase_timestamp >= '2017-01-01'   -- 2016 and Sep 2018 are sparse/partial months
    AND o.order_purchase_timestamp <  '2018-09-01'
  GROUP BY 1
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_revenue
FROM monthly
ORDER BY month;
