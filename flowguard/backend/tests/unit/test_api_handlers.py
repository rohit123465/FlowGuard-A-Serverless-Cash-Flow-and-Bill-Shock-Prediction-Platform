import json
from datetime import date
from typing import Any, Iterator

import boto3
import pytest
from moto import mock_aws

from src.handlers import commitments as commitment_handler
from src.handlers import expenses as expense_handler
from src.handlers import forecast as forecast_handler
from src.handlers import income as income_handler
from src.handlers import analytics as analytics_handler
from src.handlers import exports as export_handler
from src.models.commitment import Commitment
from src.models.expense import Expense
from src.models.income import ExpectedIncome
from src.repositories.financial_repository import FinancialRepository


def api_event(
    route_key: str,
    *,
    user_id: str | None = "user-a",
    body: dict[str, Any] | str | None = None,
    path_parameters: dict[str, str] | None = None,
    query_parameters: dict[str, str] | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "version": "2.0",
        "routeKey": route_key,
        "requestContext": {},
        "pathParameters": path_parameters,
        "queryStringParameters": query_parameters,
        "isBase64Encoded": False,
    }
    if user_id is not None:
        event["requestContext"] = {
            "authorizer": {"jwt": {"claims": {"sub": user_id}}}
        }
    if isinstance(body, dict):
        event["body"] = json.dumps(body)
    elif body is not None:
        event["body"] = body
    return event


def response_body(response: dict[str, Any]) -> dict[str, Any]:
    return json.loads(response["body"])


