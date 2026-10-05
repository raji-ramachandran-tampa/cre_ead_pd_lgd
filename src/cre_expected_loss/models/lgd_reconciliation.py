"""Reconcile source-reported Fannie loss ratios; no fitted or approved LGD target."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ..ingestion.duckdb_io import _duckdb


def reconcile_lgd(monthly_parquet: Path, output_directory: Path) -> dict:
    """Write one record per credit-event loan, retaining exclusions and raw tails.

    Source credit-event dates describe dispositions, not default onset. A
    disposition proxy is deliberately not called verified workout resolution.
    """
    source, output = Path(monthly_parquet), Path(output_directory)
    if not source.is_file():
        raise FileNotFoundError(source)
    if output.exists():
        raise FileExistsError(output)
    sql_path = str(source.resolve()).replace("'", "''")
    connection = _duckdb().connect()
    try:
        connection.execute(f"CREATE VIEW monthly AS SELECT * FROM read_parquet('{sql_path}')")
        duplicates = connection.execute("""
            SELECT COUNT(*) FROM (SELECT loan_id, reporting_date, COUNT(*) n
            FROM monthly GROUP BY 1,2 HAVING n > 1)
        """).fetchone()[0]
        event_duplicates = connection.execute("""
            SELECT COUNT(*) FROM (SELECT loan_id, reporting_date, COUNT(*) n
            FROM monthly WHERE first_credit_event_date IS NOT NULL
            GROUP BY 1,2 HAVING n > 1)
        """).fetchone()[0]
        if event_duplicates:
            raise ValueError(
                "Duplicate credit-event loan/reporting-date keys require reconciliation"
            )
        cutoff = connection.execute("SELECT MAX(reporting_date) FROM monthly").fetchone()[0]
        frame = connection.execute("""
            WITH history AS (
                SELECT loan_id, COUNT(*) history_rows,
                    COUNT(DISTINCT default_amount) default_amount_values,
                    COUNT(DISTINCT lifetime_net_credit_loss_amount) loss_amount_values,
                    COUNT(DISTINCT first_credit_event_date) event_date_values
                FROM monthly WHERE first_credit_event_date IS NOT NULL GROUP BY 1
            ), latest AS (
                SELECT * FROM monthly WHERE first_credit_event_date IS NOT NULL
                QUALIFY ROW_NUMBER() OVER(PARTITION BY loan_id ORDER BY reporting_date DESC)=1
            ), features AS (
                SELECT loan_id, reporting_date feature_date, acquisition_ltv,
                    underwritten_dscr, property_type, property_state
                FROM monthly WHERE reporting_date < first_credit_event_date
                QUALIFY ROW_NUMBER() OVER(PARTITION BY loan_id ORDER BY reporting_date DESC)=1
            )
            SELECT l.loan_id, l.first_credit_event_date AS credit_event_date,
                l.credit_event_type, l.reporting_date AS source_record_date,
                l.liquidation_date, l.liquidation_code, l.default_amount,
                l.lifetime_net_credit_loss_amount AS reported_net_loss,
                h.history_rows, h.default_amount_values, h.loss_amount_values,
                h.event_date_values, f.feature_date, f.acquisition_ltv,
                f.underwritten_dscr, f.property_type, f.property_state
            FROM latest l JOIN history h USING(loan_id)
                LEFT JOIN features f USING(loan_id) ORDER BY l.loan_id
        """).fetchdf()
    finally:
        connection.close()
    if frame.empty:
        raise ValueError("No credit-event loans to reconcile")
    frame["disposition_proxy"] = (
        frame.credit_event_type.isin(["REO", "Non-REO"])
        & frame.credit_event_date.notna()
        & (frame.credit_event_date <= pd.Timestamp(cutoff))
        & frame.liquidation_date.notna()
        & (frame.liquidation_date <= pd.Timestamp(cutoff))
    )
    frame["status"] = np.select(
        [
            (frame.event_date_values != 1)
            | (frame.default_amount_values > 1)
            | (frame.loss_amount_values > 1),
            ~frame.disposition_proxy,
            frame.default_amount.isna()
            | ~np.isfinite(frame.default_amount)
            | (frame.default_amount <= 0),
            frame.reported_net_loss.isna() | ~np.isfinite(frame.reported_net_loss),
            frame.reported_net_loss < 0,
            frame.feature_date.isna(),
        ],
        [
            "conflicting_history",
            "unverified_disposition",
            "invalid_default_amount",
            "missing_or_invalid_loss",
            "negative_loss",
            "missing_prior_features",
        ],
        default="research_eligible",
    )
    # Preserve every computable source ratio; never impute zero or cap tails.
    frame["reported_loss_ratio"] = np.where(
        np.isfinite(frame.default_amount)
        & (frame.default_amount > 0)
        & np.isfinite(frame.reported_net_loss),
        frame.reported_net_loss / frame.default_amount,
        np.nan,
    )
    frame["ratio_above_one"] = frame.reported_loss_ratio > 1
    frame["explicit_zero_loss"] = frame.reported_net_loss.eq(0)
    frame["credit_event_year"] = frame.credit_event_date.dt.year
    eligible = frame.loc[frame.status.eq("research_eligible")]
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    report = {
        "status": "research_reconciliation_not_approved_target",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": str(source.resolve()),
        "source_sha256": digest.hexdigest(),
        "source_cutoff": cutoff.isoformat(),
        "credit_event_loans": len(frame),
        "source_duplicate_key_groups": duplicates,
        "credit_event_duplicate_key_groups": event_duplicates,
        "status_counts": {str(k): int(v) for k, v in frame.status.value_counts().items()},
        "overlapping_flags": {
            "missing_default_amount": int(frame.default_amount.isna().sum()),
            "missing_loss": int(frame.reported_net_loss.isna().sum()),
            "explicit_zero_loss": int(frame.explicit_zero_loss.sum()),
            "ratio_above_one": int(frame.ratio_above_one.sum()),
        },
        "eligible_diagnostics": {
            "rows": len(eligible),
            "positive_losses": int((eligible.reported_net_loss > 0).sum()),
            "zero_losses": int(eligible.explicit_zero_loss.sum()),
            "mean_ratio": float(eligible.reported_loss_ratio.mean()) if len(eligible) else None,
            "exposure_weighted_ratio": float(
                eligible.reported_net_loss.sum() / eligible.default_amount.sum()
            )
            if len(eligible)
            else None,
        },
        "limitations": [
            "Reported loss includes interest, expenses, loss sharing and insurance effects.",
            "No dated recovery cash flows: this is not discounted workout LGD.",
            "Credit event is disposition, not true default onset; prior features are pre-disposition.",
            "Finalization and historical publication timestamps are unavailable.",
            "Chronological event splits alone cannot establish point-in-time label availability.",
            "Missing outcomes are excluded, not zero; selection and unresolved-case bias remain.",
            "Ratios above one are preserved. No model selection or use approval is implied.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lgd-stage-", dir=output.parent) as temporary:
        stage = Path(temporary) / "artifacts"
        stage.mkdir()
        frame.to_parquet(stage / "loan_reconciliation.parquet", index=False)
        frame.groupby(["credit_event_year", "status"], dropna=False).size().rename(
            "loans"
        ).reset_index().to_csv(stage / "annual_status.csv", index=False)
        (stage / "reconciliation.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        stage.rename(output)
    return report
