from sqlalchemy import text
from sqlalchemy.orm import Session

from .sql_service import _where


def _has_filters(f):
    return any(
        [
            f.start_date,
            f.end_date,
            f.transaction_type,
            f.channel,
            f.merchant_category,
            f.account_type,
        ]
    )


def _summary_from_analytics(db: Session, f):
    clauses, params = [], {}
    if f.start_date:
        clauses.append("txn_date >= :start_date")
        params["start_date"] = f.start_date
    if f.end_date:
        clauses.append("txn_date <= :end_date")
        params["end_date"] = f.end_date
    if f.transaction_type:
        clauses.append("txn_type = :transaction_type")
        params["transaction_type"] = f.transaction_type
    if f.channel:
        clauses.append("channel = :channel")
        params["channel"] = f.channel
    if f.merchant_category:
        clauses.append("merchant_category = :merchant_category")
        params["merchant_category"] = f.merchant_category
    if f.account_type:
        clauses.append("account_type = :account_type")
        params["account_type"] = f.account_type
    where = " AND ".join(clauses) if clauses else "TRUE"
    return dict(
        db.execute(
            text(f"""
        SELECT
            (SELECT COUNT(*) FROM customers) AS customers,
            (SELECT COUNT(*) FROM accounts) AS accounts,
            COALESCE(SUM(transaction_count), 0) AS transactions,
            COALESCE(SUM(total_value), 0) AS transaction_value,
            COUNT(DISTINCT channel) FILTER (WHERE channel IS NOT NULL) AS channels
        FROM analytics_daily
        WHERE {where}
    """),
            params,
        )
        .mappings()
        .one()
    )


def summary(db: Session, f):
    if not _has_filters(f):
        return _summary_from_analytics(db, f)
    # Filtered queries still use the raw tables so every dashboard filter remains exact.
    where, params = _where(f)
    q = text(f"""
        SELECT
            (SELECT COUNT(*) FROM customers) AS customers,
            (SELECT COUNT(*) FROM accounts) AS accounts,
            COUNT(*) AS transactions,
            COALESCE(SUM(t.amount),0) AS transaction_value,
            COUNT(DISTINCT t.channel) AS channels
        FROM transactions t
        JOIN accounts a ON a.account_id=t.account_id
        WHERE {where}
    """)
    return dict(db.execute(q, params).mappings().one())


def monthly_transactions(db: Session, f):
    if not _has_filters(f):
        q = text("""
            SELECT DATE_TRUNC('month', txn_date)::date AS month,
                   SUM(transaction_count) AS transaction_count,
                   COALESCE(SUM(total_value),0) AS total_value
            FROM analytics_daily
            GROUP BY 1 ORDER BY 1
        """)
        return [dict(r._mapping) for r in db.execute(q)]
    clauses, params = _analytics_filter(f)
    q = text(f"""
        SELECT DATE_TRUNC('month', txn_date)::date AS month,
               SUM(transaction_count) AS transaction_count,
               COALESCE(SUM(total_value),0) AS total_value
        FROM analytics_daily
        WHERE {clauses}
        GROUP BY 1 ORDER BY 1
    """)
    return [dict(r._mapping) for r in db.execute(q, params)]


def _analytics_filter(f):
    clauses, params = [], {}
    if f.start_date:
        clauses.append("txn_date >= :start_date")
        params["start_date"] = f.start_date
    if f.end_date:
        clauses.append("txn_date <= :end_date")
        params["end_date"] = f.end_date
    if f.transaction_type:
        clauses.append("txn_type = :transaction_type")
        params["transaction_type"] = f.transaction_type
    if f.channel:
        clauses.append("channel = :channel")
        params["channel"] = f.channel
    if f.merchant_category:
        clauses.append("merchant_category = :merchant_category")
        params["merchant_category"] = f.merchant_category
    if f.account_type:
        clauses.append("account_type = :account_type")
        params["account_type"] = f.account_type
    return (" AND ".join(clauses) if clauses else "TRUE"), params


def grouped(db: Session, f, column: str):
    allowed = {
        "txn_type": "txn_type",
        "channel": "channel",
        "merchant_category": "merchant_category",
    }
    expr = allowed[column]
    clauses, params = _analytics_filter(f)
    q = text(f"""
        SELECT COALESCE({expr}, 'Unknown') AS category,
               SUM(transaction_count) AS transaction_count,
               COALESCE(SUM(total_value),0) AS total_value
        FROM analytics_daily
        WHERE {clauses}
        GROUP BY {expr}
        ORDER BY total_value DESC
    """)
    return [dict(r._mapping) for r in db.execute(q, params)]


