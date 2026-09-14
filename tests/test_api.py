from data_pipeline.transform import transform_transactions
from data_pipeline.validate import validate_batch
import pandas as pd

def test_transaction_schema_validation():
    df=pd.DataFrame({"transaction_id":[1],"account_id":[2],"txn_date":["2020-01-01"],"txn_type":["Deposit"],"amount":[10.0],"channel":["Branch"],"merchant_category":["Other"]})
    validate_batch(transform_transactions(df), "transactions")


def test_sql_dashboard_does_not_overwrite_shared_kpi_summary():
    from backend.app.services import sql_service

    class DummyDB:
        def execute(self, *args, **kwargs):
            class Result:
                def __iter__(self):
                    return iter([])
            return Result()

    class Filters:
        start_date = end_date = transaction_type = channel = merchant_category = account_type = None

    payload = sql_service.sql_dashboard(DummyDB(), Filters())
    assert "summary" not in payload
    assert "account_summary" in payload
    assert "customer_360" in payload
