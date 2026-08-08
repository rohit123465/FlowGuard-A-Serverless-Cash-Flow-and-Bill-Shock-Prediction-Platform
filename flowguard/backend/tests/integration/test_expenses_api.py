import pytest

from tests.conftest import ApiClient


pytestmark = [pytest.mark.aws, pytest.mark.integration]


def test_expense_crud_against_deployed_api(api_client: ApiClient) -> None:
    expense_id = None
    try:
        created = api_client.request(
            "POST",
            "/expenses",
            {
                "description": "AWS integration groceries",
                "amount_minor": 4250,
                "expense_date": "2031-01-10",
                "category": "groceries",
                "status": "planned",
                "essential": True,
            },
            201,
        ).body["data"]
        expense_id = created["expense_id"]

        fetched = api_client.request("GET", f"/expenses/{expense_id}").body["data"]
        assert fetched == created

        listed = api_client.request(
            "GET",
            "/expenses?startDate=2031-01-01&endDate=2031-01-31",
        ).body["data"]
        assert [item["expense_id"] for item in listed] == [expense_id]

        updated = api_client.request(
            "PUT",
            f"/expenses/{expense_id}",
            {
                "description": "Updated AWS integration groceries",
                "amount_minor": 5000,
                "expense_date": "2031-01-11",
                "category": "groceries",
                "status": "cleared",
                "essential": True,
            },
        ).body["data"]
        assert updated["amount_minor"] == 5000
        assert updated["status"] == "cleared"

        api_client.request("DELETE", f"/expenses/{expense_id}", expected_status=204)
        api_client.request("GET", f"/expenses/{expense_id}", expected_status=404)
        expense_id = None
    finally:
        if expense_id:
            api_client.request(
                "DELETE",
                f"/expenses/{expense_id}",
                expected_status=204,
            )
