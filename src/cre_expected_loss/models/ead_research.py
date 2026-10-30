"""Scheduled-principal EAD research: contractual proxy and fixed ridge challenger."""

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .ead_amortization import scheduled_balance

FEATURES = [
    "schedule_fraction",
    "loan_age",
    "note_rate",
    "remaining_io",
    "months_to_maturity",
    "log_anchor_upb",
]


def prepare(frame):
    frame = frame.copy()
    rows = []
    for r in frame.itertuples():
        reason = "supported"
        io = 0
        if pd.isna(r.anchor_date) or pd.isna(r.maturity_date):
            reason = "missing_dates"
        elif r.onset_date.to_period("M") >= r.maturity_date.to_period("M"):
            reason = "at_or_beyond_maturity"
        elif pd.notna(r.modification_date):
            reason = "modified_schedule_unverified"
        elif r.interest_type != "Fixed":
            reason = "nonfixed_rate"
        elif any(
            not np.isfinite(x)
            for x in [r.loan_age, r.note_rate, r.amortization_months, r.anchor_upb]
        ):
            reason = "missing_schedule_inputs"
        elif r.anchor_upb <= 0 or r.note_rate < 0 or r.loan_age < 0 or r.amortization_months <= 0:
            reason = "invalid_schedule_inputs"
        elif not float(r.loan_age).is_integer() or not float(r.amortization_months).is_integer():
            reason = "noninteger_term"
        if reason == "supported" and "Interest Only" in str(r.amortization_type):
            if pd.isna(r.io_end_date):
                reason = "missing_io_end"
            else:
                io = max(
                    0,
                    (r.io_end_date.year - r.anchor_date.year) * 12
                    + r.io_end_date.month
                    - r.anchor_date.month,
                )
        elif reason == "supported" and r.amortization_type not in [
            "Fully Amortizing",
            "Amortizing Balloon",
        ]:
            reason = "unknown_amortization_type"
        primary = alternative = np.nan
        if reason == "supported":
            n = int(r.amortization_months - r.loan_age - io)
            # Primary elapsed-calendar convention: remaining at start of repayment.
            if n <= 0 and r.horizon_months > io:
                reason = "exhausted_original_amortization"
            else:
                primary = scheduled_balance(
                    r.anchor_upb, r.note_rate / 100, max(n, 0), int(r.horizon_months), io
                )
                if "Interest Only" in str(r.amortization_type) and not np.isfinite(r.io_months):
                    alternative = np.nan
                else:
                    io_original = r.io_months if "Interest Only" in str(r.amortization_type) else 0
                    n_alt = int(r.amortization_months - max(0, r.loan_age - io_original))
                    if n_alt > 0 or r.horizon_months <= io:
                        alternative = scheduled_balance(
                            r.anchor_upb,
                            r.note_rate / 100,
                            max(n_alt, 0),
                            int(r.horizon_months),
                            io,
                        )
        rows.append((reason, io, primary, alternative))
    frame[
        ["schedule_status", "remaining_io", "amortization_prediction", "io_clock_sensitivity"]
    ] = pd.DataFrame(rows, index=frame.index)
    frame["schedule_fraction"] = frame.amortization_prediction / frame.anchor_upb
    frame["months_to_maturity"] = (
        (frame.maturity_date.dt.year - frame.anchor_date.dt.year) * 12
        + frame.maturity_date.dt.month
        - frame.anchor_date.dt.month
    )
    frame["log_anchor_upb"] = np.log(frame.anchor_upb.clip(lower=1))
    return frame


def score(frame, column):
    error = frame[column] - frame.onset_scheduled_upb
    return {
        "cases": len(frame),
        "mae_dollars": float(error.abs().mean()),
        "absolute_error_over_actual": float(error.abs().sum() / frame.onset_scheduled_upb.sum()),
        "bias_over_actual": float(error.sum() / frame.onset_scheduled_upb.sum()),
        "p90_absolute_relative_error": float(
            (error.abs() / frame.onset_scheduled_upb).quantile(0.9)
        ),
    }


