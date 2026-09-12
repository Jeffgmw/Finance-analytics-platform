"""Refresh derived analytics tables against an existing PostgreSQL database."""
from data_pipeline.build_analytics import build

if __name__ == "__main__":
    import os
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    build(url)
