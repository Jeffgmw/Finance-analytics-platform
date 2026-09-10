from datetime import date
from pydantic import BaseModel, Field


class AnalyticsFilters(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    transaction_type: str | None = Field(default=None, max_length=80)
    channel: str | None = Field(default=None, max_length=80)
    merchant_category: str | None = Field(default=None, max_length=120)
    account_type: str | None = Field(default=None, max_length=50)


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
