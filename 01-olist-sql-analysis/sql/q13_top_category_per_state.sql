-- Q13. Best-selling category in each customer state (CTE + ROW_NUMBER).
WITH state_cat AS (
  SELECT c.customer_state,
         COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
         SUM(oi.price) AS revenue
  FROM order_items oi
  JOIN orders o   ON o.order_id = oi.order_id
  JOIN customers c ON c.customer_id = o.customer_id
  JOIN products p ON p.product_id = oi.product_id
  LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
  GROUP BY 1, 2
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_state ORDER BY revenue DESC) AS rn
  FROM state_cat
)
SELECT customer_state, category, ROUND(revenue, 2) AS revenue
FROM ranked WHERE rn = 1
ORDER BY revenue DESC;
