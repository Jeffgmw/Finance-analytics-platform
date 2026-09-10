from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data_pipeline" / "data" / "raw"
CUSTOMERS_FILE = RAW_DIR / "customers.xlsx"
ACCOUNTS_FILE = RAW_DIR / "accounts(1).xlsx"
TRANSACTIONS_FILE = RAW_DIR / "transactions.xlsx"
BATCH_SIZE = 20_000
