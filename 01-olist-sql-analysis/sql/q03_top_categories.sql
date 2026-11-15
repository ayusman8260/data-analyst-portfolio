-- Q3. Top 10 product categories by revenue (English names).
SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
       COUNT(*)                   AS items_sold,
       ROUND(SUM(oi.price), 2)    AS revenue,
       ROUND(100.0 * SUM(oi.price) / (SELECT SUM(price) FROM order_items), 1) AS pct_of_total
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
GROUP BY 1
ORDER BY revenue DESC
LIMIT 10;