def run(source: Path, output: Path):
    if output.exists():
        raise FileExistsError(output)
    cases = prepare(pd.read_parquet(source / "benchmark_cases.parquet"))
    performing = prepare(pd.read_parquet(source / "performing_schedule_cases.parquet"))
    # No learned convention chosen using later outcomes: both reported.
    perf = performing[
        performing.schedule_status.eq("supported") & performing.onset_scheduled_upb.gt(0)
    ].copy()
    perf["balance_hold_prediction"] = perf.anchor_upb
    performance = {
        c: score(perf[perf[c].notna()], c)
        for c in ["balance_hold_prediction", "amortization_prediction", "io_clock_sensitivity"]
    }
    eligible = cases[cases.eligible & cases.schedule_status.eq("supported")].copy()
    models = {}
    metrics = []
    for horizon, g in eligible.groupby("horizon_months"):
        train = g[g.partition.eq("through_2018")]
        model = make_pipeline(StandardScaler(), Ridge(alpha=10))
        # Conditional arithmetic-mean balance ratio; no clipping or later tuning.
        model.fit(train[FEATURES], train.onset_scheduled_upb / train.anchor_upb - 1)
        eligible.loc[g.index, "ridge_prediction"] = g.anchor_upb * (1 + model.predict(g[FEATURES]))
        models[int(horizon)] = model
    for (horizon, partition), g in eligible.groupby(["horizon_months", "partition"]):
        for column in [
            "balance_hold_prediction",
            "amortization_prediction",
            "io_clock_sensitivity",
            "ridge_prediction",
        ]:
            metrics.append(
                {
                    "horizon_months": int(horizon),
                    "partition": partition,
                    "candidate": column,
                    **score(g[g[column].notna()], column),
                }
            )
    if not np.isfinite(eligible.ridge_prediction).all() or eligible.ridge_prediction.lt(0).any():
        raise ValueError("Nonfinite or negative ridge exposure; no silent repair")
    report = {
        "status": "scheduled_principal_research_candidates_no_selection",
        "source_audit_report_sha256": hashlib.sha256(
            (source / "report.json").read_bytes()
        ).hexdigest(),
        "benchmark_input_sha256": hashlib.sha256(
            (source / "benchmark_cases.parquet").read_bytes()
        ).hexdigest(),
        "performing_input_sha256": hashlib.sha256(
            (source / "performing_schedule_cases.parquet").read_bytes()
        ).hexdigest(),
        "coverage": cases[cases.eligible]
        .groupby(["horizon_months", "schedule_status"])
        .size()
        .reset_index(name="cases")
        .to_dict("records"),
        "performing_check": performance,
        "performing_supported_loans": int(perf.loan_id.nunique()),
        "metrics": metrics,
        "features": FEATURES,
        "ridge_alpha": 10,
        "primary_schedule": "Calendar age reduces original amortization term; additional IO months also reduce remaining term before repayment",
        "sensitivity": "Amortization clock starts after original IO; not selected by accuracy",
        "limits": [
            "Scheduled principal at first observed SDQ, not actual funded economic EAD",
            "Only fixed rate, no documented modifications, supported terms, strictly before maturity",
            "No future draws, accrued interest, advances or contractual default verification",
            "Principal-only benchmark does not change LGD denominator or PD event timing",
            "Performing sample has overlapping windows and uses clean-history outcome selection",
            "Ridge estimates arithmetic mean normalized balance; enforce nonnegative scored outputs",
            "Through2018 metrics are training fit; later periods examined, not independent validation",
            "No tuning, macro selection, clipping, cap or automatic aggregation",
        ],
    }
    output.mkdir(parents=True)
    joblib.dump(models, output / "models.joblib")
    reloaded = joblib.load(output / "models.joblib")
    for horizon, g in eligible.groupby("horizon_months"):
        np.testing.assert_allclose(
            g.anchor_upb * (1 + reloaded[int(horizon)].predict(g[FEATURES])),
            g.ridge_prediction,
            rtol=1e-12,
            atol=1e-8,
        )
    eligible.to_parquet(output / "predictions.parquet", index=False)
    report["reload_verified_cases"] = len(eligible)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)
