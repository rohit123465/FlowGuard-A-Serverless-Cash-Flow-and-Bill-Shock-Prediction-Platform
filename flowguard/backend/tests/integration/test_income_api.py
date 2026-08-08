import pytest

from tests.conftest import ApiClient


pytestmark = [pytest.mark.aws, pytest.mark.integration]


def test_income_crud_against_deployed_api(api_client: ApiClient) -> None:
    income_id = None
    try:
        created = api_client.request(
            "POST",
            "/income",
            {
                "source": "AWS integration salary",
                "amount_minor": 250000,
                "expected_date": "2031-01-15",
                "confidence": "guaranteed",
            },
            201,
        ).body["data"]
        income_id = created["income_id"]

        fetched = api_client.request("GET", f"/income/{income_id}").body["data"]
        assert fetched == created

        listed = api_client.request(
            "GET",
            "/income?startDate=2031-01-01&endDate=2031-01-31",
        ).body["data"]
        assert [item["income_id"] for item in listed] == [income_id]

        updated = api_client.request(
            "PUT",
            f"/income/{income_id}",
            {
                "source": "Updated AWS integration salary",
                "amount_minor": 260000,
                "expected_date": "2031-01-16",
                "confidence": "likely",
            },
        ).body["data"]
        assert updated["amount_minor"] == 260000
        assert updated["confidence"] == "likely"

        api_client.request("DELETE", f"/income/{income_id}", expected_status=204)
        api_client.request("GET", f"/income/{income_id}", expected_status=404)
        income_id = None
    finally:
        if income_id:
            api_client.request("DELETE", f"/income/{income_id}", expected_status=204)
