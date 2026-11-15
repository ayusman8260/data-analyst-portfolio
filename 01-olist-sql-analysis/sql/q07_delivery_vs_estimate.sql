-- Q7. Actual vs estimated delivery time (days) for delivered orders.
SELECT ROUND(AVG(julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)), 1) AS avg_actual_days,
       ROUND(AVG(julianday(order_estimated_delivery_date)  - julianday(order_purchase_timestamp)), 1) AS avg_estimated_days,
       ROUND(AVG(julianday(order_estimated_delivery_date) - julianday(order_delivered_customer_date)), 1) AS avg_days_early
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL;
