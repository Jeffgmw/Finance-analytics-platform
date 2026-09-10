SELECT c.customer_id,
       COUNT(DISTINCT a.account_id) AS account_count,
       COALESCE(SUM(a.balance), 0) AS total_balance,
       COALESCE(SUM(t.amount), 0) AS transaction_value
FROM customers c
LEFT JOIN accounts a ON a.customer_id = c.customer_id
LEFT JOIN transactions t ON t.account_id = a.account_id
GROUP BY c.customer_id
ORDER BY transaction_value DESC;
