import json
from datetime import date
from pathlib import Path

from src.models.commitment import Commitment
from src.models.expense import Expense
from src.models.forecast import ForecastRequest
from src.models.income import ExpectedIncome
from src.services.risk_feature_service import FEATURE_NAMES, build_risk_features
from src.services.risk_model_service import predict_risk


def test_shared_feature_builder_uses_financial_records() -> None:
    request = ForecastRequest(
        opening_balance_minor=100_000,
        safety_buffer_minor=20_000,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 30),
    )
    features = build_risk_features(
        request,
        [ExpectedIncome(source="Salary", amount_minor=200_000, expected_date=date(2026, 8, 10), confidence="guaranteed")],
        [Commitment(name="Rent", amount_minor=80_000, next_due_date=date(2026, 8, 15), recurrence="once", essential=True)],
        [Expense(description="Food", amount_minor=10_000, expense_date=date(2026, 8, 5), category="food", essential=True)],
    )
    assert tuple(features) == FEATURE_NAMES
    assert features["balance_buffer_gap_ratio"] == 0.8
    assert features["guaranteed_income_ratio"] == 2.0
    assert features["commitment_outflow_ratio"] == 0.8
    assert features["essential_outflow_ratio"] == 0.9
    assert features["days_to_next_guaranteed_income"] == 9


def test_trained_baseline_returns_bounded_explainable_probability() -> None:
    artifact_path = Path(__file__).parents[3] / "ml" / "artifacts" / "baseline-logistic-v1.json"
    model = json.loads(artifact_path.read_text(encoding="utf-8"))
    features = dict.fromkeys(model["feature_names"], 0.0)
    prediction = predict_risk(features, model)
    assert 0 <= prediction.probability <= 1
    assert prediction.risk_level in {"low", "medium", "high"}
    assert prediction.training_data == "synthetic"
    assert len(prediction.explanation) == 3


def test_more_outgoings_increase_baseline_risk() -> None:
    artifact_path = Path(__file__).parents[3] / "ml" / "artifacts" / "baseline-logistic-v1.json"
    model = json.loads(artifact_path.read_text(encoding="utf-8"))
    safe = dict.fromkeys(model["feature_names"], 0.0)
    safe["balance_buffer_gap_ratio"] = 2.0
    risky = safe | {"balance_buffer_gap_ratio": -0.5, "commitment_outflow_ratio": 3.0, "expense_outflow_ratio": 2.0}
    assert predict_risk(risky, model).probability > predict_risk(safe, model).probability
