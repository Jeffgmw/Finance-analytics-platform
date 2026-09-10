from sqlalchemy import text
from sqlalchemy.orm import Session

from .sql_service import _where


def summary(db: Session, f):
    where, params = _where(f)
    queries = {
        "customers": text("SELECT COUNT(*) FROM customers"),
        "accounts": text("SELECT COUNT(*) FROM accounts"),
        "transactions": text(
            f"SELECT COUNT(*) FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE {where}"
        ),
        "transaction_value": text(
            f"SELECT COALESCE(SUM(t.amount),0) FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE {where}"
        ),
        "channels": text(
            f"SELECT COUNT(DISTINCT t.channel) FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE {where}"
        ),
    }
    return {
        k: db.execute(
            q, params if k in {"transactions", "transaction_value", "channels"} else {}
        ).scalar()
        for k, q in queries.items()
    }


def monthly_transactions(db: Session, f):
    where, params = _where(f)
    q = text(f"""SELECT DATE_TRUNC('month', t.txn_date)::date AS month, COUNT(*) transaction_count,
        COALESCE(SUM(t.amount),0) total_value FROM transactions t JOIN accounts a ON a.account_id=t.account_id
        WHERE {where} GROUP BY 1 ORDER BY 1""")
    return [dict(r._mapping) for r in db.execute(q, params)]


def grouped(db: Session, f, column: str):
    allowed = {
        "txn_type": "t.txn_type",
        "channel": "t.channel",
        "merchant_category": "t.merchant_category",
    }
    expr = allowed[column]
    where, params = _where(f)
    q = text(f"""SELECT {expr} category, COUNT(*) transaction_count, COALESCE(SUM(t.amount),0) total_value
        FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE {where}
        GROUP BY {expr} ORDER BY total_value DESC""")
    return [dict(r._mapping) for r in db.execute(q, params)]


def income_activity(db: Session, f):
    where, params = _where(f)
    q = text(f"""SELECT c.customer_id, c.annual_income, COUNT(t.transaction_id) transaction_count,
        COALESCE(SUM(t.amount),0) transaction_value
        FROM customers c JOIN accounts a ON a.customer_id=c.customer_id
        LEFT JOIN transactions t ON t.account_id=a.account_id
        WHERE {where} GROUP BY c.customer_id,c.annual_income ORDER BY c.annual_income""")
    return [dict(r._mapping) for r in db.execute(q, params)]


def fraud_overview(db: Session, f):
    """Explainable risk proxy; supplied data contains no ground-truth fraud label."""
    where, params = _where(f)
    risk_case = """
        CASE
          WHEN (t.amount >= 100000)
            OR (t.txn_type = 'Withdrawal' AND t.amount >= 50000)
            OR (t.channel = 'UPI' AND t.amount >= 25000) THEN 'High'
          WHEN (t.amount >= 10000)
            OR (t.txn_type = 'Withdrawal')
            OR (t.channel = 'UPI') THEN 'Medium'
          ELSE 'Low'
        END
    """
    summary = dict(
        db.execute(
            text(f"""
        WITH filtered AS (SELECT t.amount,t.channel,{risk_case} AS threat_level FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE {where})
        SELECT COUNT(*) transaction_count, COUNT(DISTINCT channel) channel_count, COALESCE(SUM(amount),0) transaction_value, COUNT(*) 
        FILTER (WHERE threat_level='High') high_count, COUNT(*) 
        FILTER (WHERE threat_level='Medium') medium_count, COUNT(*) 
        FILTER (WHERE threat_level='Low') low_count,
        COALESCE(SUM(amount) FILTER (WHERE threat_level='High'),0) high_value, COALESCE(SUM(amount) 
        FILTER (WHERE threat_level='Medium'),0) medium_value, COALESCE(SUM(amount) 
        FILTER (WHERE threat_level='Low'),0) low_value FROM filtered
    """),
            params,
        )
        .mappings()
        .one()
    )
    daily = (
        db.execute(
            text(f"""
        WITH filtered AS (SELECT t.txn_date,t.amount,{risk_case} AS threat_level FROM transactions t JOIN accounts a ON a.account_id=t.account_id 
        WHERE {where})
        SELECT txn_date,COUNT(*) transaction_count,COALESCE(SUM(amount),0) transaction_value,COUNT(*) 
        FILTER (WHERE threat_level='High') high_count,COALESCE(SUM(amount) 
        FILTER (WHERE threat_level='High'),0) high_value FROM filtered GROUP BY txn_date ORDER BY txn_date
    """),
            params,
        )
        .mappings()
        .all()
    )
    channels = (
        db.execute(
            text(f"""
        WITH filtered AS (SELECT t.channel,t.amount,{risk_case} AS threat_level FROM transactions t JOIN accounts a ON a.account_id=t.account_id 
        WHERE {where})
        SELECT COALESCE(channel,'Unknown') channel,COUNT(*) transaction_count,COALESCE(SUM(amount),0) transaction_value,COUNT(*) 
        FILTER (WHERE threat_level='High') high_count,COALESCE(SUM(amount) 
        FILTER (WHERE threat_level='High'),0) high_value FROM filtered GROUP BY channel ORDER BY transaction_value DESC
    """),
            params,
        )
        .mappings()
        .all()
    )
    threats = [
        {
            "threat_level": "High",
            "transaction_count": summary["high_count"],
            "transaction_value": summary["high_value"],
        },
        {
            "threat_level": "Medium",
            "transaction_count": summary["medium_count"],
            "transaction_value": summary["medium_value"],
        },
        {
            "threat_level": "Low",
            "transaction_count": summary["low_count"],
            "transaction_value": summary["low_value"],
        },
    ]
    return {
        "summary": summary,
        "threat_levels": threats,
        "daily": [dict(x) for x in daily],
        "channels": [dict(x) for x in channels],
    }


def filter_options(db: Session):
    """Return all dashboard filter choices in one database round trip."""
    queries = {
        "transaction_types": "SELECT DISTINCT txn_type AS value FROM transactions WHERE txn_type IS NOT NULL ORDER BY 1",
        "channels": "SELECT DISTINCT channel AS value FROM transactions WHERE channel IS NOT NULL ORDER BY 1",
        "merchant_categories": "SELECT DISTINCT merchant_category AS value FROM transactions WHERE merchant_category IS NOT NULL ORDER BY 1",
        "account_types": "SELECT DISTINCT account_type AS value FROM accounts WHERE account_type IS NOT NULL ORDER BY 1",
    }
    return {
        name: [r.value for r in db.execute(text(sql))] for name, sql in queries.items()
    }
