import argparse
import os

from data_pipeline.config import *
from data_pipeline.extract import iter_excel_batches, read_small_excel
from data_pipeline.transform import (
    transform_accounts,
    transform_customers,
    transform_transactions,
)
from data_pipeline.validate import validate_batch, validate_relationships


def run(reset=False, validate_only=False):
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://finance_analytics_db_la8f_user:HzUWl6Gkq6osKkpk3WEp1oTZd42tC1zx@dpg-dahq8qrm8hqs73cune80-a.ohio-postgres.render.com/finance_analytics_db_la8f",
    )
    customers = transform_customers(read_small_excel(CUSTOMERS_FILE))
    accounts = transform_accounts(read_small_excel(ACCOUNTS_FILE))
    validate_batch(customers, "customers")
    validate_batch(accounts, "accounts")
    validate_relationships(customers, accounts)
    print(f"Customers validated: {len(customers):,}")
    print(f"Accounts validated: {len(accounts):,}")
    if validate_only:
        txn_count = 0
        for batch in iter_excel_batches(TRANSACTIONS_FILE, BATCH_SIZE):
            batch = transform_transactions(batch)
            validate_batch(batch, "transactions")
            txn_count += len(batch)
        print(f"Transactions validated: {txn_count:,}")
        return
    from data_pipeline.load import create_schema, load_dataframe, reset_tables

    create_schema(database_url)
    if reset:
        reset_tables(database_url)
    load_dataframe(database_url, "customers", customers)
    load_dataframe(database_url, "accounts", accounts)
    txn_count = 0
    for batch in iter_excel_batches(TRANSACTIONS_FILE, BATCH_SIZE):
        batch = transform_transactions(batch)
        validate_batch(batch, "transactions")
        load_dataframe(database_url, "transactions", batch)
        txn_count += len(batch)
        print(f"Loaded transactions: {txn_count:,}")
    print("ETL complete.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reset", action="store_true")
    p.add_argument("--validate-only", action="store_true")
    args = p.parse_args()
    run(args.reset, args.validate_only)
