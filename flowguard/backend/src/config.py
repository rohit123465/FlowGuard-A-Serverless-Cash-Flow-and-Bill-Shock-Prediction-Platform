import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Settings:
    table_name: str
    aws_region: str | None = None


@lru_cache
def get_settings() -> Settings:
    table_name = os.getenv("TABLE_NAME", "").strip()
    if not table_name:
        raise RuntimeError("TABLE_NAME environment variable is required")

    aws_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    return Settings(table_name=table_name, aws_region=aws_region)
