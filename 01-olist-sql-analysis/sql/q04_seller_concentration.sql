-- Q4. Revenue concentration: what share of revenue comes from the top 20% of sellers?
WITH seller_rev AS (
  SELECT seller_id, SUM(price) AS revenue
  FROM order_items
  GROUP BY seller_id
),
bucketed AS (
  SELECT seller_id, revenue,
         NTILE(5) OVER (ORDER BY revenue DESC) AS quintile
  FROM seller_rev
)
SELECT quintile,
       COUNT(*)                  AS sellers,
       ROUND(SUM(revenue), 2)    AS revenue,
       ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM seller_rev), 1) AS pct_of_revenue
FROM bucketed
GROUP BY quintile
ORDER BY quintile;
