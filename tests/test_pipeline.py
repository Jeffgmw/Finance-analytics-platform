import pandas as pd
from data_pipeline.transform import transform_customers, transform_accounts, transform_transactions
from data_pipeline.validate import validate_batch, validate_relationships

def test_customer_transform_preserves_phone_as_text():
    df=pd.DataFrame([{"customer_id":1,"name":"A","gender":"F","date_of_birth":"1990-01-01","city":"X","state":"Y","phone":712345678,"email":"a@x.com","occupation":"Analyst","annual_income":100000,"join_date":"2020-01-01","credit_score":700}])
    out=transform_customers(df)
    assert str(out.loc[0,"phone"]) == "712345678"

def test_relationship_validation():
    c=pd.DataFrame({"customer_id":[1,2]})
    a=pd.DataFrame({"customer_id":[1]})
    validate_relationships(c,a)

def test_transaction_validation_rejects_duplicate_ids():
    df=pd.DataFrame({"transaction_id":[1,1],"account_id":[2,2],"txn_date":["2020-01-01"]*2,"txn_type":["Deposit"]*2,"amount":[10,20],"channel":["Branch"]*2,"merchant_category":["Other"]*2})
    try: validate_batch(df,"transactions")
    except ValueError as e: assert "duplicate" in str(e)
    else: raise AssertionError("Expected duplicate ID validation failure")
