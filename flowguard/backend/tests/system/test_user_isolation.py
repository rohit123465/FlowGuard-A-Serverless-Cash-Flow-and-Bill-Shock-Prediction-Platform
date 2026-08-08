import pytest

from tests.conftest import AwsTestEnvironment


pytestmark = [pytest.mark.aws, pytest.mark.system]


def test_users_cannot_access_each_others_records(
    aws_environment: AwsTestEnvironment,
) -> None:
    user_a = aws_environment.create_user("isolation-a")
    user_b = aws_environment.create_user("isolation-b")
    records: list[tuple[str, str]] = []
    try:
        expense = user_a.request(
            "POST",
            "/expenses",
            {
                "description": "User A private expense",
                "amount_minor": 1000,
                "expense_date": "2033-04-10",
                "category": "private",
                "status": "cleared",
                "essential": False,
            },
            201,
        ).body["data"]
        records.append(("/expenses", expense["expense_id"]))

        income = user_a.request(
            "POST",
            "/income",
            {
                "source": "User A private income",
                "amount_minor": 5000,
                "expected_date": "2033-04-15",
                "confidence": "guaranteed",
            },
            201,
        ).body["data"]
        records.append(("/income", income["income_id"]))

        commitment = user_a.request(
            "POST",
            "/commitments",
            {
                "name": "User A private commitment",
                "amount_minor": 2000,
                "next_due_date": "2033-04-20",
                "recurrence": "once",
                "essential": True,
            },
            201,
        ).body["data"]
        records.append(("/commitments", commitment["commitment_id"]))

        assert user_b.request(
            "GET",
            "/expenses?startDate=2033-04-01&endDate=2033-04-30",
        ).body["data"] == []
        assert user_b.request(
            "GET",
            "/income?startDate=2033-04-01&endDate=2033-04-30",
        ).body["data"] == []
        assert user_b.request("GET", "/commitments").body["data"] == []

        user_b.request(
            "GET",
            f"/expenses/{expense['expense_id']}",
            expected_status=404,
        )
        user_b.request(
            "GET",
            f"/income/{income['income_id']}",
            expected_status=404,
        )
        user_b.request(
            "GET",
            f"/commitments/{commitment['commitment_id']}",
            expected_status=404,
        )
        user_b.request(
            "DELETE",
            f"/expenses/{expense['expense_id']}",
            expected_status=404,
        )

        user_a.request("GET", f"/expenses/{expense['expense_id']}")
        user_a.request("GET", f"/income/{income['income_id']}")
        user_a.request("GET", f"/commitments/{commitment['commitment_id']}")

        forecast = user_b.request(
            "GET",
            "/forecast?openingBalanceMinor=10000&safetyBufferMinor=1000"
            "&startDate=2033-04-01&endDate=2033-04-30"
            "&includeLikelyIncome=false&includeUncertainIncome=false",
        ).body["data"]
        assert forecast["timeline"] == []
        assert forecast["minimum_balance_minor"] == 10000
    finally:
        for route, record_id in reversed(records):
            user_a.request(
                "DELETE",
                f"{route}/{record_id}",
                expected_status=204,
            )
