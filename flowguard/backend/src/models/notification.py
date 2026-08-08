from datetime import date, datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BillShockSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    opening_balance_minor: int = 0
    safety_buffer_minor: int = Field(default=0, ge=0)
    horizon_days: int = Field(default=30, ge=7, le=90)
    include_likely_income: bool = False


class BillShockNotification(BaseModel):
    model_config = ConfigDict(frozen=True)

    notification_id: UUID
    created_at: datetime
    forecast_start_date: date
    forecast_end_date: date
    first_shortfall_date: date
    shortfall_amount_minor: int = Field(gt=0)
    minimum_balance_minor: int
    safety_buffer_minor: int = Field(ge=0)
    read: bool = False


class EnabledBillShockSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str
    settings: BillShockSettings
