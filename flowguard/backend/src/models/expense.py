from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

#Indicates whether an expense is planned or has already been paid.
class ExpenseStatus(StrEnum):
    PLANNED = "planned" #a future or intended expense
    CLEARED = "cleared" #a completed expense

#Money the user has spent or plans to spend.
class Expense(BaseModel):
    model_config = ConfigDict(frozen=True)

    expense_id: UUID = Field(default_factory=uuid4)
    description: str = Field(min_length=1, max_length=200)
    amount_minor: int = Field(gt=0)
    expense_date: date
    category: str = Field(min_length=1, max_length=80)
    status: ExpenseStatus = ExpenseStatus.PLANNED
    essential: bool = False
