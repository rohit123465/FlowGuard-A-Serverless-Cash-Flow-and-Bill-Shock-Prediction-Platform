from datetime import date

import boto3
from moto import mock_aws

from src.models.commitment import Commitment
from src.models.notification import BillShockSettings
from src.repositories.financial_repository import FinancialRepository
from src.services.notification_service import evaluate_bill_shock


def _repository() -> FinancialRepository:
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
    table = dynamodb.create_table(
        TableName="flowguard-notifications-test",
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
            {"AttributeName": "GSI2PK", "AttributeType": "S"},
            {"AttributeName": "GSI2SK", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "GSI2",
                "KeySchema": [
                    {"AttributeName": "GSI2PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI2SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    )
    return FinancialRepository(table)


@mock_aws
def test_daily_evaluation_creates_and_deduplicates_warning() -> None:
    repository = _repository()
    settings = BillShockSettings(
        enabled=True,
        opening_balance_minor=10_000,
        safety_buffer_minor=5_000,
        horizon_days=30,
    )
    repository.put_bill_shock_settings("user-a", settings)
    repository.create_commitment(
        "user-a",
        Commitment(
            name="Rent",
            amount_minor=8_000,
            next_due_date=date(2032, 5, 10),
            recurrence="once",
            essential=True,
        ),
    )

    warning = evaluate_bill_shock(repository, "user-a", settings, date(2032, 5, 1))
    assert warning is not None
    assert warning.first_shortfall_date == date(2032, 5, 10)
    assert warning.shortfall_amount_minor == 3_000
    assert len(repository.list_notifications("user-a")) == 1

    assert evaluate_bill_shock(repository, "user-a", settings, date(2032, 5, 1)) is None
    assert len(repository.list_notifications("user-a")) == 1
    assert repository.list_enabled_bill_shock_settings()[0].user_id == "user-a"

    assert repository.mark_notification_read("user-a", warning.notification_id)
    assert repository.list_notifications("user-a")[0].read is True
    assert not repository.mark_notification_read("user-b", warning.notification_id)


@mock_aws
def test_daily_evaluation_does_not_create_safe_warning() -> None:
    repository = _repository()
    settings = BillShockSettings(
        enabled=True,
        opening_balance_minor=100_000,
        safety_buffer_minor=10_000,
    )
    assert evaluate_bill_shock(repository, "user-a", settings, date(2032, 5, 1)) is None
    assert repository.list_notifications("user-a") == []
