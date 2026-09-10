SELECT DATE_TRUNC('month', txn_date)::date AS month,
       txn_type,
       COUNT(*) AS transaction_count,
       SUM(amount) AS total_value,
       AVG(amount) AS average_value
FROM transactions
GROUP BY 1, 2
ORDER BY 1, 2;
