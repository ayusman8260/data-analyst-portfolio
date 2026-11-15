-- Q12. Top 3 sellers in each state (RANK within partition).
WITH seller_rev AS (
  SELECT s.seller_state, s.seller_id, SUM(oi.price) AS revenue
  FROM order_items oi JOIN sellers s ON s.seller_id = oi.seller_id
  GROUP BY s.seller_state, s.seller_id
),
ranked AS (
  SELECT *, RANK() OVER (PARTITION BY seller_state ORDER BY revenue DESC) AS rnk
  FROM seller_rev
)
SELECT seller_state, seller_id, ROUND(revenue, 2) AS revenue, rnk
FROM ranked
WHERE rnk <= 3
ORDER BY seller_state, rnk;
