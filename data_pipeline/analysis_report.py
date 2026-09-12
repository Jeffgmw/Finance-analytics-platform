"""Optional Python-side analysis artifact generator using Pandas + Matplotlib."""

import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine

OUT = Path(__file__).resolve().parent / "data" / "processed"


def main():
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://finance_analytics_db_la8f_user:HzUWl6Gkq6osKkpk3WEp1oTZd42tC1zx@dpg-dahq8qrm8hqs73cune80-a.ohio-postgres.render.com/finance_analytics_db_la8f",
    )
    engine = create_engine(url)
    monthly = pd.read_sql(
        "SELECT DATE_TRUNC('month', txn_date)::date month, SUM(amount) total_value FROM transactions GROUP BY 1 ORDER BY 1",
        engine,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(monthly["month"], monthly["total_value"])
    plt.title("Monthly transaction value")
    plt.xlabel("Month")
    plt.ylabel("Value")
    plt.tight_layout()
    plt.savefig(OUT / "monthly_transaction_value.png", dpi=160)
    plt.close()
    engine.dispose()
    print(f"Wrote {OUT / 'monthly_transaction_value.png'}")


if __name__ == "__main__":
    main()
