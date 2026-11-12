"""EAD deterministic payment reconstruction from strictly prior balance history."""

import argparse
import hashlib
import json
from math import exp, expm1, isfinite, log1p
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from .ead_research import prepare, score


def inferred_payment(balances, annual_rate):
    """Median of three implied payments, with prespecified stability gate.

    Monthly balances must be four consecutive, positive end-period observations.
    Rate is annual decimal. $1 or0.1% of implied payment is a mechanical stability
    tolerance, not a policy limit or threshold tuned on future outcomes.
    """
    b = np.asarray(balances, dtype=float)
    if b.shape != (4,) or not np.isfinite(b).all() or (b <= 0).any():
        raise ValueError("Four positive finite monthly balances required")
    if not isfinite(annual_rate) or annual_rate < 0:
        raise ValueError("Invalid rate")
    p = b[:-1] * (1 + annual_rate / 12) - b[1:]
    median = float(np.median(p))
    if median < 0:
        raise ValueError("Negative implied payment")
    if np.max(p) - np.min(p) > max(1.0, abs(median) * 0.001):
        raise ValueError("Unstable implied payment")
    return median


def project_payment(balance, annual_rate, payment, months):
    if any(not isfinite(x) or x < 0 for x in [balance, annual_rate, payment]):
        raise ValueError("Finite nonnegative values required")
    if isinstance(months, bool) or not isinstance(months, int) or months < 0:
        raise ValueError("Integer nonnegative horizon required")
    r = annual_rate / 12
    result = (
        balance - payment * months
        if r == 0
        else balance * exp(months * log1p(r)) - payment * expm1(months * log1p(r)) / r
    )
    if not isfinite(result) or result < 0:
        raise ValueError("Schedule exhausted or invalid; no inferred balloon payoff")
    return result


