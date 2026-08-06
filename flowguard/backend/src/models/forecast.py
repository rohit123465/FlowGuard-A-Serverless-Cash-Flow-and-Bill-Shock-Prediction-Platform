from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CashFlowEventType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    COMMITMENT = "commitment"

#The information needed to calculate a forecast, such as current balance, safety buffer, and date range.
class ForecastRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    opening_balance_minor: int
    safety_buffer_minor: int = Field(ge=0)
    start_date: date
    end_date: date
    include_likely_income: bool = False
    include_uncertain_income: bool = False

    @model_validator(mode="after")
    def validate_date_range(self) -> "ForecastRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self

#One item on the forecast timeline, showing the balance after that item occurs.
class ForecastEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID
    event_date: date
    description: str
    event_type: CashFlowEventType
    change_minor: int
    projected_balance_minor: int

#he completed forecast, including safe-to-spend, lowest balance, shortfall date, and timeline.
class ForecastResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    opening_balance_minor: int
    safety_buffer_minor: int
    safe_to_spend_minor: int = Field(ge=0)
    minimum_balance_minor: int
    first_shortfall_date: date | None
    shortfall_amount_minor: int = Field(ge=0)
    excluded_income_count: int = Field(ge=0)
    timeline: tuple[ForecastEvent, ...]
