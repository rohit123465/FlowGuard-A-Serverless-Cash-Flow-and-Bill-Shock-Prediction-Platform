import json
import math
from functools import lru_cache
from typing import Any

from ..config import get_settings
from ..database import get_s3_client
from ..models.risk import RiskPrediction


@lru_cache
def load_risk_model() -> dict[str, Any]:
    settings = get_settings()
    if not settings.model_bucket_name or not settings.model_object_key:
        raise RuntimeError("ML model location is not configured")
    response = get_s3_client().get_object(
        Bucket=settings.model_bucket_name,
        Key=settings.model_object_key,
    )
    return json.loads(response["Body"].read())


def predict_risk(features: dict[str, float], model: dict[str, Any]) -> RiskPrediction:
    names = model["feature_names"]
    standardized = [
        (features[name] - model["scaler_mean"][index]) / model["scaler_scale"][index]
        for index, name in enumerate(names)
    ]
    score = model["intercept"] + sum(
        coefficient * value
        for coefficient, value in zip(model["coefficients"], standardized, strict=True)
    )
    probability = 1 / (1 + math.exp(-max(-700, min(700, score))))
    risk_level = "high" if probability >= 0.7 else "medium" if probability >= 0.4 else "low"
    contributions = sorted(
        zip(names, (coefficient * value for coefficient, value in zip(model["coefficients"], standardized, strict=True)), strict=True),
        key=lambda item: abs(item[1]),
        reverse=True,
    )[:3]
    labels = {
        "balance_buffer_gap_ratio": "balance available above the safety buffer",
        "guaranteed_income_ratio": "guaranteed expected income",
        "likely_income_ratio": "lower-confidence expected income",
        "expense_outflow_ratio": "scheduled expenses",
        "commitment_outflow_ratio": "upcoming commitments",
        "essential_outflow_ratio": "essential outgoings",
        "days_to_next_guaranteed_income": "time until guaranteed income",
        "scheduled_event_count": "number of scheduled cash-flow events",
    }
    explanation = tuple(
        f"{labels[name]} {'increased' if contribution > 0 else 'reduced'} estimated risk"
        for name, contribution in contributions
    )
    return RiskPrediction(
        probability=round(probability, 4),
        risk_level=risk_level,
        model_version=model["model_version"],
        model_type="logistic_regression",
        training_data="synthetic",
        features={name: round(features[name], 4) for name in names},
        explanation=explanation,
        disclaimer="Experimental estimate trained on synthetic scenarios; not financial advice or a guaranteed outcome.",
    )
