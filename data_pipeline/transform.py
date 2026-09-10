import pandas as pd

CUSTOMER_COLUMNS = [
    "customer_id",
    "name",
    "gender",
    "date_of_birth",
    "city",
    "state",
    "phone",
    "email",
    "occupation",
    "annual_income",
    "join_date",
    "credit_score",
]
ACCOUNT_COLUMNS = [
    "account_id",
    "customer_id",
    "branch_id",
    "account_type",
    "balance",
    "open_date",
    "status",
]
TRANSACTION_COLUMNS = [
    "transaction_id",
    "account_id",
    "txn_date",
    "txn_type",
    "amount",
    "channel",
    "merchant_category",
]


def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
    return df


def transform_customers(df):
    df = clean_strings(df.copy())
    for c in ["date_of_birth", "join_date"]:
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    df["phone"] = df["phone"].astype("string")
    df["annual_income"] = pd.to_numeric(df["annual_income"], errors="coerce")
    df["credit_score"] = pd.to_numeric(df["credit_score"], errors="coerce").astype(
        "Int64"
    )
    return df[CUSTOMER_COLUMNS]


def transform_accounts(df):
    df = clean_strings(df.copy())
    df["open_date"] = pd.to_datetime(df["open_date"], errors="coerce").dt.date
    df["balance"] = pd.to_numeric(df["balance"], errors="coerce")
    return df[ACCOUNT_COLUMNS]


def transform_transactions(df):
    df = clean_strings(df.copy())
    df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce").dt.date
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df[TRANSACTION_COLUMNS]