@pytest.fixture
def repository(monkeypatch: pytest.MonkeyPatch) -> Iterator[FinancialRepository]:
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
        table = dynamodb.create_table(
            TableName="flowguard-api-test",
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
        repository = FinancialRepository(table)
        for module in (
            expense_handler,
            income_handler,
            commitment_handler,
            forecast_handler,
            analytics_handler,
            export_handler,
        ):
            monkeypatch.setattr(module, "get_repository", lambda: repository)
        yield repository


def test_missing_authenticated_user_returns_401(
    repository: FinancialRepository,
) -> None:
    del repository
    response = expense_handler.handler(
        api_event("GET /expenses", user_id=None),
        None,
    )

    assert response["statusCode"] == 401
    assert response_body(response)["error"]["code"] == "UNAUTHORIZED"


def test_invalid_json_returns_400(repository: FinancialRepository) -> None:
    del repository
    response = expense_handler.handler(
        api_event("POST /expenses", body="not-json"),
        None,
    )

    assert response["statusCode"] == 400
    assert response_body(response)["error"]["code"] == "BAD_REQUEST"


def test_expense_api_crud(repository: FinancialRepository) -> None:
    del repository
    create_response = expense_handler.handler(
        api_event(
            "POST /expenses",
            body={
                "description": "Groceries",
                "amount_minor": 4_250,
                "expense_date": "2026-08-10",
                "category": "groceries",
                "essential": True,
            },
        ),
        None,
    )
    assert create_response["statusCode"] == 201
    expense_id = response_body(create_response)["data"]["expense_id"]

    get_response = expense_handler.handler(
        api_event(
            "GET /expenses/{expenseId}",
            path_parameters={"expenseId": expense_id},
        ),
        None,
    )
    assert get_response["statusCode"] == 200
    assert response_body(get_response)["data"]["description"] == "Groceries"

    update_response = expense_handler.handler(
        api_event(
            "PUT /expenses/{expenseId}",
            path_parameters={"expenseId": expense_id},
            body={
                "description": "Groceries and toiletries",
                "amount_minor": 5_000,
                "expense_date": "2026-08-11",
                "category": "groceries",
            },
        ),
        None,
    )
    assert update_response["statusCode"] == 200
    assert response_body(update_response)["data"]["amount_minor"] == 5_000

    list_response = expense_handler.handler(
        api_event(
            "GET /expenses",
            query_parameters={
                "startDate": "2026-08-01",
                "endDate": "2026-08-31",
            },
        ),
        None,
    )
    assert list_response["statusCode"] == 200
    assert len(response_body(list_response)["data"]) == 1

    delete_response = expense_handler.handler(
        api_event(
            "DELETE /expenses/{expenseId}",
            path_parameters={"expenseId": expense_id},
        ),
        None,
    )
    assert delete_response["statusCode"] == 204

    missing_response = expense_handler.handler(
        api_event(
            "GET /expenses/{expenseId}",
            path_parameters={"expenseId": expense_id},
        ),
        None,
    )
    assert missing_response["statusCode"] == 404


def test_expense_api_keeps_users_isolated(repository: FinancialRepository) -> None:
    expense = Expense(
        description="User A expense",
        amount_minor=1_000,
        expense_date=date(2026, 8, 10),
        category="other",
    )
    repository.create_expense("user-a", expense)

    response = expense_handler.handler(
        api_event(
            "GET /expenses/{expenseId}",
            user_id="user-b",
            path_parameters={"expenseId": str(expense.expense_id)},
        ),
        None,
    )

    assert response["statusCode"] == 404


def test_income_api_crud(repository: FinancialRepository) -> None:
    del repository
    create_response = income_handler.handler(
        api_event(
            "POST /income",
            body={
                "source": "Client invoice",
                "amount_minor": 50_000,
                "expected_date": "2026-08-15",
                "confidence": "likely",
            },
        ),
        None,
    )
    assert create_response["statusCode"] == 201
    income_id = response_body(create_response)["data"]["income_id"]

    update_response = income_handler.handler(
        api_event(
            "PUT /income/{incomeId}",
            path_parameters={"incomeId": income_id},
            body={
                "source": "Client invoice",
                "amount_minor": 50_000,
                "expected_date": "2026-08-15",
                "confidence": "guaranteed",
            },
        ),
        None,
    )
    assert update_response["statusCode"] == 200
    assert response_body(update_response)["data"]["confidence"] == "guaranteed"

    list_response = income_handler.handler(
        api_event(
            "GET /income",
            query_parameters={
                "startDate": "2026-08-01",
                "endDate": "2026-08-31",
            },
        ),
        None,
    )
    assert len(response_body(list_response)["data"]) == 1

    delete_response = income_handler.handler(
        api_event(
            "DELETE /income/{incomeId}",
            path_parameters={"incomeId": income_id},
        ),
        None,
    )
    assert delete_response["statusCode"] == 204


def test_commitment_api_crud(repository: FinancialRepository) -> None:
    del repository
    create_response = commitment_handler.handler(
        api_event(
            "POST /commitments",
            body={
                "name": "Rent",
                "amount_minor": 80_000,
                "next_due_date": "2026-08-20",
                "recurrence": "monthly",
                "essential": True,
            },
        ),
        None,
    )
    assert create_response["statusCode"] == 201
    commitment_id = response_body(create_response)["data"]["commitment_id"]

    get_response = commitment_handler.handler(
        api_event(
            "GET /commitments/{commitmentId}",
            path_parameters={"commitmentId": commitment_id},
        ),
        None,
    )
    assert get_response["statusCode"] == 200

    list_response = commitment_handler.handler(
        api_event("GET /commitments"),
        None,
    )
    assert len(response_body(list_response)["data"]) == 1

    delete_response = commitment_handler.handler(
        api_event(
            "DELETE /commitments/{commitmentId}",
            path_parameters={"commitmentId": commitment_id},
        ),
        None,
    )
    assert delete_response["statusCode"] == 204


def test_forecast_api_uses_stored_records(repository: FinancialRepository) -> None:
    repository.create_income(
        "user-a",
        ExpectedIncome(
            source="Client invoice",
            amount_minor=50_000,
            expected_date=date(2026, 8, 15),
        ),
    )
    repository.create_commitment(
        "user-a",
        Commitment(
            name="Rent",
            amount_minor=80_000,
            next_due_date=date(2026, 8, 20),
        ),
    )
    repository.create_expense(
        "user-a",
        Expense(
            description="Electricity",
            amount_minor=10_000,
            expense_date=date(2026, 8, 10),
            category="utilities",
        ),
    )

    response = forecast_handler.handler(
        api_event(
            "GET /forecast",
            query_parameters={
                "openingBalanceMinor": "100000",
                "safetyBufferMinor": "10000",
                "startDate": "2026-08-01",
                "endDate": "2026-08-31",
            },
        ),
        None,
    )

    assert response["statusCode"] == 200
    data = response_body(response)["data"]
    assert data["minimum_balance_minor"] == 60_000
    assert data["safe_to_spend_minor"] == 50_000
    assert len(data["timeline"]) == 3


def test_forecast_api_rejects_invalid_query(repository: FinancialRepository) -> None:
    del repository
    response = forecast_handler.handler(
        api_event(
            "GET /forecast",
            query_parameters={
                "openingBalanceMinor": "not-an-integer",
                "safetyBufferMinor": "10000",
                "startDate": "2026-08-01",
                "endDate": "2026-08-31",
            },
        ),
        None,
    )

    assert response["statusCode"] == 400


def test_monthly_analytics_uses_stored_income_and_expenses(
    repository: FinancialRepository,
) -> None:
    repository.create_income(
        "user-a",
        ExpectedIncome(
            source="Salary",
            amount_minor=200_000,
            expected_date=date(2026, 8, 15),
        ),
    )
    repository.create_expense(
        "user-a",
        Expense(
            description="Rent",
            amount_minor=80_000,
            expense_date=date(2026, 8, 1),
            category="housing",
            essential=True,
        ),
    )
    repository.create_expense(
        "user-a",
        Expense(
            description="Cinema",
            amount_minor=2_000,
            expense_date=date(2026, 8, 5),
            category="leisure",
            essential=False,
        ),
    )

    response = analytics_handler.handler(
        api_event(
            "GET /analytics/monthly",
            query_parameters={"year": "2026", "month": "8"},
        ),
        None,
    )
    data = response_body(response)["data"]
    assert response["statusCode"] == 200
    assert data["total_income_minor"] == 200_000
    assert data["total_expenses_minor"] == 82_000
    assert data["net_cash_flow_minor"] == 118_000
    assert data["savings_rate_percent"] == 59.0
    assert data["highest_spending_category"] == "housing"


def test_expense_csv_export_is_downloadable(repository: FinancialRepository) -> None:
    repository.create_expense(
        "user-a",
        Expense(
            description="Groceries, weekly",
            amount_minor=4_250,
            expense_date=date(2026, 8, 10),
            category="groceries",
            essential=True,
        ),
    )
    response = export_handler.handler(
        api_event(
            "GET /exports/expenses.csv",
            query_parameters={
                "startDate": "2026-08-01",
                "endDate": "2026-08-31",
            },
        ),
        None,
    )
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"].startswith("text/csv")
    assert '"Groceries, weekly"' in response["body"]
    assert "42.50" in response["body"]


def test_invalid_uuid_returns_400(repository: FinancialRepository) -> None:
    del repository
    response = expense_handler.handler(
        api_event(
            "GET /expenses/{expenseId}",
            path_parameters={"expenseId": "not-a-uuid"},
        ),
        None,
    )

    assert response["statusCode"] == 400
