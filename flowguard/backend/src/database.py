from functools import lru_cache

import boto3

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
