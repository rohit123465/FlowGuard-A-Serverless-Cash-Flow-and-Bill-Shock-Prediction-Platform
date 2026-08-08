from pydantic import BaseModel, ConfigDict, Field


class ReceiptUploadRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0, le=5 * 1024 * 1024)


class ReceiptConfirmRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    receipt_key: str = Field(min_length=1, max_length=1024)
