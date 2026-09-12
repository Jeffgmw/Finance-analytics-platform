"""Build the small serving tables used by the dashboards.

Run after the raw customers/accounts/transactions tables have been loaded.
The raw tables remain the source of truth; these tables are derived analytics data.
"""
import argparse
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from data_pipeline.config import ROOT

load_dotenv()

ANALYTICS_SCHEMA = (ROOT / "sql" / "analytics_schema.sql").read_text()


def sqlalchemy_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def build(database_url: str) -> None:
    engine = create_engine(sqlalchemy_url(database_url), pool_pre_ping=True)
    statements = [s.strip() for s in ANALYTICS_SCHEMA.split(";") if s.strip()]
    with engine.begin() as conn:
        for statement in statements:
            conn.exec_driver_sql(statement)

        conn.execute(text("TRUNCATE TABLE analytics_daily"))
        conn.execute(text("""
            INSERT INTO analytics_daily (
                txn_date, txn_type, channel, merchant_category, account_type,
                threat_level, transaction_count, total_value, high_count, high_value
            )
            SELECT
                t.txn_date,
                COALESCE(t.txn_type, 'Unknown'),
                COALESCE(t.channel, 'Unknown'),
                COALESCE(t.merchant_category, 'Unknown'),
                COALESCE(a.account_type, 'Unknown'),
                CASE
                    WHEN t.amount >= 100000
                      OR (t.txn_type = 'Withdrawal' AND t.amount >= 50000)
                      OR (t.channel = 'UPI' AND t.amount >= 25000) THEN 'High'
                    WHEN t.amount >= 10000
                      OR t.txn_type = 'Withdrawal'
                      OR t.channel = 'UPI' THEN 'Medium'
                    ELSE 'Low'
                END AS threat_level,
                COUNT(*) AS transaction_count,
                COALESCE(SUM(t.amount), 0) AS total_value,
                COUNT(*) FILTER (
                    WHERE t.amount >= 100000
                       OR (t.txn_type = 'Withdrawal' AND t.amount >= 50000)
                       OR (t.channel = 'UPI' AND t.amount >= 25000)
                ) AS high_count,
                COALESCE(SUM(t.amount) FILTER (
                    WHERE t.amount >= 100000
                       OR (t.txn_type = 'Withdrawal' AND t.amount >= 50000)
                       OR (t.channel = 'UPI' AND t.amount >= 25000)
                ), 0) AS high_value
            FROM transactions t
            JOIN accounts a ON a.account_id = t.account_id
            GROUP BY 1,2,3,4,5,6
        """))

        conn.execute(text("TRUNCATE TABLE analytics_customer"))
        conn.execute(text("""
            INSERT INTO analytics_customer (
                customer_id, annual_income, credit_score, account_count,
                total_balance, transaction_count, total_transaction_value,
                average_transaction_value, transaction_value_rank
            )
            WITH account_rollup AS (
                SELECT customer_id, COUNT(*) AS account_count,
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
            ), ranked AS (
                SELECT c.customer_id, c.annual_income, c.credit_score,
                       COALESCE(ar.account_count,0) AS account_count,
                       COALESCE(ar.total_balance,0) AS total_balance,
                       COALESCE(tr.transaction_count,0) AS transaction_count,
                       COALESCE(tr.total_transaction_value,0) AS total_transaction_value,
                       COALESCE(tr.average_transaction_value,0) AS average_transaction_value,
                       RANK() OVER (
                           ORDER BY COALESCE(tr.total_transaction_value,0) DESC
                       ) AS transaction_value_rank
                FROM customers c
                LEFT JOIN account_rollup ar ON ar.customer_id=c.customer_id
                LEFT JOIN transaction_rollup tr ON tr.customer_id=c.customer_id
            )
            SELECT * FROM ranked
        """))

        conn.execute(text("ANALYZE analytics_daily"))
        conn.execute(text("ANALYZE analytics_customer"))

        daily_count = conn.execute(text("SELECT COUNT(*) FROM analytics_daily")).scalar_one()
        customer_count = conn.execute(text("SELECT COUNT(*) FROM analytics_customer")).scalar_one()
        print(f"analytics_daily rows: {daily_count:,}")
        print(f"analytics_customer rows: {customer_count:,}")

    engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    url = args.database_url or os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    build(url)
