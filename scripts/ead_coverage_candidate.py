"""Explicit EAD research routing; fallbacks are proxies, not verified schedules."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cre_expected_loss.models.ead_research import prepare, score


def run(source, models, output):
    if output.exists():
        raise FileExistsError(output)
    frame = prepare(pd.read_parquet(source / "benchmark_cases.parquet"))
    fitted = pd.read_parquet(models / "predictions.parquet")
    frame = frame[frame.eligible].merge(
        fitted[["loan_id", "horizon_months", "ridge_prediction"]],
        on=["loan_id", "horizon_months"],
        how="left",
        validate="one_to_one",
    )
    # Known end date implies no scheduled principal amortization within IO.
    # Fully funded/no draw/no capitalization assumption remains explicit.
    within = (
        frame.amortization_type.str.contains("Interest Only", na=False)
        & frame.io_end_date.notna()
        & (frame.io_end_date.dt.to_period("M") >= frame.onset_date.dt.to_period("M"))
    )
    within &= (
        frame.interest_type.eq("Fixed")
        & frame.modification_date.isna()
        & frame.maturity_date.notna()
        & (frame.onset_date.dt.to_period("M") < frame.maturity_date.dt.to_period("M"))
    )
    supported = frame.schedule_status.eq("supported") & frame.io_clock_sensitivity.notna()
    frame["route"] = np.select(
        [within, supported, frame.schedule_status.eq("at_or_beyond_maturity")],
        ["io_principal_hold", "supported_post_io_schedule", "unpaid_maturity_hold"],
        default="unverified_schedule_hold",
    )
    frame["coverage_prediction"] = np.where(supported, frame.io_clock_sensitivity, frame.anchor_upb)
    frame.loc[within, "coverage_prediction"] = frame.loc[within, "anchor_upb"]
    frame["guarded_ridge_prediction"] = frame.ridge_prediction
    frame.loc[within & frame.ridge_prediction.notna(), "guarded_ridge_prediction"] = frame.loc[
        within & frame.ridge_prediction.notna(), "anchor_upb"
    ]
    if frame.duplicated(["loan_id", "horizon_months"]).any():
        raise ValueError("Duplicate routed exposure")
    if not np.isfinite(frame.coverage_prediction).all() or frame.coverage_prediction.lt(0).any():
        raise ValueError("Invalid routed EAD; no clipping")
    maturity = frame.route.eq("unpaid_maturity_hold")
    np.testing.assert_array_equal(
        frame.loc[maturity, "coverage_prediction"], frame.loc[maturity, "anchor_upb"]
    )
    metrics = []
    for (horizon, partition), g in frame.groupby(["horizon_months", "partition"]):
        for c in ["balance_hold_prediction", "coverage_prediction"]:
            metrics.append(
                {
                    "population": "all_initial_eligible",
                    "horizon_months": int(horizon),
                    "partition": partition,
                    "candidate": c,
                    **score(g, c),
                }
            )
        matched = g[g.ridge_prediction.notna()]
        for c in ["ridge_prediction", "guarded_ridge_prediction"]:
            metrics.append(
                {
                    "population": "supported_ridge_only",
                    "horizon_months": int(horizon),
                    "partition": partition,
                    "candidate": c,
                    **score(matched, c),
                }
            )
    report = {
        "status": "research_coverage_candidate_not_selected_baseline",
        "model_report_sha256": hashlib.sha256((models / "report.json").read_bytes()).hexdigest(),
        "source_report_sha256": hashlib.sha256((source / "report.json").read_bytes()).hexdigest(),
        "routes": frame.groupby(["horizon_months", "route"])
        .size()
        .reset_index(name="cases")
        .to_dict("records"),
        "metrics": metrics,
        "limits": [
            "Proxy scheduled principal target; not broad economic EAD",
            "Hold fallback is explicit assumption, not recovered missing schedule",
            "IO assumes no new draws, principal capitalization or changed schedule",
            "Maturity route retains unpaid exposure; no predicted payoff or refinance",
            "No new fit/tuning, unchanged frozen ridge and postIO sensitivity",
            "Later outcomes already examined; no independent validation",
            "Principal/accrual/participation denominator reconciliation still open",
        ],
    }
    output.mkdir(parents=True)
    frame.to_parquet(output / "predictions.parquet", index=False)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ["source", "models", "output"]:
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.source, a.models, a.output)
