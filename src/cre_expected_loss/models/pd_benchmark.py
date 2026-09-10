"""Chronological segment/vintage PD benchmark fitted with DuckDB."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from ..ingestion.duckdb_io import _duckdb


def _path(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def fit_segment_pd_benchmark(
    monthly_parquet: Path,
    artifact_directory: Path,
    *,
    train_end: date,
    validation_end: date,
    smoothing_observations: float = 500.0,
) -> dict[str, Any]:
    """Fit and evaluate a smoothed property-type/vintage monthly hazard benchmark."""
    monthly_parquet, artifact_directory = Path(monthly_parquet), Path(artifact_directory)
    if not monthly_parquet.is_file():
        raise FileNotFoundError(monthly_parquet)
    if train_end >= validation_end:
        raise ValueError("train_end must be before validation_end")
    if smoothing_observations < 0:
        raise ValueError("smoothing_observations must be nonnegative")
    artifact_directory.mkdir(parents=True, exist_ok=True)
    rates_path = artifact_directory / "segment_rates.parquet"
    report_path = artifact_directory / "model_report.json"
    if rates_path.exists() or report_path.exists():
        raise FileExistsError(f"Model artifact already exists: {artifact_directory}")

    connection = _duckdb().connect()
    try:
        connection.execute(
            f"""
            CREATE TEMP VIEW risk_set AS
            SELECT *,
                   COALESCE(property_type, 'UNKNOWN') AS model_property_type,
                   COALESCE(CAST(FLOOR(EXTRACT(YEAR FROM acquisition_date) / 5) * 5 AS INTEGER), -1)
                       AS acquisition_vintage,
                   CASE WHEN reporting_date <= DATE '{train_end}' THEN 'train'
                        WHEN reporting_date <= DATE '{validation_end}' THEN 'validation'
                        ELSE 'test' END AS sample
            FROM read_parquet('{_path(monthly_parquet)}')
            WHERE reporting_date IS NOT NULL
              AND (first_credit_event_date IS NULL OR reporting_date <= first_credit_event_date)
            """
        )
        global_rate = float(
            connection.execute(
                "SELECT AVG(proposed_default_event::DOUBLE) FROM risk_set WHERE sample='train'"
            ).fetchone()[0]
        )
        connection.execute(
            f"""
            COPY (
              SELECT model_property_type AS property_type, acquisition_vintage,
                     COUNT(*) AS observations, SUM(proposed_default_event) AS events,
                     (SUM(proposed_default_event) + {smoothing_observations} * {global_rate}) /
                     (COUNT(*) + {smoothing_observations}) AS monthly_hazard
              FROM risk_set WHERE sample='train'
              GROUP BY ALL
            ) TO '{_path(rates_path)}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
        rows = connection.execute(
            f"""
            WITH scored AS (
              SELECT r.sample, r.proposed_default_event AS actual,
                     COALESCE(s.monthly_hazard, {global_rate}) AS probability
              FROM risk_set r
              LEFT JOIN read_parquet('{_path(rates_path)}') s
                ON r.model_property_type=s.property_type
               AND r.acquisition_vintage=s.acquisition_vintage
            )
            SELECT sample, COUNT(*) observations, SUM(actual) events,
                   SUM(probability) predicted_events,
                   AVG(POWER(actual-probability, 2)) brier_score,
                   AVG(-(actual*LN(GREATEST(probability,1e-15)) +
                         (1-actual)*LN(GREATEST(1-probability,1e-15)))) log_loss
            FROM scored GROUP BY sample ORDER BY sample
            """
        ).fetchall()
    finally:
        connection.close()

    report = {
        "model_id": "fannie_segment_vintage_pd_benchmark",
        "model_version": "0.1.0-development",
        "status": "proposed_not_approved",
        "target": "first reported Fannie credit event allocated to last observable pre-event month",
        "grain": "loan_month",
        "train_end": train_end.isoformat(),
        "validation_end": validation_end.isoformat(),
        "smoothing_observations": smoothing_observations,
        "training_global_monthly_hazard": global_rate,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "metrics": {
            sample: {
                "observations": observations,
                "events": events,
                "predicted_events": predicted,
                "observed_to_expected": events / predicted if predicted else None,
                "brier_score": brier,
                "log_loss": log_loss,
            }
            for sample, observations, events, predicted, brier, log_loss in rows
        },
        "limitations": [
            "Credit-event definition and allocation rule are proposed, not approved.",
            "Public Fannie multifamily performance is not representative of all CRE.",
            "This transparent benchmark is not the final discrete-time hazard model.",
            "No macroeconomic scenario variables or annual DSCR are included yet.",
        ],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
