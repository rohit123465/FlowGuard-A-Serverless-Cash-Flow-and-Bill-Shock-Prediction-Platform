import urllib.request
import uuid

import pytest

from tests.conftest import ApiClient


pytestmark = [pytest.mark.aws, pytest.mark.integration]


def _raw_request(client: ApiClient, path: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        f"{client.base_url}{path}",
        headers={"Authorization": f"Bearer {client.access_token}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.headers.get_content_type(), response.read()


def _upload_presigned_post(
    upload_url: str,
    fields: dict[str, str],
    filename: str,
    content_type: str,
    content: bytes,
) -> int:
    boundary = f"----FlowGuard{uuid.uuid4().hex}"
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                str(value).encode(),
                b"\r\n",
            ]
        )
    parts.extend(
        [
            f"--{boundary}\r\n".encode(),
            (
                'Content-Disposition: form-data; name="file"; '
                f'filename="{filename}"\r\n'
            ).encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    request = urllib.request.Request(
        upload_url,
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status


def test_receipt_csv_and_monthly_analytics_against_aws(api_client: ApiClient) -> None:
    expense_id = None
    income_id = None
    receipt_attached = False
    receipt_bytes = b"\x89PNG\r\n\x1a\nflowguard-test"
    try:
        expense = api_client.request(
            "POST",
            "/expenses",
            {
                "description": "Analytics test groceries",
                "amount_minor": 4500,
                "expense_date": "2032-05-10",
                "category": "groceries",
                "status": "cleared",
                "essential": True,
            },
            201,
        ).body["data"]
        expense_id = expense["expense_id"]
        income = api_client.request(
            "POST",
            "/income",
            {
                "source": "Analytics test salary",
                "amount_minor": 200000,
                "expected_date": "2032-05-01",
                "confidence": "guaranteed",
            },
            201,
        ).body["data"]
        income_id = income["income_id"]

        analytics = api_client.request("GET", "/analytics/monthly?year=2032&month=5").body[
            "data"
        ]
        assert analytics["total_income_minor"] == 200000
        assert analytics["total_expenses_minor"] == 4500
        assert analytics["net_cash_flow_minor"] == 195500
        assert analytics["expense_count"] == 1
        assert analytics["category_breakdown"][0]["category"] == "groceries"

        status, content_type, csv_body = _raw_request(
            api_client,
            "/exports/expenses.csv?startDate=2032-05-01&endDate=2032-05-31",
        )
        csv_text = csv_body.decode("utf-8")
        assert status == 200
        assert content_type == "text/csv"
        assert "Analytics test groceries" in csv_text
        assert "45.00" in csv_text

        upload = api_client.request(
            "POST",
            f"/expenses/{expense_id}/receipt-upload",
            {
                "filename": "receipt.png",
                "content_type": "image/png",
                "size_bytes": len(receipt_bytes),
            },
        ).body["data"]
        assert _upload_presigned_post(
            upload["upload_url"],
            upload["fields"],
            "receipt.png",
            "image/png",
            receipt_bytes,
        ) in {200, 201, 204}

        confirmed = api_client.request(
            "POST",
            f"/expenses/{expense_id}/receipt-confirm",
            {"receipt_key": upload["receipt_key"]},
        ).body["data"]
        receipt_attached = True
        assert confirmed["receipt_key"] == upload["receipt_key"]

        download = api_client.request(
            "GET", f"/expenses/{expense_id}/receipt"
        ).body["data"]
        with urllib.request.urlopen(download["download_url"], timeout=30) as response:
            assert response.read() == receipt_bytes

        api_client.request(
            "DELETE", f"/expenses/{expense_id}/receipt", expected_status=204
        )
        receipt_attached = False
        fetched = api_client.request("GET", f"/expenses/{expense_id}").body["data"]
        assert fetched["receipt_key"] is None
    finally:
        if receipt_attached and expense_id:
            api_client.request(
                "DELETE", f"/expenses/{expense_id}/receipt", expected_status=204
            )
        if expense_id:
            api_client.request("DELETE", f"/expenses/{expense_id}", expected_status=204)
        if income_id:
            api_client.request("DELETE", f"/income/{income_id}", expected_status=204)
