import pytest

from tests.conftest import ApiClient


pytestmark = [pytest.mark.aws, pytest.mark.system]


def test_deterministic_forecast_against_deployed_system(
    api_client: ApiClient,
) -> None:
    records: list[tuple[str, str]] = []
    try:
        expense = api_client.request(
            "POST",
            "/expenses",
            {
                "description": "Forecast electricity",
                "amount_minor": 10000,
                "expense_date": "2032-08-10",
                "category": "utilities",
                "status": "cleared",
                "essential": True,
            },
            201,
        ).body["data"]
        records.append(("/expenses", expense["expense_id"]))

        income = api_client.request(
            "POST",
            "/income",
            {
                "source": "Forecast income",
                "amount_minor": 50000,
                "expected_date": "2032-08-15",
                "confidence": "guaranteed",
            },
            201,
        ).body["data"]
        records.append(("/income", income["income_id"]))

        commitment = api_client.request(
            "POST",
            "/commitments",
            {
                "name": "Forecast rent",
                "amount_minor": 80000,
                "next_due_date": "2032-08-20",
                "recurrence": "once",
                "essential": True,
            },
            201,
        ).body["data"]
        records.append(("/commitments", commitment["commitment_id"]))

        forecast = api_client.request(
            "GET",
            "/forecast?openingBalanceMinor=100000&safetyBufferMinor=10000"
            "&startDate=2032-08-01&endDate=2032-08-31"
            "&includeLikelyIncome=false&includeUncertainIncome=false",
        ).body["data"]

        assert forecast["minimum_balance_minor"] == 60000
        assert forecast["safe_to_spend_minor"] == 50000
        assert forecast["first_shortfall_date"] is None
        assert forecast["shortfall_amount_minor"] == 0
        assert [event["event_type"] for event in forecast["timeline"]] == [
            "expense",
            "income",
            "commitment",
        ]
        assert [
            event["projected_balance_minor"]
            for event in forecast["timeline"]
        ] == [90000, 140000, 60000]

        shortfall = api_client.request(
            "GET",
            "/forecast?openingBalanceMinor=20000&safetyBufferMinor=10000"
            "&startDate=2032-08-01&endDate=2032-08-31"
            "&includeLikelyIncome=false&includeUncertainIncome=false",
        ).body["data"]
        assert shortfall["minimum_balance_minor"] == -20000
        assert shortfall["safe_to_spend_minor"] == 0
        assert shortfall["first_shortfall_date"] == "2032-08-20"
        assert shortfall["shortfall_amount_minor"] == 30000
    finally:
        for route, record_id in reversed(records):
            api_client.request(
                "DELETE",
                f"{route}/{record_id}",
                expected_status=204,
            )
