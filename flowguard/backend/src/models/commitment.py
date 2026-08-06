from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

#Indicates whether a bill happens once, weekly, monthly, or yearly.
class Recurrence(StrEnum):
    ONCE = "once"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

#A commitment represents an upcoming bill, whether the bill is monthly, weekly, monthly or yearly. 
class Commitment(BaseModel):
    model_config = ConfigDict(frozen=True)

    commitment_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=120)
    amount_minor: int = Field(gt=0)
    next_due_date: date
    recurrence: Recurrence = Recurrence.ONCE
    essential: bool = True
