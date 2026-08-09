from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ReceiptAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    vendor_name: str | None = None
    vendor_confidence: float | None = Field(default=None, ge=0, le=100)
    receipt_date: date | None = None
    date_text: str | None = None
    date_confidence: float | None = Field(default=None, ge=0, le=100)
    total_minor: int | None = Field(default=None, ge=0)
    total_text: str | None = None
    total_confidence: float | None = Field(default=None, ge=0, le=100)
    currency: str = "GBP"
    model_version: str | None = None
