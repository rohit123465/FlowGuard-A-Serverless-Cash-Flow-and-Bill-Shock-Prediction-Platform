import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Settings:
    table_name: str
    aws_region: str | None = None
    receipt_bucket_name: str | None = None
    model_bucket_name: str | None = None
    model_object_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    table_name = os.getenv("TABLE_NAME", "").strip()
    if not table_name:
        raise RuntimeError("TABLE_NAME environment variable is required")

    aws_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    receipt_bucket_name = os.getenv("RECEIPT_BUCKET_NAME", "").strip() or None
    model_bucket_name = os.getenv("MODEL_BUCKET_NAME", "").strip() or None
    model_object_key = os.getenv("MODEL_OBJECT_KEY", "").strip() or None
    return Settings(
        table_name=table_name,
        aws_region=aws_region,
        receipt_bucket_name=receipt_bucket_name,
        model_bucket_name=model_bucket_name,
        model_object_key=model_object_key,
    )
