WITH account_rollup AS (
    SELECT customer_id,
           COUNT(*) AS account_count,
           COALESCE(SUM(balance), 0) AS total_balance
    FROM accounts
    GROUP BY customer_id
), transaction_rollup AS (
    SELECT a.customer_id,
           COUNT(t.transaction_id) AS transaction_count,
           COALESCE(SUM(t.amount), 0) AS total_transaction_value,
           COALESCE(AVG(t.amount), 0) AS average_transaction_value
    FROM accounts a
    LEFT JOIN transactions t ON t.account_id = a.account_id
    GROUP BY a.customer_id
)
SELECT c.customer_id,
       c.annual_income,
       c.credit_score,
       COALESCE(ar.account_count, 0) AS account_count,
       COALESCE(ar.total_balance, 0) AS total_balance,
       COALESCE(tr.transaction_count, 0) AS transaction_count,
       COALESCE(tr.total_transaction_value, 0) AS total_transaction_value,
       COALESCE(tr.average_transaction_value, 0) AS average_transaction_value,
       RANK() OVER (ORDER BY COALESCE(tr.total_transaction_value, 0) DESC) AS transaction_value_rank
FROM customers c
LEFT JOIN account_rollup ar ON ar.customer_id = c.customer_id
LEFT JOIN transaction_rollup tr ON tr.customer_id = c.customer_id
ORDER BY total_transaction_value DESC;
