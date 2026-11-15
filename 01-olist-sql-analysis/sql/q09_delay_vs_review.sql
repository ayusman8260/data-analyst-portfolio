-- Q9. Does a late delivery hurt review scores?
WITH d AS (
  SELECT o.order_id,
         CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
              THEN 'late' ELSE 'on_time' END AS delivery
  FROM orders o
  WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
)
SELECT d.delivery,
       COUNT(*)                          AS reviews,
       ROUND(AVG(r.review_score), 2)     AS avg_review_score,
       ROUND(100.0 * SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_negative
FROM d
JOIN reviews r ON r.order_id = d.order_id
GROUP BY d.delivery;