def income_activity(db: Session, f):
    if not _has_filters(f):
        q = text("""
            SELECT customer_id, annual_income, transaction_count,
                   total_transaction_value AS transaction_value
            FROM analytics_customer
            WHERE transaction_count > 0
            ORDER BY annual_income
            LIMIT 5000
        """)
        return [dict(r._mapping) for r in db.execute(q)]
    where, params = _where(f)
    q = text(f"""
        SELECT c.customer_id, c.annual_income, COUNT(t.transaction_id) transaction_count,
               COALESCE(SUM(t.amount),0) transaction_value
        FROM customers c
        JOIN accounts a ON a.customer_id=c.customer_id
        LEFT JOIN transactions t ON t.account_id=a.account_id
        WHERE {where}
        GROUP BY c.customer_id,c.annual_income
        ORDER BY c.annual_income
        LIMIT 5000
    """)
    return [dict(r._mapping) for r in db.execute(q, params)]


def fraud_overview(db: Session, f):
    """Explainable risk proxy; supplied data contains no ground-truth fraud label."""
    clauses, params = _analytics_filter(f)
    q = text(f"""
        WITH agg AS (
            SELECT threat_level, channel, txn_date,
                   SUM(transaction_count) AS transaction_count,
                   SUM(total_value) AS transaction_value,
                   SUM(high_count) AS high_count,
                   SUM(high_value) AS high_value
            FROM analytics_daily
            WHERE {clauses}
            GROUP BY threat_level, channel, txn_date
        ), overall AS (
            SELECT
                COALESCE(SUM(transaction_count),0) transaction_count,
                COUNT(DISTINCT channel) channel_count,
                COALESCE(SUM(transaction_value),0) transaction_value,
                COALESCE(SUM(transaction_count) FILTER (WHERE threat_level='High'),0) high_count,
                COALESCE(SUM(transaction_count) FILTER (WHERE threat_level='Medium'),0) medium_count,
                COALESCE(SUM(transaction_count) FILTER (WHERE threat_level='Low'),0) low_count,
                COALESCE(SUM(transaction_value) FILTER (WHERE threat_level='High'),0) high_value,
                COALESCE(SUM(transaction_value) FILTER (WHERE threat_level='Medium'),0) medium_value,
                COALESCE(SUM(transaction_value) FILTER (WHERE threat_level='Low'),0) low_value
            FROM agg
        ), daily AS (
            SELECT txn_date,
                   SUM(transaction_count) transaction_count,
                   SUM(transaction_value) transaction_value,
                   SUM(high_count) high_count,
                   SUM(high_value) high_value
            FROM agg GROUP BY txn_date ORDER BY txn_date
        ), channels AS (
            SELECT channel,
                   SUM(transaction_count) transaction_count,
                   SUM(transaction_value) transaction_value,
                   SUM(high_count) high_count,
                   SUM(high_value) high_value
            FROM agg GROUP BY channel ORDER BY transaction_value DESC
        )
        SELECT
            (SELECT row_to_json(overall) FROM overall) AS summary,
            (SELECT json_agg(json_build_object(
                'threat_level', threat_level,
                'transaction_count', transaction_count,
                'transaction_value', transaction_value
            ) ORDER BY CASE threat_level WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END)
             FROM (
                SELECT threat_level, SUM(transaction_count) transaction_count,
                       SUM(transaction_value) transaction_value
                FROM agg GROUP BY threat_level
             ) x) AS threat_levels,
            (SELECT json_agg(row_to_json(daily)) FROM daily) AS daily,
            (SELECT json_agg(row_to_json(channels)) FROM channels) AS channels
    """)
    row = db.execute(q, params).mappings().one()
    return {
        "summary": row["summary"] or {},
        "threat_levels": row["threat_levels"] or [],
        "daily": row["daily"] or [],
        "channels": row["channels"] or [],
    }


def dashboard(db: Session, f):
    """Single core dashboard request to reduce HTTP/database round trips."""
    return {
        "summary": summary(db, f),
        "monthly": monthly_transactions(db, f),
        "fraud": fraud_overview(db, f),
    }


def filter_options(db: Session):
    queries = {
        "transaction_types": "SELECT DISTINCT txn_type AS value FROM analytics_daily WHERE txn_type IS NOT NULL ORDER BY 1",
        "channels": "SELECT DISTINCT channel AS value FROM analytics_daily WHERE channel IS NOT NULL ORDER BY 1",
        "merchant_categories": "SELECT DISTINCT merchant_category AS value FROM analytics_daily WHERE merchant_category IS NOT NULL ORDER BY 1",
        "account_types": "SELECT DISTINCT account_type AS value FROM analytics_daily WHERE account_type IS NOT NULL ORDER BY 1",
    }
    return {
        name: [r.value for r in db.execute(text(sql))] for name, sql in queries.items()
    }
