-- Q16. When do customers order? Orders by weekday (0 = Sunday) and hour.
SELECT strftime('%w', order_purchase_timestamp) AS weekday,
       strftime('%H', order_purchase_timestamp) AS hour,
       COUNT(*) AS orders
FROM orders
GROUP BY 1, 2
ORDER BY orders DESC
LIMIT 15;
