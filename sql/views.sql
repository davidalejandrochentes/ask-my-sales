DROP VIEW IF EXISTS sales_by_month_country;
DROP VIEW IF EXISTS top_customers;

CREATE VIEW sales_by_month_country AS
SELECT
    strftime('%Y-%m', order_date) AS month,
    country,
    COUNT(*) AS orders,
    ROUND(SUM(amount), 2) AS total_sales
FROM orders
WHERE status = 'completado'
GROUP BY strftime('%Y-%m', order_date), country
ORDER BY month, country;

CREATE VIEW top_customers AS
SELECT
    customer,
    COUNT(*) AS orders,
    ROUND(SUM(amount), 2) AS total_spent
FROM orders
WHERE status = 'completado'
GROUP BY customer
ORDER BY total_spent DESC, customer ASC
LIMIT 10;