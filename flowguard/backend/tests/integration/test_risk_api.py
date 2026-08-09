from datetime import date, timedelta

import pytest

from tests.conftest import ApiClient


pytestmark = [pytest.mark.aws, pytest.mark.integration]


def test_logistic_baseline_against_deployed_api(api_client: ApiClient) -> None:
    commitment_id = None
    start = date.today()
    end = start + timedelta(days=29)
    try:
        commitment = api_client.request(
            "POST",
            "/commitments",
            {
                "name": "ML integration test bill",
                "amount_minor": 150_000,
                "next_due_date": (start + timedelta(days=5)).isoformat(),
                "recurrence": "once",
                "essential": True,
            },
            201,
        ).body["data"]
        commitment_id = commitment["commitment_id"]
        result = api_client.request(
            "GET",
            "/ml/risk?"
            f"openingBalanceMinor=100000&safetyBufferMinor=20000&startDate={start}"
            f"&endDate={end}&includeLikelyIncome=false",
        ).body["data"]
        assert 0 <= result["probability"] <= 1
        assert result["risk_level"] in {"low", "medium", "high"}
        assert result["model_version"] == "baseline-logistic-v2-ons-calibrated"
        assert result["model_type"] == "logistic_regression"
        assert result["training_data"] == "public-data-informed synthetic scenarios"
        assert result["features"]["commitment_outflow_ratio"] == 1.5
        assert len(result["explanation"]) == 3
    finally:
        if commitment_id:
            api_client.request("DELETE", f"/commitments/{commitment_id}", expected_status=204)
