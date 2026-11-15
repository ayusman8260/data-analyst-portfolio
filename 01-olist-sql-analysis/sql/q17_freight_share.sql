-- Q17. Freight as a percent of price, by category (high = shipping-sensitive).
SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
       COUNT(*) AS items,
       ROUND(100.0 * SUM(oi.freight_value) / SUM(oi.price), 1) AS freight_pct_of_price
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
GROUP BY 1
HAVING COUNT(*) >= 50
ORDER BY freight_pct_of_price DESC
LIMIT 15;
