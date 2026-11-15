-- Q15. Sellers with large sales but poor reviews (a quality-risk list).
WITH seller_sales AS (
  SELECT seller_id, SUM(price) AS revenue, COUNT(DISTINCT order_id) AS orders
  FROM order_items GROUP BY seller_id
),
seller_reviews AS (
  SELECT oi.seller_id, AVG(r.review_score) AS avg_score
  FROM (SELECT DISTINCT order_id, seller_id FROM order_items) oi
  JOIN reviews r ON r.order_id = oi.order_id
  GROUP BY oi.seller_id
)
SELECT ss.seller_id, ss.orders, ROUND(ss.revenue, 2) AS revenue, ROUND(sr.avg_score, 2) AS avg_review_score
FROM seller_sales ss
JOIN seller_reviews sr USING (seller_id)
WHERE ss.revenue >= (SELECT AVG(revenue) FROM seller_sales)   -- above-average sales
  AND sr.avg_score < 4.0
ORDER BY ss.revenue DESC
LIMIT 20;
