import pytest

from tests.conftest import ApiClient


pytestmark = [pytest.mark.aws, pytest.mark.integration]


def test_commitment_crud_against_deployed_api(api_client: ApiClient) -> None:
    commitment_id = None
    try:
        created = api_client.request(
            "POST",
            "/commitments",
            {
                "name": "AWS integration rent",
                "amount_minor": 90000,
                "next_due_date": "2031-01-20",
                "recurrence": "monthly",
                "essential": True,
            },
            201,
        ).body["data"]
        commitment_id = created["commitment_id"]

        fetched = api_client.request(
            "GET",
            f"/commitments/{commitment_id}",
        ).body["data"]
        assert fetched == created

        listed = api_client.request("GET", "/commitments").body["data"]
        assert [item["commitment_id"] for item in listed] == [commitment_id]

        updated = api_client.request(
            "PUT",
            f"/commitments/{commitment_id}",
            {
                "name": "Updated AWS integration rent",
                "amount_minor": 95000,
                "next_due_date": "2031-01-21",
                "recurrence": "monthly",
                "essential": True,
            },
        ).body["data"]
        assert updated["amount_minor"] == 95000
        assert updated["next_due_date"] == "2031-01-21"

        api_client.request(
            "DELETE",
            f"/commitments/{commitment_id}",
            expected_status=204,
        )
        api_client.request(
            "GET",
            f"/commitments/{commitment_id}",
            expected_status=404,
        )
        commitment_id = None
    finally:
        if commitment_id:
            api_client.request(
                "DELETE",
                f"/commitments/{commitment_id}",
                expected_status=204,
            )
