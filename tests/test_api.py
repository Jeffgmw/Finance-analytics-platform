from data_pipeline.transform import transform_transactions
from data_pipeline.validate import validate_batch
import pandas as pd

def test_transaction_schema_validation():
    df=pd.DataFrame({"transaction_id":[1],"account_id":[2],"txn_date":["2020-01-01"],"txn_type":["Deposit"],"amount":[10.0],"channel":["Branch"],"merchant_category":["Other"]})
    validate_batch(transform_transactions(df), "transactions")
