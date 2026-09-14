from sqlalchemy import text
from sqlalchemy.orm import Session


def _where(f):
    clauses = []
    params = {}
    for field, col in [
        ("start_date", "t.txn_date >= :start_date"),
        ("end_date", "t.txn_date <= :end_date"),
        ("transaction_type", "t.txn_type = :transaction_type"),
        ("channel", "t.channel = :channel"),
        ("merchant_category", "t.merchant_category = :merchant_category"),
        ("account_type", "a.account_type = :account_type"),
    ]:
        val = getattr(f, field)
        if val:
            clauses.append(col)
            params[field] = val
    return (" AND ".join(clauses) if clauses else "TRUE"), params


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


def customer_summary(db):
    q = text("""SELECT customer_id,account_count,total_balance FROM analytics_customer
              ORDER BY total_balance DESC LIMIT 100""")
    return [dict(r._mapping) for r in db.execute(q)]


def account_summary(db):
    q = text("""SELECT account_type,status,account_count,total_balance,average_balance
              FROM analytics_account_summary ORDER BY total_balance DESC""")
    return [dict(r._mapping) for r in db.execute(q)]


def transaction_summary(db, f):
    if not _has_filters(f):
        q = text("""SELECT COALESCE(SUM(transaction_count),0) transaction_count,
                         COALESCE(SUM(total_value),0) total_value,
                         COALESCE(SUM(total_value)/NULLIF(SUM(transaction_count),0),0) average_value
                  FROM analytics_daily_summary""")
        return dict(db.execute(q).mappings().one())
    where, params = _where(f)
    return dict(
        db.execute(
            text(f"""SELECT COUNT(*) transaction_count,COALESCE(SUM(t.amount),0) total_value,
        COALESCE(AVG(t.amount),0) average_value FROM transactions t JOIN accounts a ON a.account_id=t.account_id
        WHERE {where}"""),
            params,
        )
        .mappings()
        .one()
    )


def customer_360(db, f):
    if not _has_filters(f):
        q = text("""SELECT customer_id,annual_income,credit_score,account_count,total_balance,
                         transaction_count,total_transaction_value,average_transaction_value,transaction_value_rank
                  FROM analytics_customer ORDER BY total_transaction_value DESC LIMIT 500""")
        return [dict(r._mapping) for r in db.execute(q)]
    where, params = _where(f)
    q = text(f"""WITH tr AS (
        SELECT a.customer_id,COUNT(t.transaction_id) transaction_count,
               COALESCE(SUM(t.amount),0) total_transaction_value,COALESCE(AVG(t.amount),0) average_transaction_value
        FROM accounts a LEFT JOIN transactions t ON t.account_id=a.account_id
        WHERE {where} GROUP BY a.customer_id),
      ar AS (SELECT customer_id,COUNT(*) account_count,COALESCE(SUM(balance),0) total_balance
             FROM accounts GROUP BY customer_id)
      SELECT c.customer_id,c.annual_income,c.credit_score,COALESCE(ar.account_count,0) account_count,
             COALESCE(ar.total_balance,0) total_balance,COALESCE(tr.transaction_count,0) transaction_count,
             COALESCE(tr.total_transaction_value,0) total_transaction_value,
             COALESCE(tr.average_transaction_value,0) average_transaction_value,
             RANK() OVER(ORDER BY COALESCE(tr.total_transaction_value,0) DESC) transaction_value_rank
      FROM customers c LEFT JOIN ar ON ar.customer_id=c.customer_id LEFT JOIN tr ON tr.customer_id=c.customer_id
      ORDER BY total_transaction_value DESC LIMIT 500""")
    return [dict(r._mapping) for r in db.execute(q, params)]


def sql_dashboard(db, f):
    # The shared dashboard summary is supplied by analytics_service.dashboard().
    # Do not return a second `summary` object here: the SQL endpoint merges this
    # result with the shared dashboard payload, and returning another summary
    # would overwrite the KPI fields (customers, accounts, transaction_value,
    # channels) with the smaller transaction-summary shape.
    return {"account_summary": account_summary(db), "customer_360": customer_360(db, f)}
