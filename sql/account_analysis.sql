SELECT a.account_type,
       a.status,
       COUNT(*) AS account_count,
       SUM(a.balance) AS total_balance,
       AVG(a.balance) AS average_balance
FROM accounts a
GROUP BY a.account_type, a.status
ORDER BY total_balance DESC;
