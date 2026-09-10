from sqlalchemy import text
from sqlalchemy.orm import Session


def _where(f):
    clauses, params = [], {}
    if f.start_date:
        clauses.append("t.txn_date >= :start_date")
        params["start_date"] = f.start_date
    if f.end_date:
        clauses.append("t.txn_date <= :end_date")
        params["end_date"] = f.end_date
    if f.transaction_type:
        clauses.append("t.txn_type = :transaction_type")
        params["transaction_type"] = f.transaction_type
    if f.channel:
        clauses.append("t.channel = :channel")
        params["channel"] = f.channel
    if f.merchant_category:
        clauses.append("t.merchant_category = :merchant_category")
        params["merchant_category"] = f.merchant_category
    if f.account_type:
        clauses.append("a.account_type = :account_type")
        params["account_type"] = f.account_type
    return (" AND ".join(clauses) if clauses else "TRUE"), params


def customer_summary(db: Session):
    q = text("""WITH account_rollup AS (
        SELECT customer_id, COUNT(*) account_count, COALESCE(SUM(balance),0) total_balance
        FROM accounts GROUP BY customer_id
    )
    SELECT c.customer_id, COALESCE(ar.account_count,0) account_count,
           COALESCE(ar.total_balance,0) total_balance
    FROM customers c LEFT JOIN account_rollup ar ON ar.customer_id=c.customer_id
    ORDER BY total_balance DESC LIMIT 100""")
    return [dict(r._mapping) for r in db.execute(q)]


def account_summary(db: Session):
    q = text("""SELECT a.account_type, a.status, COUNT(*) account_count,
        COALESCE(SUM(a.balance),0) total_balance, COALESCE(AVG(a.balance),0) average_balance
        FROM accounts a GROUP BY a.account_type,a.status ORDER BY total_balance DESC""")
    return [dict(r._mapping) for r in db.execute(q)]


def transaction_summary(db: Session, f):
    where, params = _where(f)
    q = text(f"""SELECT COUNT(*) transaction_count, COALESCE(SUM(t.amount),0) total_value,
        COALESCE(AVG(t.amount),0) average_value FROM transactions t
        JOIN accounts a ON a.account_id=t.account_id WHERE {where}""")
    return dict(db.execute(q, params).mappings().one())


def customer_360(db: Session, f):
    where, params = _where(f)
    q = text(f"""WITH filtered_transactions AS (
        SELECT t.* FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE {where}
    ), account_rollup AS (
        SELECT customer_id, COUNT(*) account_count, COALESCE(SUM(balance),0) total_balance FROM accounts GROUP BY customer_id
    ), transaction_rollup AS (
        SELECT a.customer_id, COUNT(ft.transaction_id) transaction_count,
               COALESCE(SUM(ft.amount),0) total_transaction_value,
               COALESCE(AVG(ft.amount),0) average_transaction_value
        FROM accounts a LEFT JOIN filtered_transactions ft ON ft.account_id=a.account_id
        GROUP BY a.customer_id
    )
    SELECT c.customer_id, c.annual_income, c.credit_score,
           COALESCE(ar.account_count,0) account_count, COALESCE(ar.total_balance,0) total_balance,
           COALESCE(tr.transaction_count,0) transaction_count,
           COALESCE(tr.total_transaction_value,0) total_transaction_value,
           COALESCE(tr.average_transaction_value,0) average_transaction_value,
           RANK() OVER (ORDER BY COALESCE(tr.total_transaction_value,0) DESC) transaction_value_rank
    FROM customers c LEFT JOIN account_rollup ar ON ar.customer_id=c.customer_id
    LEFT JOIN transaction_rollup tr ON tr.customer_id=c.customer_id
    ORDER BY total_transaction_value DESC LIMIT 500""")
    return [dict(r._mapping) for r in db.execute(q, params)]
