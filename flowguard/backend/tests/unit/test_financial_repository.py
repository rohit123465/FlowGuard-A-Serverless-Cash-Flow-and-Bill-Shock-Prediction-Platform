from datetime import date
from typing import Iterator

import boto3
import pytest
from moto import mock_aws

from src.models.commitment import Commitment, Recurrence
from src.models.expense import Expense, ExpenseStatus
from src.models.forecast import ForecastRequest
from src.models.income import ExpectedIncome, IncomeConfidence
from src.repositories.financial_repository import (
    FinancialRepository,
    RecordAlreadyExistsError,
    RecordNotFoundError,
)
from src.services.forecast_service import calculate_forecast


@pytest.fixture
def repository() -> Iterator[FinancialRepository]:
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
        table = dynamodb.create_table(
            TableName="flowguard-test",
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
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
                }
            ],
        )
        yield FinancialRepository(table)


def test_expense_crud_and_date_index(repository: FinancialRepository) -> None:
    expense = Expense(
        description="Groceries",
        amount_minor=4_250,
        expense_date=date(2026, 8, 10),
        category="groceries",
        status=ExpenseStatus.CLEARED,
        essential=True,
    )

    repository.create_expense("user-a", expense)
    assert repository.get_expense("user-a", expense.expense_id) == expense

    updated = expense.model_copy(
        update={"amount_minor": 5_000, "expense_date": date(2026, 9, 1)}
    )
    repository.update_expense("user-a", updated)

    assert repository.list_expenses(
        "user-a", date(2026, 8, 1), date(2026, 8, 31)
    ) == []
    assert repository.list_expenses(
        "user-a", date(2026, 9, 1), date(2026, 9, 30)
    ) == [updated]
    assert repository.delete_expense("user-a", expense.expense_id) is True
    assert repository.get_expense("user-a", expense.expense_id) is None
    assert repository.delete_expense("user-a", expense.expense_id) is False


def test_records_are_isolated_by_user(repository: FinancialRepository) -> None:
    expense = Expense(
        description="Private expense",
        amount_minor=1_000,
        expense_date=date(2026, 8, 10),
        category="other",
    )
    repository.create_expense("user-a", expense)

    assert repository.get_expense("user-b", expense.expense_id) is None
    assert repository.list_expenses(
        "user-b", date(2026, 8, 1), date(2026, 8, 31)
    ) == []
    assert repository.delete_expense("user-b", expense.expense_id) is False
    assert repository.get_expense("user-a", expense.expense_id) == expense


def test_expense_receipt_key_is_persisted(repository: FinancialRepository) -> None:
    expense = Expense(
        description="Receipt test",
        amount_minor=1_500,
        expense_date=date(2026, 8, 10),
        category="other",
        receipt_key="receipts/user-a/expense/receipt.png",
    )
    repository.create_expense("user-a", expense)
    assert repository.get_expense("user-a", expense.expense_id) == expense


def test_duplicate_record_is_rejected(repository: FinancialRepository) -> None:
    expense = Expense(
        description="Train ticket",
        amount_minor=2_500,
        expense_date=date(2026, 8, 5),
        category="transport",
    )
    repository.create_expense("user-a", expense)

    with pytest.raises(RecordAlreadyExistsError):
        repository.create_expense("user-a", expense)


def test_expense_date_range_is_inclusive_and_ordered(
    repository: FinancialRepository,
) -> None:
    expenses = [
        Expense(
            description="End",
            amount_minor=300,
            expense_date=date(2026, 8, 31),
            category="other",
        ),
        Expense(
            description="Before",
            amount_minor=100,
            expense_date=date(2026, 7, 31),
            category="other",
        ),
        Expense(
            description="Start",
            amount_minor=200,
            expense_date=date(2026, 8, 1),
            category="other",
        ),
    ]
    for expense in expenses:
        repository.create_expense("user-a", expense)

    results = repository.list_expenses(
        "user-a", date(2026, 8, 1), date(2026, 8, 31)
    )

    assert [expense.description for expense in results] == ["Start", "End"]


def test_income_crud_preserves_confidence(repository: FinancialRepository) -> None:
    income = ExpectedIncome(
        source="Client invoice",
        amount_minor=50_000,
        expected_date=date(2026, 8, 15),
        confidence=IncomeConfidence.LIKELY,
    )
    repository.create_income("user-a", income)

    assert repository.get_income("user-a", income.income_id) == income
    assert repository.list_income(
        "user-a", date(2026, 8, 1), date(2026, 8, 31)
    ) == [income]

    updated = income.model_copy(update={"confidence": IncomeConfidence.GUARANTEED})
    repository.update_income("user-a", updated)
    assert repository.get_income("user-a", income.income_id) == updated
    assert repository.delete_income("user-a", income.income_id) is True


def test_commitments_are_stored_and_listed(repository: FinancialRepository) -> None:
    rent = Commitment(
        name="Rent",
        amount_minor=80_000,
        next_due_date=date(2026, 8, 20),
        recurrence=Recurrence.MONTHLY,
    )
    insurance = Commitment(
        name="Insurance",
        amount_minor=12_000,
        next_due_date=date(2026, 7, 1),
        recurrence=Recurrence.YEARLY,
        essential=False,
    )
    repository.create_commitment("user-a", rent)
    repository.create_commitment("user-a", insurance)

    assert repository.get_commitment("user-a", rent.commitment_id) == rent
    assert set(repository.list_commitments("user-a")) == {rent, insurance}

    updated_rent = rent.model_copy(update={"amount_minor": 82_500})
    repository.update_commitment("user-a", updated_rent)
    assert repository.get_commitment("user-a", rent.commitment_id) == updated_rent
    assert repository.delete_commitment("user-a", rent.commitment_id) is True


def test_updating_missing_record_fails(repository: FinancialRepository) -> None:
    expense = Expense(
        description="Missing",
        amount_minor=1_000,
        expense_date=date(2026, 8, 10),
        category="other",
    )

    with pytest.raises(RecordNotFoundError):
        repository.update_expense("user-a", expense)


def test_invalid_query_range_is_rejected(repository: FinancialRepository) -> None:
    with pytest.raises(ValueError):
        repository.list_expenses(
            "user-a",
            date(2026, 9, 1),
            date(2026, 8, 1),
        )


def test_stored_records_feed_the_forecast(repository: FinancialRepository) -> None:
    income = ExpectedIncome(
        source="Client invoice",
        amount_minor=50_000,
        expected_date=date(2026, 8, 15),
    )
    rent = Commitment(
        name="Rent",
        amount_minor=80_000,
        next_due_date=date(2026, 8, 20),
    )
    expense = Expense(
        description="Electricity",
        amount_minor=10_000,
        expense_date=date(2026, 8, 10),
        category="utilities",
    )
    repository.create_income("user-a", income)
    repository.create_commitment("user-a", rent)
    repository.create_expense("user-a", expense)

    start_date = date(2026, 8, 1)
    end_date = date(2026, 8, 31)
    result = calculate_forecast(
        ForecastRequest(
            opening_balance_minor=100_000,
            safety_buffer_minor=10_000,
            start_date=start_date,
            end_date=end_date,
        ),
        incomes=repository.list_income("user-a", start_date, end_date),
        commitments=repository.list_commitments("user-a"),
        expenses=repository.list_expenses("user-a", start_date, end_date),
    )

    assert result.minimum_balance_minor == 60_000
    assert result.safe_to_spend_minor == 50_000
