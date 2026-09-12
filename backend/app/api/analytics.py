from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..schemas.analytics import AnalyticsFilters
from ..services import analytics_service, sql_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def filters(
    start_date, end_date, transaction_type, channel, merchant_category, account_type
):
    return AnalyticsFilters(
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        channel=channel,
        merchant_category=merchant_category,
        account_type=account_type,
    )


common = dict(
    start_date=None,
    end_date=None,
    transaction_type=None,
    channel=None,
    merchant_category=None,
    account_type=None,
)


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.dashboard(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )


@router.get("/python/summary")
def python_summary(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.summary(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )


@router.get("/python/monthly-transactions")
def monthly(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.monthly_transactions(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )


@router.get("/python/transaction-types")
def txn_types(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.grouped(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
        "txn_type",
    )


@router.get("/python/channels")
def channels(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.grouped(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
        "channel",
    )


@router.get("/python/merchant-categories")
def categories(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.grouped(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
        "merchant_category",
    )


@router.get("/python/filter-options")
def filter_options(db: Session = Depends(get_db)):
    return analytics_service.filter_options(db)


@router.get("/python/account-types")
def account_types(db: Session = Depends(get_db)):
    return [
        dict(r._mapping)
        for r in db.execute(
            text(
                "SELECT account_type category, COUNT(*) account_count FROM accounts GROUP BY account_type ORDER BY account_count DESC"
            )
        )
    ]


@router.get("/python/income-activity")
def income(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.income_activity(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )


@router.get("/sql/monthly-transactions")
def sql_monthly(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.monthly_transactions(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )


@router.get("/sql/customer-summary")
def customer_summary(db: Session = Depends(get_db)):
    return sql_service.customer_summary(db)


@router.get("/sql/account-summary")
def account_summary(db: Session = Depends(get_db)):
    return sql_service.account_summary(db)


@router.get("/sql/transaction-summary")
def transaction_summary(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return sql_service.transaction_summary(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )


@router.get("/sql/customer-360")
def customer_360(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return sql_service.customer_360(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )


@router.get("/python/fraud-overview")
def python_fraud_overview(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.fraud_overview(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )


@router.get("/sql/summary")
def sql_summary(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.summary(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )


@router.get("/sql/fraud-overview")
def sql_fraud_overview(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    transaction_type: str | None = None,
    channel: str | None = None,
    merchant_category: str | None = None,
    account_type: str | None = None,
):
    return analytics_service.fraud_overview(
        db,
        filters(
            start_date,
            end_date,
            transaction_type,
            channel,
            merchant_category,
            account_type,
        ),
    )