def run(root, output):
    if output.exists():
        raise FileExistsError(output)
    a = root / "artifacts/2026Q1"
    source = a / "ead-source-audit-v0.2.0/benchmark_cases.parquet"
    frozen = a / "ead-advanced-residual-v0.1.1/predictions.parquet"
    monthly = root / "processed/2026Q1/v0.3.0/fannie_monthly.parquet"
    frame = prepare(pd.read_parquet(source))
    frame = frame[frame.eligible].copy()
    con = duckdb.connect()
    con.register("anchors", frame[["loan_id", "horizon_months", "anchor_date"]])
    history = con.execute(
        """SELECT DISTINCT a.loan_id,a.horizon_months,a.anchor_date,
        m.reporting_date,m.current_upb,m.note_rate,m.maturity_date,m.payment_status,m.sdq_indicator
        FROM read_parquet(?) m JOIN anchors a ON m.loan_id=a.loan_id
        AND m.reporting_date>=date_trunc('month',a.anchor_date)-INTERVAL '3 months'
        AND m.reporting_date<=a.anchor_date
        ORDER BY a.loan_id,a.horizon_months,m.reporting_date""",
        [str(monthly)],
    ).fetchdf()
    con.close()
    histories = {
        (loan, int(h)): g for (loan, h), g in history.groupby(["loan_id", "horizon_months"])
    }
    frame["post_io_reference"] = np.where(
        frame.schedule_status.eq("supported") & frame.io_clock_sensitivity.notna(),
        frame.io_clock_sensitivity,
        frame.anchor_upb,
    )
    reasons = []
    payments = []
    predictions = []
    for r in frame.itertuples():
        reason = "reconstructed_payment"
        payment = np.nan
        result = r.post_io_reference
        h = histories.get((r.loan_id, int(r.horizon_months)))
        is_io = "Interest Only" in str(r.amortization_type)
        if r.interest_type != "Fixed" or pd.notna(r.modification_date):
            reason = "unsupported_contract"
        elif pd.isna(r.maturity_date) or r.onset_date.to_period("M") >= r.maturity_date.to_period(
            "M"
        ):
            reason = "missing_or_crossed_maturity"
        elif is_io and pd.isna(r.io_end_date):
            reason = "unknown_io_end"
        elif is_io and r.io_end_date.to_period("M") > r.anchor_date.to_period("M"):
            reason = "ongoing_or_transition_io"
        elif h is None or len(h) != 4 or h.reporting_date.dt.to_period("M").nunique() != 4:
            reason = "missing_or_duplicate_history"
        elif not (h.payment_status.eq("Current") & h.sdq_indicator.eq("N")).all():
            reason = "prior_noncurrent_history"
        elif (
            not np.isfinite(h.current_upb).all()
            or not h.note_rate.eq(r.note_rate).all()
            or not h.maturity_date.eq(r.maturity_date).all()
        ):
            reason = "changing_or_missing_contract"
        elif h.current_upb.diff().gt(0.01).any():
            reason = "prior_balance_increase"
        elif abs(h.iloc[-1].current_upb - r.anchor_upb) > 0.01:
            reason = "anchor_source_mismatch"
        elif is_io and r.io_end_date.to_period("M") >= h.iloc[0].reporting_date.to_period("M"):
            reason = "lookback_crosses_io_end"
        else:
            try:
                payment = inferred_payment(h.current_upb.to_numpy(), r.note_rate / 100)
                result = project_payment(
                    r.anchor_upb, r.note_rate / 100, payment, int(r.horizon_months)
                )
            except ValueError:
                reason = "unstable_payment_or_exhausted_schedule"
                payment = np.nan
        reasons.append(reason)
        payments.append(payment)
        predictions.append(result)
    frame["history_route"] = reasons
    frame["inferred_monthly_payment"] = payments
    frame["payment_history_prediction"] = predictions
    if (
        not np.isfinite(frame.payment_history_prediction).all()
        or frame.payment_history_prediction.lt(0).any()
    ):
        raise ValueError("Invalid principal forecast")
    advanced = pd.read_parquet(frozen)
    matched = frame.merge(
        advanced[["loan_id", "horizon_months", "boosted_residual", "guarded_ridge"]],
        on=["loan_id", "horizon_months"],
        how="left",
        validate="one_to_one",
    )
    reference_path = a / "ead-schedule-reference-v0.1.0/predictions.parquet"
    reference = pd.read_parquet(reference_path)
    check = frame[["loan_id", "horizon_months", "post_io_reference"]].merge(
        reference[["loan_id", "horizon_months", "principal_ead_prediction"]],
        on=["loan_id", "horizon_months"],
        validate="one_to_one",
    )
    if len(check) != len(frame):
        raise ValueError("Reference population mismatch")
    np.testing.assert_allclose(
        check.post_io_reference, check.principal_ead_prediction, rtol=0, atol=1e-8
    )
    drift = []
    for (horizon, partition), g in matched[matched.boosted_residual.notna()].groupby(
        ["horizon_months", "partition"]
    ):
        drift.append(
            {
                "horizon_months": int(horizon),
                "partition": partition,
                "needed_schedule_adjustment_over_actual": float(
                    (g.onset_scheduled_upb - g.post_io_reference).sum()
                    / g.onset_scheduled_upb.sum()
                ),
                "boosted_schedule_adjustment_over_actual": float(
                    (g.boosted_residual - g.post_io_reference).sum() / g.onset_scheduled_upb.sum()
                ),
            }
        )
    metrics = []
    for (horizon, partition), g in matched.groupby(["horizon_months", "partition"]):
        for scope, s in [
            ("all_initial_eligible", g),
            ("supported_advanced_matched", g[g.boosted_residual.notna()]),
        ]:
            for column in ["post_io_reference", "payment_history_prediction"] + (
                ["boosted_residual", "guarded_ridge"]
                if scope == "supported_advanced_matched"
                else []
            ):
                if not s.empty:
                    metrics.append(
                        {
                            "horizon_months": int(horizon),
                            "partition": partition,
                            "scope": scope,
                            "candidate": column,
                            **score(s, column),
                        }
                    )
    report = {
        "status": "prior_payment_reconstruction_research_not_selected",
        "inputs": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [source, frozen, monthly, reference_path]
        },
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "specification": {
            "lookback_months": 3,
            "prior_rows": 4,
            "payment": "median implied monthly payment",
            "stability_dollars": 1,
            "stability_relative_to_payment": 0.001,
            "rate": "anchor fixed rate held constant",
            "target": "scheduled principal at firstSDQ",
            "fallback": "existing postIO schedule where supported, otherwise flagged balance hold",
        },
        "routes": frame.groupby(["horizon_months", "history_route"])
        .size()
        .reset_index(name="cases")
        .to_dict("records"),
        "metrics": metrics,
        "boosted_adjustment_diagnostics": drift,
        "reference_identity_verified_horizon_cases": len(check),
        "limits": [
            "No future balances or cohort outcomes in payment reconstruction; no fitted coefficients",
            "Mechanical stability gate prespecified before run; no recent-outcome threshold tuning",
            "Prior payments inferred from stated principal, not verified contractual cash payments",
            "No principal+interest EAD,CCF,PD refit,LGD denominator change or EL integration",
            "Examined later cohorts reused for development; no independent generalization claim",
            "Historical pre2019 scores are descriptive formula scores, not fitted training scores",
            "IO and maturity ambiguities retain prior flagged proxy, not inferred payoff",
            "Processed v0.3.0 unreconstructed after signed-parser change; only balance/rate/status/date used",
        ],
    }
    output.mkdir(parents=True)
    matched.to_parquet(output / "predictions.parquet", index=False)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.root, a.output)
