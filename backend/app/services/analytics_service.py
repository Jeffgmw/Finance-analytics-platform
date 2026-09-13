from sqlalchemy import text

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


def _analytics_filter(f):
    clauses = []
    params = {}
    for field, col in [
        ("start_date", "txn_date >= :start_date"),
        ("end_date", "txn_date <= :end_date"),
        ("transaction_type", "txn_type = :transaction_type"),
        ("channel", "channel = :channel"),
        ("merchant_category", "merchant_category = :merchant_category"),
        ("account_type", "account_type = :account_type"),
    ]:
        val = getattr(f, field)
        if val:
            clauses.append(col)
            params[field] = val
    return (" AND ".join(clauses) if clauses else "TRUE"), params


def summary(db, f):
    if not _has_filters(f):
        return dict(
            db.execute(
                text("""SELECT
            (SELECT COUNT(*) FROM customers) customers,
            (SELECT COUNT(*) FROM accounts) accounts,
            COALESCE(SUM(transaction_count),0) transactions,
            COALESCE(SUM(total_value),0) transaction_value,
            (SELECT COUNT(*) FROM analytics_dimension_summary WHERE dimension_name='channel') channels
            FROM analytics_daily_summary""")
            )
            .mappings()
            .one()
        )
    where, params = _where(f)
    return dict(
        db.execute(
            text(f"""SELECT (SELECT COUNT(*) FROM customers) customers,
        (SELECT COUNT(*) FROM accounts) accounts,COUNT(*) transactions,
        COALESCE(SUM(t.amount),0) transaction_value,COUNT(DISTINCT t.channel) channels
        FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE {where}"""),
            params,
        )
        .mappings()
        .one()
    )


def monthly_transactions(db, f):
    if not _has_filters(f):
        q = text("""SELECT DATE_TRUNC('month',txn_date)::date AS month,SUM(transaction_count) transaction_count,
                  SUM(total_value) total_value FROM analytics_daily_summary GROUP BY 1 ORDER BY 1""")
        return [dict(r._mapping) for r in db.execute(q)]
    clauses, params = _analytics_filter(f)
    q = text(f"""SELECT DATE_TRUNC('month',txn_date)::date month,SUM(transaction_count) transaction_count,
               SUM(total_value) total_value FROM analytics_daily_summary WHERE {clauses}
               GROUP BY 1 ORDER BY 1""")
    # A filtered request is exact only for dimensions represented by the serving
    # grain; otherwise the raw fallback in grouped/summary is used.
    if any([f.transaction_type, f.channel, f.merchant_category, f.account_type]):
        where, params = _where(f)
        q = text(f"""SELECT DATE_TRUNC('month',t.txn_date)::date month,COUNT(*) transaction_count,
                   COALESCE(SUM(t.amount),0) total_value FROM transactions t
                   JOIN accounts a ON a.account_id=t.account_id WHERE {where}
                   GROUP BY 1 ORDER BY 1""")
    return [dict(r._mapping) for r in db.execute(q, params)]


def grouped(db, f, column):
    allowed = {
        "txn_type": "txn_type",
        "channel": "channel",
        "merchant_category": "merchant_category",
    }
    expr = allowed[column]
    if not _has_filters(f):
        q = text("""SELECT dimension_value category,transaction_count,total_value
                   FROM analytics_dimension_summary
                   WHERE dimension_name=:dimension_name ORDER BY total_value DESC""")
        return [dict(r._mapping) for r in db.execute(q, {"dimension_name": column})]
    where, params = _where(f)
    q = text(f"""SELECT COALESCE(t.{expr},'Unknown') category,COUNT(*) transaction_count,
               COALESCE(SUM(t.amount),0) total_value FROM transactions t
               JOIN accounts a ON a.account_id=t.account_id WHERE {where}
               GROUP BY t.{expr} ORDER BY total_value DESC""")
    return [dict(r._mapping) for r in db.execute(q, params)]


def income_activity(db, f):
    if not _has_filters(f):
        q = text("""SELECT customer_id,annual_income,transaction_count,
                  total_transaction_value transaction_value FROM analytics_customer
                  WHERE transaction_count>0 ORDER BY annual_income LIMIT 5000""")
        return [dict(r._mapping) for r in db.execute(q)]
    where, params = _where(f)
    q = text(f"""SELECT c.customer_id,c.annual_income,COUNT(t.transaction_id) transaction_count,
               COALESCE(SUM(t.amount),0) transaction_value FROM customers c
               JOIN accounts a ON a.customer_id=c.customer_id LEFT JOIN transactions t ON t.account_id=a.account_id
               WHERE {where} GROUP BY c.customer_id,c.annual_income ORDER BY c.annual_income LIMIT 5000""")
    return [dict(r._mapping) for r in db.execute(q, params)]


