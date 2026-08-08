from pydantic import BaseModel, ConfigDict, Field


class CategorySpending(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    amount_minor: int = Field(ge=0)
    percentage: float = Field(ge=0, le=100)


class MonthlyAnalytics(BaseModel):
    model_config = ConfigDict(frozen=True)

    year: int
    month: int
    total_income_minor: int = Field(ge=0)
    total_expenses_minor: int = Field(ge=0)
    essential_expenses_minor: int = Field(ge=0)
    discretionary_expenses_minor: int = Field(ge=0)
    net_cash_flow_minor: int
    savings_rate_percent: float | None
    expense_count: int = Field(ge=0)
    income_count: int = Field(ge=0)
    highest_spending_category: str | None
    category_breakdown: tuple[CategorySpending, ...]
