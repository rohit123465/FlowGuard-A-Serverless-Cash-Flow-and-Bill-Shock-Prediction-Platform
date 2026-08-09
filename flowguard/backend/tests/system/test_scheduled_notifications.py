import json
from datetime import date, datetime, timedelta, timezone

import pytest

from tests.conftest import AwsTestEnvironment


pytestmark = [pytest.mark.aws, pytest.mark.system]


def test_scheduled_warning_reaches_authenticated_frontend_api(
    aws_environment: AwsTestEnvironment,
) -> None:
    client = aws_environment.create_user("scheduled-warning")
    commitment_id = None
    today = date.today()
    due_date = today + timedelta(days=1)
    try:
        settings = client.request(
            "PUT",
            "/notifications/settings",
            {
                "enabled": True,
                "opening_balance_minor": 10_000,
                "safety_buffer_minor": 5_000,
                "horizon_days": 30,
                "include_likely_income": False,
            },
        ).body["data"]
        assert settings["enabled"] is True

        commitment = client.request(
            "POST",
            "/commitments",
            {
                "name": "Scheduled warning test bill",
                "amount_minor": 20_000,
                "next_due_date": due_date.isoformat(),
                "recurrence": "once",
                "essential": True,
            },
            201,
        ).body["data"]
        commitment_id = commitment["commitment_id"]

        invocation = aws_environment.lambda_client.invoke(
            FunctionName=aws_environment.scheduled_bill_shock_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps({"time": datetime.now(timezone.utc).isoformat()}).encode(),
        )
        assert invocation["StatusCode"] == 200
        payload = json.loads(invocation["Payload"].read())
        assert payload["warnings_created"] >= 1

        warnings = client.request("GET", "/notifications").body["data"]
        assert len(warnings) == 1
        assert warnings[0]["first_shortfall_date"] == due_date.isoformat()
        assert warnings[0]["shortfall_amount_minor"] == 15_000
        assert 0 <= warnings[0]["risk_probability"] <= 1
        assert warnings[0]["risk_model_version"] == "baseline-logistic-v2-ons-calibrated"
        client.request(
            "PUT",
            f"/notifications/{warnings[0]['notification_id']}/read",
            expected_status=204,
        )
        assert client.request("GET", "/notifications").body["data"][0]["read"] is True
    finally:
        if commitment_id:
            client.request("DELETE", f"/commitments/{commitment_id}", expected_status=204)
        client.request(
            "PUT",
            "/notifications/settings",
            {
                "enabled": False,
                "opening_balance_minor": 0,
                "safety_buffer_minor": 0,
                "horizon_days": 30,
                "include_likely_income": False,
            },
        )
