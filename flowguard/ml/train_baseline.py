"""Train FlowGuard's ONS-calibrated synthetic logistic-regression risk model."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import boto3
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_NAMES = [
    "balance_buffer_gap_ratio", "guaranteed_income_ratio", "likely_income_ratio",
    "expense_outflow_ratio", "commitment_outflow_ratio", "essential_outflow_ratio",
    "days_to_next_guaranteed_income", "scheduled_event_count",
]
DEFAULT_PUBLIC_DATA = Path(__file__).parent / "public_data" / "ons-family-spending-fye2024.json"
MODEL_VERSION = "baseline-logistic-v2-ons-calibrated"


def load_public_calibration(path: Path) -> dict:
    calibration = json.loads(path.read_text(encoding="utf-8"))
    if len(calibration.get("deciles", [])) != 10:
        raise ValueError("public calibration must contain ten income deciles")
    return calibration


def _falls_below_buffer(
    rng: np.random.Generator,
    opening: float,
    buffer: float,
    guaranteed: float,
    likely: float,
    outflow: float,
    income_day: int,
    event_count: int,
) -> int:
    events: list[tuple[int, float]] = [(income_day, guaranteed)]
    if rng.random() >= 0.35:  # uncertain income sometimes arrives late or outside the window
        events.append((int(rng.integers(0, 31)), likely))
    pieces = max(1, event_count - 2)
    weights = rng.dirichlet(np.ones(pieces))
    events.extend((int(rng.integers(0, 31)), -outflow * weight) for weight in weights)
    surprise = rng.gamma(1.15, outflow * 0.045)
    events.append((int(rng.integers(0, 31)), -surprise))
    balance = opening
    minimum = opening
    for _, amount in sorted(events, key=lambda item: item[0]):
        balance += amount
        minimum = min(minimum, balance)
    return int(minimum < buffer)


def generate_public_calibrated_scenarios(
    rows: int, seed: int, calibration: dict
) -> tuple[np.ndarray, np.ndarray]:
    """Generate account scenarios whose income/outgoings follow ONS decile aggregates.

    ONS rows are aggregate household statistics, so they calibrate distributions;
    they are not copied or represented as individual bank-account observations.
    """
    rng = np.random.default_rng(seed)
    deciles = calibration["deciles"]
    x = np.zeros((rows, len(FEATURE_NAMES)), dtype=float)
    y = np.zeros(rows, dtype=int)
    weeks_per_month = 52 / 12

    for index in range(rows):
        decile = deciles[int(rng.integers(0, len(deciles)))]
        monthly_income = decile["mean_disposable_income"] * weeks_per_month * rng.lognormal(0, 0.20)
        monthly_outflow = decile["total_expenditure"] * weeks_per_month * rng.lognormal(0, 0.18)
        essential_share = min(1.0, decile["essential_expenditure"] / decile["total_expenditure"])

        likely_share = rng.beta(1.4, 8.0) * 0.45
        guaranteed = monthly_income * (1 - likely_share)
        likely = monthly_income * likely_share
        commitment_share = rng.uniform(0.42, 0.72)
        commitments = monthly_outflow * commitment_share
        expenses = monthly_outflow - commitments
        essential = monthly_outflow * np.clip(rng.normal(essential_share, 0.06), 0.2, 0.95)

        safety_buffer = monthly_income * rng.uniform(0.10, 0.55)
        opening = monthly_income * rng.lognormal(-0.65, 0.75)
        scale = max(abs(opening), safety_buffer, 100.0)
        income_day = int(rng.integers(0, 31))
        event_count = int(np.clip(rng.poisson(8) + 2, 2, 24))

        x[index] = [
            (opening - safety_buffer) / scale,
            guaranteed / scale,
            likely / scale,
            expenses / scale,
            commitments / scale,
            essential / scale,
            float(income_day),
            float(event_count),
        ]
        y[index] = _falls_below_buffer(
            rng, opening, safety_buffer, guaranteed, likely,
            monthly_outflow, income_day, event_count,
        )
    return x, y


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=12_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--public-data", type=Path, default=DEFAULT_PUBLIC_DATA)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "artifacts")
    parser.add_argument("--upload-bucket")
    parser.add_argument("--upload-key", default=f"models/{MODEL_VERSION}.json")
    parser.add_argument("--profile", default="flowguard-dev")
    parser.add_argument("--region", default="eu-west-2")
    args = parser.parse_args()

    calibration = load_public_calibration(args.public_data)
    x, y = generate_public_calibrated_scenarios(args.rows, args.seed, calibration)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=args.seed, stratify=y
    )
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1_000, class_weight="balanced", random_state=args.seed)),
    ])
    pipeline.fit(x_train, y_train)
    probabilities = pipeline.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions)), 4),
        "recall": round(float(recall_score(y_test, predictions)), 4),
        "f1": round(float(f1_score(y_test, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "brier_score": round(float(brier_score_loss(y_test, probabilities)), 4),
        "positive_rate": round(float(y.mean()), 4),
        "test_rows": len(y_test),
    }
    scaler = pipeline.named_steps["scaler"]
    model = pipeline.named_steps["model"]
    artifact = {
        "model_version": MODEL_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_data": "public-data-informed synthetic scenarios",
        "public_data": {
            "publisher": calibration["publisher"],
            "title": calibration["title"],
            "period": calibration["period"],
            "source_url": calibration["source_url"],
        },
        "label_definition": "simulated balance falls below the safety buffer within a 30-day forecast window",
        "seed": args.seed,
        "training_rows": len(y_train),
        "feature_names": FEATURE_NAMES,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "coefficients": model.coef_[0].tolist(),
        "intercept": float(model.intercept_[0]),
        "metrics": metrics,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.output_dir / f"{MODEL_VERSION}.json"
    model_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    with (args.output_dir / "public-calibrated-evaluation-sample.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow([*FEATURE_NAMES, "label"])
        writer.writerows([*row, int(label)] for row, label in zip(x_test[:500], y_test[:500], strict=True))
    print(json.dumps(metrics, indent=2))
    if args.upload_bucket:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        session.client("s3").upload_file(str(model_path), args.upload_bucket, args.upload_key)
        print(f"Uploaded s3://{args.upload_bucket}/{args.upload_key}")


if __name__ == "__main__":
    main()
