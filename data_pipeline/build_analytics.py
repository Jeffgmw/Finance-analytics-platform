"""Build compact serving tables for fast dashboard reads."""

import argparse
import os
from datetime import date

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from data_pipeline.config import ROOT

load_dotenv()
ANALYTICS_SCHEMA = (ROOT / "sql" / "analytics_schema.sql").read_text()


def sqlalchemy_url(url: str) -> str:
    return (
        url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql://")
        else url
    )


def next_month(d: date) -> date:
    return date(d.year + 1, 1, 1) if d.month == 12 else date(d.year, d.month + 1, 1)


THREAT = """CASE
    WHEN t.amount >= 100000 OR (t.txn_type='Withdrawal' AND t.amount>=50000)
         OR (t.channel='UPI' AND t.amount>=25000) THEN 'High'
    WHEN t.amount >= 10000 OR t.txn_type='Withdrawal' OR t.channel='UPI' THEN 'Medium'
    ELSE 'Low' END"""


def build(database_url: str) -> None:
    engine = create_engine(
        sqlalchemy_url(database_url),
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        connect_args={"connect_timeout": 30},
    )
    statements = [s.strip() for s in ANALYTICS_SCHEMA.split(";") if s.strip()]
    with engine.begin() as conn:
        # Remove the previous high-cardinality date x dimension serving table.
        # It is no longer used by the API and can consume substantial disk/memory.
        conn.execute(text("DROP TABLE IF EXISTS analytics_daily"))
        for s in statements:
            conn.exec_driver_sql(s)
        conn.execute(
            text("""TRUNCATE TABLE analytics_daily_summary,
            analytics_dimension_summary, analytics_customer,
            analytics_account_summary""")
        )

    with engine.connect() as conn:
        min_date, max_date = conn.execute(
            text("SELECT MIN(txn_date),MAX(txn_date) FROM transactions")
        ).one()
        if min_date is None:
            raise RuntimeError("transactions table contains no rows")
        current = date(min_date.year, min_date.month, 1)
        last = date(max_date.year, max_date.month, 1)
        n = 0
        while current <= last:
            following = next_month(current)
            n += 1
            print(
                f"Building analytics batch {n}: {current} to {following}...", flush=True
            )
            params = {"start_date": current, "end_date": following}
            base = """FROM transactions t JOIN accounts a ON a.account_id=t.account_id
                    WHERE t.txn_date>=:start_date AND t.txn_date<:end_date"""
            conn.execute(
                text(f"""INSERT INTO analytics_daily_summary
                (txn_date,transaction_count,total_value,high_count,high_value)
                SELECT t.txn_date,COUNT(*),COALESCE(SUM(t.amount),0),
                       COUNT(*) FILTER (WHERE {THREAT}='High'),
                       COALESCE(SUM(t.amount) FILTER (WHERE {THREAT}='High'),0)
                {base} GROUP BY t.txn_date"""),
                params,
            )
            conn.commit()

            # One grouped scan creates all five dimension summaries for this month.
            q = f"""WITH base AS (
                SELECT COALESCE(t.txn_type,'Unknown') txn_type,
                       COALESCE(t.channel,'Unknown') channel,
                       COALESCE(t.merchant_category,'Unknown') merchant_category,
                       COALESCE(a.account_type,'Unknown') account_type,
                       {THREAT} threat_level, t.amount
                {base}
            ), grouped AS (
                SELECT 'txn_type' dimension_name, txn_type dimension_value,
                       COUNT(*) transaction_count, SUM(amount) total_value,
                       COUNT(*) FILTER(WHERE threat_level='High') high_count,
                       COALESCE(SUM(amount) FILTER(WHERE threat_level='High'),0) high_value
                FROM base GROUP BY txn_type
                UNION ALL
                SELECT 'channel',channel,COUNT(*),SUM(amount),
                       COUNT(*) FILTER(WHERE threat_level='High'),
                       COALESCE(SUM(amount) FILTER(WHERE threat_level='High'),0)
                FROM base GROUP BY channel
                UNION ALL
                SELECT 'merchant_category',merchant_category,COUNT(*),SUM(amount),
                       COUNT(*) FILTER(WHERE threat_level='High'),
                       COALESCE(SUM(amount) FILTER(WHERE threat_level='High'),0)
                FROM base GROUP BY merchant_category
                UNION ALL
                SELECT 'account_type',account_type,COUNT(*),SUM(amount),
                       COUNT(*) FILTER(WHERE threat_level='High'),
                       COALESCE(SUM(amount) FILTER(WHERE threat_level='High'),0)
                FROM base GROUP BY account_type
                UNION ALL
                SELECT 'threat_level',threat_level,COUNT(*),SUM(amount),
                       COUNT(*) FILTER(WHERE threat_level='High'),
                       COALESCE(SUM(amount) FILTER(WHERE threat_level='High'),0)
                FROM base GROUP BY threat_level
            )
            INSERT INTO analytics_dimension_summary
              (dimension_name,dimension_value,transaction_count,total_value,high_count,high_value)
            SELECT dimension_name,dimension_value,SUM(transaction_count),SUM(total_value),
                   SUM(high_count),SUM(high_value)
            FROM grouped GROUP BY dimension_name,dimension_value
            ON CONFLICT(dimension_name,dimension_value) DO UPDATE SET
              transaction_count=analytics_dimension_summary.transaction_count+EXCLUDED.transaction_count,
              total_value=analytics_dimension_summary.total_value+EXCLUDED.total_value,
              high_count=analytics_dimension_summary.high_count+EXCLUDED.high_count,
              high_value=analytics_dimension_summary.high_value+EXCLUDED.high_value"""
            conn.execute(text(q), params)
            conn.commit()
            current = following

    with engine.begin() as conn:
        conn.execute(
            text("""CREATE TEMP TABLE tmp_customer_transaction_rollup(
            customer_id INTEGER NOT NULL, transaction_count BIGINT NOT NULL,
            total_transaction_value NUMERIC(24,2) NOT NULL) ON COMMIT DROP""")
        )
        mn, mx = conn.execute(
            text("SELECT MIN(account_id),MAX(account_id) FROM accounts")
        ).one()
        start = int(mn or 0)
        mx = int(mx or -1)
        size = 2000
        while start <= mx:
            end = start + size
            conn.execute(
                text("""INSERT INTO tmp_customer_transaction_rollup
                SELECT a.customer_id,COUNT(t.transaction_id),COALESCE(SUM(t.amount),0)
                FROM accounts a JOIN transactions t ON t.account_id=a.account_id
                WHERE a.account_id>=:s AND a.account_id<:e GROUP BY a.customer_id"""),
                {"s": start, "e": end},
            )
            start = end
        conn.execute(
            text("""INSERT INTO analytics_customer
            (customer_id,annual_income,credit_score,account_count,total_balance,
             transaction_count,total_transaction_value,average_transaction_value,transaction_value_rank)
            WITH ar AS (SELECT customer_id,COUNT(*) account_count,COALESCE(SUM(balance),0) total_balance
                        FROM accounts GROUP BY customer_id),
            tr AS (SELECT customer_id,SUM(transaction_count) transaction_count,
                          SUM(total_transaction_value) total_transaction_value
                   FROM tmp_customer_transaction_rollup GROUP BY customer_id),
            ranked AS (
              SELECT c.customer_id,c.annual_income,c.credit_score,
                     COALESCE(ar.account_count,0) account_count,COALESCE(ar.total_balance,0) total_balance,
                     COALESCE(tr.transaction_count,0) transaction_count,
                     COALESCE(tr.total_transaction_value,0) total_transaction_value,
                     CASE WHEN COALESCE(tr.transaction_count,0)>0
                          THEN COALESCE(tr.total_transaction_value,0)/tr.transaction_count ELSE 0 END average_transaction_value
              FROM customers c LEFT JOIN ar ON ar.customer_id=c.customer_id
              LEFT JOIN tr ON tr.customer_id=c.customer_id)
            SELECT *,RANK() OVER(ORDER BY total_transaction_value DESC) FROM ranked""")
        )

        conn.execute(
            text("""INSERT INTO analytics_account_summary
            (account_type,status,account_count,total_balance,average_balance)
            SELECT account_type,status,COUNT(*),COALESCE(SUM(balance),0),COALESCE(AVG(balance),0)
            FROM accounts GROUP BY account_type,status""")
        )

    with engine.begin() as conn:
        for table in (
            "analytics_daily_summary",
            "analytics_dimension_summary",
            "analytics_customer",
            "analytics_account_summary",
        ):
            conn.execute(text(f"ANALYZE {table}"))
        print("Serving tables refreshed successfully.", flush=True)
    engine.dispose()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--database-url", default=None)
    args = p.parse_args()
    url = args.database_url or os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    build(url)
