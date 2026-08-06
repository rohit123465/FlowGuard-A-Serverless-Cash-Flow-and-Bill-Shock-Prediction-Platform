from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

#Class to represent the confidence level of an expected income payment. It explains the reliability of the payment. 
class IncomeConfidence(StrEnum):
    GUARANTEED = "guaranteed"
    LIKELY = "likely"
    UNCERTAIN = "uncertain"

# It represents one future income payment.
class ExpectedIncome(BaseModel):
    model_config = ConfigDict(frozen=True)

    income_id: UUID = Field(default_factory=uuid4)
    source: str = Field(min_length=1, max_length=120) #Client invoice for example
    amount_minor: int = Field(gt=0)
    expected_date: date
    confidence: IncomeConfidence = IncomeConfidence.GUARANTEED
