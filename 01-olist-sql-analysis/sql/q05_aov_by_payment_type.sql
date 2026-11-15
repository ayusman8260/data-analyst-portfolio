-- Q5. Average order value by payment type.
-- Caveat: payment_value is per payment METHOD. An order paid partly by voucher and partly by card
-- appears under both, so voucher AOV is understated relative to true basket size.
SELECT payment_type,
       COUNT(DISTINCT order_id)                         AS orders,
       ROUND(SUM(payment_value) / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM payments
WHERE payment_type <> 'not_defined'   -- 3 rows with zero value
GROUP BY payment_type
ORDER BY orders DESC;