def fraud_overview(db, f):
    if not _has_filters(f):
        overall = (
            db.execute(
                text("""SELECT COALESCE(SUM(transaction_count),0) transaction_count,
            (SELECT COUNT(*) FROM analytics_dimension_summary WHERE dimension_name='channel') channel_count,
            COALESCE(SUM(total_value),0) transaction_value,
            COALESCE(SUM(high_count),0) high_count FROM analytics_daily_summary""")
            )
            .mappings()
            .one()
        )
        threats = [
            dict(r._mapping)
            for r in db.execute(
                text("""SELECT dimension_value threat_level,
            transaction_count,total_value FROM analytics_dimension_summary
            WHERE dimension_name='threat_level'
            ORDER BY CASE dimension_value WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END""")
            )
        ]
        channels = [
            dict(r._mapping)
            for r in db.execute(
                text("""SELECT dimension_value channel,
            transaction_count, total_value, high_count, high_value FROM analytics_dimension_summary
            WHERE dimension_name='channel' ORDER BY total_value DESC""")
            )
        ]
        daily = [
            dict(r._mapping)
            for r in db.execute(
                text("""SELECT txn_date,transaction_count,
            total_value transaction_value,high_count,high_value FROM analytics_daily_summary ORDER BY txn_date""")
            )
        ]
        return {
            "summary": dict(overall),
            "threat_levels": threats,
            "daily": daily,
            "channels": channels,
        }
    # Exact filtered fraud view.
    where, params = _analytics_filter(f)
    q = text(f"""WITH agg AS (
      SELECT t.txn_date,COALESCE(t.channel,'Unknown') channel,{_threat_sql()} threat_level,
             COUNT(*) transaction_count,COALESCE(SUM(t.amount),0) transaction_value,
             COUNT(*) FILTER(WHERE {_threat_sql()}='High') high_count,
             COALESCE(SUM(t.amount) FILTER(WHERE {_threat_sql()}='High'),0) high_value
      FROM transactions t JOIN accounts a ON a.account_id=t.account_id WHERE {where}
      GROUP BY t.txn_date,t.channel,{_threat_sql()})
      SELECT json_agg(json_build_object('txn_date',txn_date,'transaction_count',transaction_count,
             'transaction_value',transaction_value,'high_count',high_count,'high_value',high_value)
             ORDER BY txn_date) daily FROM agg""")
    daily = db.execute(q, params).scalar_one() or []

    # Keep filtered threat/channel queries simple and exact.
    def simple(group):
        q = text(f"""SELECT COALESCE({group},'Unknown') category,COUNT(*) transaction_count,
                   COALESCE(SUM(t.amount),0) transaction_value,
                   COUNT(*) FILTER(WHERE {_threat_sql()}='High') high_count
                   FROM transactions t JOIN accounts a ON a.account_id=t.account_id
                   WHERE {where} GROUP BY {group} ORDER BY transaction_value DESC""")
        return [dict(r._mapping) for r in db.execute(q, params)]

    threats = simple(_threat_sql())
    channels = simple("t.channel")
    total = sum(x["transaction_count"] for x in daily)
    value = sum((x["transaction_value"] or 0) for x in daily)
    high = sum(x["high_count"] for x in daily)
    return {
        "summary": {
            "transaction_count": total,
            "channel_count": len(channels),
            "transaction_value": value,
            "high_count": high,
        },
        "threat_levels": [
            {
                "threat_level": x["category"],
                "transaction_count": x["transaction_count"],
                "transaction_value": x["transaction_value"],
            }
            for x in threats
        ],
        "daily": daily,
        "channels": [
            {
                "channel": x["category"],
                "transaction_count": x["transaction_count"],
                "transaction_value": x["transaction_value"],
                "high_count": x["high_count"],
            }
            for x in channels
        ],
    }


def _threat_sql():
    return """CASE WHEN t.amount>=100000 OR (t.txn_type='Withdrawal' AND t.amount>=50000)
    OR (t.channel='UPI' AND t.amount>=25000) THEN 'High'
    WHEN t.amount>=10000 OR t.txn_type='Withdrawal' OR t.channel='UPI' THEN 'Medium'
    ELSE 'Low' END"""


def filter_options(db):
    def vals(name):
        return [
            r[0]
            for r in db.execute(
                text("""SELECT dimension_value FROM analytics_dimension_summary
            WHERE dimension_name=:n ORDER BY dimension_value"""),
                {"n": name},
            ).all()
        ]

    return {
        "transaction_types": vals("txn_type"),
        "channels": vals("channel"),
        "merchant_categories": vals("merchant_category"),
        "account_types": vals("account_type"),
    }


def dashboard(db, f):
    return {
        "summary": summary(db, f),
        "monthly": monthly_transactions(db, f),
        "fraud": fraud_overview(db, f),
    }


def python_dashboard(db, f):
    return {
        **dashboard(db, f),
        "secondary": {
            "transaction_types": grouped(db, f, "txn_type"),
            "merchant_categories": grouped(db, f, "merchant_category"),
            "income_activity": income_activity(db, f),
        },
    }
