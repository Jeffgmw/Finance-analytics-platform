"""Build the small serving tables used by the dashboards.

The build is intentionally batched because the Render PostgreSQL instance may
have limited memory. Raw tables remain the source of truth; these are derived
analytics data used only for fast dashboard reads.
"""

import argparse
import os
from datetime import date

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from data_pipeline.config import ROOT

load_dotenv()

ANALYTICS_SCHEMA = (ROOT / "sql" / "analytics_schema.sql").read_text()
DAILY_INDEXES = (
    "idx_analytics_daily_date",
    "idx_analytics_daily_filters",
    "idx_analytics_daily_channel",
    "idx_analytics_daily_threat_date",
)
CUSTOMER_INDEXES = (
    "idx_analytics_customer_value",
    "idx_analytics_customer_income",
)


def sqlalchemy_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def next_month(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


def _drop_secondary_indexes(conn):
    for index in DAILY_INDEXES + CUSTOMER_INDEXES:
        conn.exec_driver_sql(f"DROP INDEX IF EXISTS {index}")


def _recreate_secondary_indexes(conn):
    # Index definitions are kept in analytics_schema.sql so there is one
    # source of truth. Re-run only CREATE INDEX statements after loading.
    statements = [s.strip() for s in ANALYTICS_SCHEMA.split(";") if s.strip()]
    for statement in statements:
        if statement.upper().startswith("CREATE INDEX"):
            conn.exec_driver_sql(statement)


def build(database_url: str) -> None:
    engine = create_engine(
        sqlalchemy_url(database_url),
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        connect_args={"connect_timeout": 30},
    )

    # Create tables first. Keep this transaction short.
    with engine.begin() as conn:
        for statement in [s.strip() for s in ANALYTICS_SCHEMA.split(";") if s.strip()]:
            conn.exec_driver_sql(statement)
        _drop_secondary_indexes(conn)

    # ------------------------------------------------------------------
    # analytics_daily
    # ------------------------------------------------------------------
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE analytics_daily"))

    with engine.connect() as conn:
        bounds = conn.execute(
            text("SELECT MIN(txn_date), MAX(txn_date) FROM transactions")
        ).one()
        min_date, max_date = bounds
        if min_date is None or max_date is None:
            raise RuntimeError("transactions table contains no rows")

        current = date(min_date.year, min_date.month, 1)
        last_month = date(max_date.year, max_date.month, 1)
        month_number = 0

        while current <= last_month:
            following = next_month(current)
            month_number += 1
            print(
                f"Building analytics_daily batch {month_number}: {current} to {following}...",
                flush=True,
            )
            conn.execute(
                text("""
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
                    WHERE t.txn_date >= :start_date
                      AND t.txn_date < :end_date
                    GROUP BY 1,2,3,4,5,6
                """),
                {"start_date": current, "end_date": following},
            )
            conn.commit()
            current = following

    # ------------------------------------------------------------------
    # analytics_customer
    # Build transaction rollups by account-id batches to avoid another
    # million-row GROUP BY that can exhaust a small Render database.
    # ------------------------------------------------------------------
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE analytics_customer"))

    # Keep the temporary rollup and all account batches on the SAME database
    # connection; PostgreSQL temporary tables are connection-local.
    with engine.connect() as conn:
        conn.execute(
            text("""
            CREATE TEMP TABLE tmp_customer_transaction_rollup (
                customer_id INTEGER NOT NULL,
                transaction_count BIGINT NOT NULL,
                total_transaction_value NUMERIC(24,2) NOT NULL
            ) ON COMMIT PRESERVE ROWS
        """)
        )
        conn.commit()

        min_account, max_account = conn.execute(
            text("SELECT MIN(account_id), MAX(account_id) FROM accounts")
        ).one()
        batch_size = 5000
        current_account = int(min_account or 0)
        max_account = int(max_account or -1)
        batch_number = 0

        while current_account <= max_account:
            end_account = current_account + batch_size
            batch_number += 1
            print(
                f"Building customer transaction batch {batch_number}: "
                f"account_id {current_account:,} to {end_account - 1:,}...",
                flush=True,
            )
            conn.execute(
                text("""
                    INSERT INTO tmp_customer_transaction_rollup (
                        customer_id, transaction_count, total_transaction_value
                    )
                    SELECT
                        a.customer_id,
                        COUNT(t.transaction_id),
                        COALESCE(SUM(t.amount), 0)
                    FROM accounts a
                    JOIN transactions t ON t.account_id = a.account_id
                    WHERE a.account_id >= :start_account
                      AND a.account_id < :end_account
                    GROUP BY a.customer_id
                """),
                {"start_account": current_account, "end_account": end_account},
            )
            conn.commit()
            current_account = end_account

        conn.execute(
            text("""
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
                SELECT customer_id,
                       SUM(transaction_count) AS transaction_count,
                       SUM(total_transaction_value) AS total_transaction_value
                FROM tmp_customer_transaction_rollup
                GROUP BY customer_id
            ), ranked AS (
                SELECT c.customer_id, c.annual_income, c.credit_score,
                       COALESCE(ar.account_count, 0) AS account_count,
                       COALESCE(ar.total_balance, 0) AS total_balance,
                       COALESCE(tr.transaction_count, 0) AS transaction_count,
                       COALESCE(tr.total_transaction_value, 0) AS total_transaction_value,
                       CASE
                           WHEN COALESCE(tr.transaction_count, 0) > 0
                           THEN COALESCE(tr.total_transaction_value, 0) / tr.transaction_count
                           ELSE 0
                       END AS average_transaction_value
                FROM customers c
                LEFT JOIN account_rollup ar ON ar.customer_id = c.customer_id
                LEFT JOIN transaction_rollup tr ON tr.customer_id = c.customer_id
            )
            SELECT *,
                   RANK() OVER (ORDER BY total_transaction_value DESC) AS transaction_value_rank
            FROM ranked
        """)
        )
        conn.commit()

    # Recreate secondary indexes only after the data is loaded.
    with engine.begin() as conn:
        conn.execute(text("ANALYZE analytics_daily"))
        conn.execute(text("ANALYZE analytics_customer"))
        _recreate_secondary_indexes(conn)
        conn.execute(text("ANALYZE analytics_daily"))
        conn.execute(text("ANALYZE analytics_customer"))
        daily_count = conn.execute(
            text("SELECT COUNT(*) FROM analytics_daily")
        ).scalar_one()
        customer_count = conn.execute(
            text("SELECT COUNT(*) FROM analytics_customer")
        ).scalar_one()
        print(f"analytics_daily rows: {daily_count:,}")
        print(f"analytics_customer rows: {customer_count:,}")
        print("Analytics serving tables refreshed successfully.")

    engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    url = args.database_url or os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    build(url)
