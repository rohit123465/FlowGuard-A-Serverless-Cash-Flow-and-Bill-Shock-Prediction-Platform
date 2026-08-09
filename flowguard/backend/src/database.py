from functools import lru_cache

import boto3
from botocore.config import Config

from .config import get_settings
from .repositories.financial_repository import FinancialRepository


@lru_cache
def get_repository() -> FinancialRepository:
    settings = get_settings()
    resource_arguments = {}
    if settings.aws_region:
        resource_arguments["region_name"] = settings.aws_region

    dynamodb = boto3.resource("dynamodb", **resource_arguments)
    return FinancialRepository(dynamodb.Table(settings.table_name))


@lru_cache
def get_s3_client():
    settings = get_settings()
    client_arguments = {}
    if settings.aws_region:
        client_arguments["region_name"] = settings.aws_region
        client_arguments["endpoint_url"] = f"https://s3.{settings.aws_region}.amazonaws.com"
    client_arguments["config"] = Config(
        signature_version="s3v4",
        s3={"addressing_style": "virtual"},
    )
    return boto3.client("s3", **client_arguments)


@lru_cache
def get_textract_client():
    settings = get_settings()
    arguments = {"region_name": settings.aws_region} if settings.aws_region else {}
    return boto3.client("textract", **arguments)
