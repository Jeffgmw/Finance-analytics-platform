from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://finance_user:finance_password@localhost:5432/finance_analytics"
    cors_origins: str = "https://finance-analytics-platform-1.onrender.com"
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4.1-mini"
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False
    )


settings = Settings()
engine = create_engine(
    settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=10
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
