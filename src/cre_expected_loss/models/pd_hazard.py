"""Classical discrete-time hazard development pipeline for Fannie MFLPD."""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from ..ingestion.duckdb_io import _duckdb
from .classical import fit_logistic_pd

NUMERIC_FEATURES = (
    "acquisition_ltv",
    "underwritten_dscr",
    "annual_dscr_lag1",
    "note_rate",
    "loan_age",
    "log_current_upb",
    "months_to_maturity",
)
CATEGORICAL_FEATURES = (
    "property_type",
    "property_state",
    "amortization_type",
    "interest_type",
)


def _sql_path(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def _weighted_metrics(actual: Any, probability: Any, weight: Any) -> dict[str, float | int]:
    import numpy as np
    from sklearn.metrics import average_precision_score, log_loss, roc_auc_score

    y = np.asarray(actual, dtype=int)
    p = np.asarray(probability, dtype=float)
    w = np.asarray(weight, dtype=float)
    return {
        "sample_rows": len(y),
        "weighted_observations": float(w.sum()),
        "weighted_events": float((w * y).sum()),
        "weighted_predicted_events": float((w * p).sum()),
        "observed_to_expected": float((w * y).sum() / (w * p).sum()),
        "roc_auc": float(roc_auc_score(y, p, sample_weight=w)),
        "average_precision": float(average_precision_score(y, p, sample_weight=w)),
        "brier_score": float(np.average((y - p) ** 2, weights=w)),
        "log_loss": float(log_loss(y, p, sample_weight=w, labels=[0, 1])),
    }


def fit_fannie_discrete_time_hazard(
    monthly_parquet: Path,
    annual_dscr_parquet: Path,
    artifact_directory: Path,
    *,
    train_end: date,
    validation_end: date,
    negative_sample_rate: float = 0.10,
    random_state: int = 20260901,
) -> dict[str, Any]:
    """Fit a weighted logistic monthly hazard using chronological samples.

    Every event is retained. Non-events are selected by a deterministic hash
    and receive inverse-probability weights. Annual DSCR is joined only from the
    preceding calendar year, a conservative proposed availability convention.
    """
    if not 0.0 < negative_sample_rate <= 1.0:
        raise ValueError("negative_sample_rate must be in (0, 1]")
    if train_end >= validation_end:
        raise ValueError("train_end must be before validation_end")
    for path in (monthly_parquet, annual_dscr_parquet):
        if not Path(path).is_file():
            raise FileNotFoundError(path)
    artifact_directory = Path(artifact_directory)
    artifact_directory.mkdir(parents=True, exist_ok=True)
    model_path = artifact_directory / "model.joblib"
    report_path = artifact_directory / "model_report.json"
    coefficient_path = artifact_directory / "coefficients.csv"
    if model_path.exists() or report_path.exists() or coefficient_path.exists():
        raise FileExistsError(f"Model artifact already exists: {artifact_directory}")

    threshold = round(negative_sample_rate * 10_000)
    connection = _duckdb().connect()
    try:
        connection.execute(
            f"""
            CREATE TEMP VIEW model_frame AS
            WITH dscr AS (
              SELECT loan_id, dscr_year, AVG(annual_dscr) annual_dscr
              FROM read_parquet('{_sql_path(Path(annual_dscr_parquet))}') GROUP BY ALL
            ), risk_set AS (
              SELECT m.*,
                     d.annual_dscr AS annual_dscr_lag1,
                     LN(1 + GREATEST(COALESCE(m.current_upb, 0), 0)) AS log_current_upb,
                     DATE_DIFF('month', m.reporting_date, m.maturity_date) AS months_to_maturity,
                     CASE WHEN m.reporting_date <= DATE '{train_end}' THEN 'train'
                          WHEN m.reporting_date <= DATE '{validation_end}' THEN 'validation'
                          ELSE 'test' END sample_name
              FROM read_parquet('{_sql_path(Path(monthly_parquet))}') m
              LEFT JOIN dscr d ON m.loan_id=d.loan_id
                              AND d.dscr_year=EXTRACT(YEAR FROM m.reporting_date)-1
              WHERE m.reporting_date IS NOT NULL
                AND (m.first_credit_event_date IS NULL OR m.reporting_date <= m.first_credit_event_date)
            )
            SELECT *, CASE WHEN proposed_default_event=1 THEN 1.0
                           ELSE {1.0 / negative_sample_rate} END sample_weight
            FROM risk_set
            WHERE proposed_default_event=1 OR
                  ABS(HASH(loan_id || CAST(reporting_date AS VARCHAR))) % 10000 < {threshold}
            """
        )
        frames = {
            sample_name: connection.execute(
                f"SELECT * FROM model_frame WHERE sample_name='{sample_name}'"
            ).fetch_df()
            for sample_name in ("train", "validation", "test")
        }
    finally:
        connection.close()

    train = frames["train"]
    model = fit_logistic_pd(
        train,
        "proposed_default_event",
        NUMERIC_FEATURES,
        CATEGORICAL_FEATURES,
        class_weight=None,
        random_state=random_state,
        sample_weight=train["sample_weight"],
    )
    import joblib

    joblib.dump(model, model_path)
    feature_names = model.named_steps["features"].get_feature_names_out()
    coefficients = model.named_steps["model"].coef_[0]
    with coefficient_path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["transformed_feature", "log_odds_coefficient"])
        writer.writerows(zip(feature_names, coefficients, strict=True))
    features = list(NUMERIC_FEATURES + CATEGORICAL_FEATURES)
    metrics = {}
    for sample, frame in frames.items():
        probability = model.predict_proba(frame[features])[:, 1]
        metrics[sample] = _weighted_metrics(
            frame["proposed_default_event"], probability, frame["sample_weight"]
        )
    report = {
        "model_id": "fannie_logistic_discrete_time_hazard",
        "model_version": "0.1.1-development",
        "status": "proposed_not_approved",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "target_version": "fannie_outcomes_0.3.0",
        "grain": "loan_month",
        "train_end": train_end.isoformat(),
        "validation_end": validation_end.isoformat(),
        "negative_sample_rate": negative_sample_rate,
        "negative_sample_weight": 1.0 / negative_sample_rate,
        "random_state": random_state,
        "numeric_features": list(NUMERIC_FEATURES),
        "categorical_features": list(CATEGORICAL_FEATURES),
        "coefficient_artifact": coefficient_path.name,
        "annual_dscr_availability_rule": "exact preceding calendar year; proposed",
        "metrics": metrics,
        "limitations": [
            "Default and DSCR availability rules are proposed, not approved.",
            "Sampling-weighted metrics are estimates of full-population metrics.",
            "No macroeconomic or property-market time series are included.",
            "Fannie multifamily results cannot be generalized to all CRE.",
            "The 2023-2026 period has already been viewed and is not a pristine final holdout.",
        ],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
