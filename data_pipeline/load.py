import io

import psycopg
from sqlalchemy import create_engine

from data_pipeline.config import ROOT

SCHEMA = (ROOT / "sql" / "schema.sql").read_text()
INDEXES = (ROOT / "sql" / "indexes.sql").read_text()


def create_schema(database_url: str):
    engine = create_engine(database_url)
    with engine.begin() as conn:
        for statement in [x.strip() for x in SCHEMA.split(";") if x.strip()]:
            conn.exec_driver_sql(statement)
        for statement in [x.strip() for x in INDEXES.split(";") if x.strip()]:
            conn.exec_driver_sql(statement)
    engine.dispose()


def reset_tables(database_url: str):
    engine = create_engine(database_url)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "TRUNCATE TABLE transactions, accounts, customers RESTART IDENTITY CASCADE"
        )
    engine.dispose()


def _copy_rows(conn, table, df):
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)
    columns = ",".join(df.columns)
    with conn.cursor() as cur, cur.copy(
        f"COPY {table} ({columns}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
    ) as copy:
        while data := buf.read(1024 * 1024):
            copy.write(data)
    conn.commit()


def connection_url(database_url: str):
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def load_dataframe(database_url, table, df):
    with psycopg.connect(connection_url(database_url)) as conn:
        _copy_rows(conn, table, df)
