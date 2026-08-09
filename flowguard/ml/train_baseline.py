"""Train FlowGuard's reproducible synthetic logistic-regression baseline."""

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


def generate_synthetic_scenarios(rows: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    gap = rng.normal(0.8, 1.1, rows)
    guaranteed = rng.gamma(1.7, 0.8, rows)
    likely = rng.gamma(1.2, 0.45, rows)
    expenses = rng.gamma(1.8, 0.55, rows)
    commitments = rng.gamma(1.6, 0.75, rows)
    essential = np.minimum(expenses + commitments, rng.gamma(1.5, 0.65, rows))
    days = rng.integers(0, 32, rows).astype(float)
    events = rng.integers(0, 20, rows).astype(float)
    x = np.column_stack([gap, guaranteed, likely, expenses, commitments, essential, days, events])

    # Simulates uncertainty unavailable to the deterministic forecast: surprise
    # costs and likely income failing to arrive. Labels remain synthetic.
    late_likely_income = rng.binomial(1, 0.35, rows) * likely
    surprise_outflow = rng.gamma(1.1, 0.35, rows)
    latent = (
        -1.0 - 2.0 * gap - 0.65 * guaranteed - 0.12 * likely
        + 0.8 * expenses + 1.05 * commitments + 0.35 * essential
        + 0.035 * days + 0.025 * events + 0.75 * late_likely_income
        + 0.9 * surprise_outflow + rng.normal(0, 0.55, rows)
    )
    probability = 1 / (1 + np.exp(-np.clip(latent, -30, 30)))
    return x, rng.binomial(1, probability).astype(int)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=12_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "artifacts")
    parser.add_argument("--upload-bucket")
    parser.add_argument("--upload-key", default="models/baseline-logistic-v1.json")
    parser.add_argument("--profile", default="flowguard-dev")
    parser.add_argument("--region", default="eu-west-2")
    args = parser.parse_args()

    x, y = generate_synthetic_scenarios(args.rows, args.seed)
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
        "model_version": "baseline-logistic-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_data": "synthetic",
        "label_definition": "simulated balance falls below the safety buffer within the forecast window",
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
    model_path = args.output_dir / "baseline-logistic-v1.json"
    model_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    with (args.output_dir / "synthetic-evaluation-sample.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output); writer.writerow([*FEATURE_NAMES, "label"])
        writer.writerows([*row, int(label)] for row, label in zip(x_test[:500], y_test[:500], strict=True))
    print(json.dumps(metrics, indent=2))
    if args.upload_bucket:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        session.client("s3").upload_file(str(model_path), args.upload_bucket, args.upload_key)
        print(f"Uploaded s3://{args.upload_bucket}/{args.upload_key}")


if __name__ == "__main__":
    main()
