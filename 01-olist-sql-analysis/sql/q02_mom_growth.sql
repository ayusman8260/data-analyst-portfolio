-- Q2. Month-over-month revenue growth (LAG window function).
WITH monthly AS (
  SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month,
         SUM(oi.price) AS revenue
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
    AND o.order_purchase_timestamp >= '2017-01-01'   -- 2016 and Sep 2018 are sparse/partial months
    AND o.order_purchase_timestamp <  '2018-09-01'
  GROUP BY 1
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(LAG(revenue) OVER (ORDER BY month), 2) AS prev_month,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1) AS mom_growth_pct
FROM monthly
ORDER BY month;
