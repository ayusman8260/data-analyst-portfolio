-- Q1. How do revenue and order volume trend month by month?
-- Revenue = item price (excludes freight). Cancelled/unavailable orders removed.
SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month,
       COUNT(DISTINCT o.order_id)                    AS orders,
       ROUND(SUM(oi.price), 2)                       AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY 1
ORDER BY 1;
