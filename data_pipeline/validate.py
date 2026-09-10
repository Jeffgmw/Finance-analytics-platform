
EXPECTED = {
    "customers": [
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
    ],
    "accounts": [
        "account_id",
        "customer_id",
        "branch_id",
        "account_type",
        "balance",
        "open_date",
        "status",
    ],
    "transactions": [
        "transaction_id",
        "account_id",
        "txn_date",
        "txn_type",
        "amount",
        "channel",
        "merchant_category",
    ],
}


def validate_columns(df, table):
    missing = [c for c in EXPECTED[table] if c not in df.columns]
    if missing:
        raise ValueError(f"{table}: missing columns {missing}")


def validate_batch(df, table):
    validate_columns(df, table)
    id_col = {
        "customers": "customer_id",
        "accounts": "account_id",
        "transactions": "transaction_id",
    }[table]
    if df[id_col].isna().any():
        raise ValueError(f"{table}: null primary keys in batch")
    if df[id_col].duplicated().any():
        raise ValueError(f"{table}: duplicate primary keys in batch")
    if table == "transactions" and df["amount"].isna().any():
        raise ValueError("transactions: null amount found")
    if table == "accounts" and df["balance"].isna().any():
        raise ValueError("accounts: null balance found")


def validate_relationships(customers, accounts):
    ids = set(customers["customer_id"].dropna().astype(int))
    missing = set(accounts["customer_id"].dropna().astype(int)) - ids
    if missing:
        raise ValueError(f"accounts: {len(missing)} customer foreign keys not found")
