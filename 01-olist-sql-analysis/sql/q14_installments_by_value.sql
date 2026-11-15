-- Q14. Do bigger purchases use more installments? (CASE bucketing)
SELECT CASE WHEN payment_value < 50  THEN '1. under 50'
            WHEN payment_value < 150 THEN '2. 50-149'
            WHEN payment_value < 400 THEN '3. 150-399'
            ELSE '4. 400+' END AS value_bucket,
       COUNT(*) AS payments,
       ROUND(AVG(payment_installments), 2) AS avg_installments
FROM payments
WHERE payment_type = 'credit_card'
GROUP BY 1
ORDER BY 1;
