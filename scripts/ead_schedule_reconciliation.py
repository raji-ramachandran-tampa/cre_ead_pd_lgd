"""Schedule conventions and source exposure basis reconciliation, no accrual inference."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cre_expected_loss.models.ead_research import prepare, score


def comparison(frame, field):
    rows = []
    for value, g in frame.groupby(field, observed=True):
        for candidate in ["amortization_prediction", "io_clock_sensitivity"]:
            rows.append(
                {
                    "segment": str(value),
                    "candidate": candidate,
                    "unique_loans": int(g.loan_id.nunique()),
                    **score(g, candidate),
                }
            )
    return rows


def run(root, output):
    if output.exists():
        raise FileExistsError(output)
    sources = root / "ead-source-audit-v0.2.0"
    performing = prepare(pd.read_parquet(sources / "performing_schedule_cases.parquet"))
    good = (
        performing[performing.schedule_status.eq("supported")]
        .dropna(subset=["amortization_prediction", "io_clock_sensitivity"])
        .copy()
    )
    # One latest supported diagnostic window per loan: reduce repeated-window dominance.
    one = (
        good.sort_values(["loan_id", "anchor_date"]).drop_duplicates("loan_id", keep="last").copy()
    )
    one["calendar_error"] = abs(one.amortization_prediction - one.onset_scheduled_upb)
    one["post_io_error"] = abs(one.io_clock_sensitivity - one.onset_scheduled_upb)
    different = (one.amortization_prediction - one.io_clock_sensitivity).abs().gt(0.01)
    convention_wins = {
        "distinct_prediction_loans": int(different.sum()),
        "post_io_lower_error": int((different & one.post_io_error.lt(one.calendar_error)).sum()),
        "calendar_lower_error": int((different & one.calendar_error.lt(one.post_io_error)).sum()),
    }
    reconciliation = pd.read_parquet(sources / "lgd_denominator_reconciliation.parquet")
    labels = pd.read_parquet(root / "lgd-signed-research-v0.1.0/signed_outcomes.parquet")
    matched = reconciliation.merge(
        labels[
            [
                "loan_id",
                "parsed_default",
                "credit_event_date",
                "source_record_date",
                "signed_loss",
                "signed_ratio",
            ]
        ],
        on="loan_id",
        validate="one_to_one",
    )
    np.testing.assert_allclose(matched.default_amount, matched.parsed_default, rtol=0, atol=1e-8)
    np.testing.assert_allclose(
        matched.signed_loss / matched.parsed_default, matched.signed_ratio, rtol=1e-12, atol=1e-12
    )
    matched["years_sdq_to_disposition"] = (
        matched.credit_event_date - matched.reporting_date
    ).dt.days / 365.25
    matched["source_minus_scheduled"] = matched.parsed_default - matched.current_upb
    matched["source_minus_participation"] = matched.parsed_default - matched.delinquency_upb
    summaries = []
    for column in ["current_upb", "delinquency_upb"]:
        g = matched[matched[column].gt(0)]
        ratio = g.parsed_default / g[column]
        # Source LGD * a different EAD rescales accounting-loss identity.
        scale = g[column] / g.parsed_default
        summaries.append(
            {
                "comparison": column,
                "cases": len(g),
                "residual_positive": int((g.parsed_default - g[column]).gt(0.01).sum()),
                "residual_negative": int((g.parsed_default - g[column]).lt(-0.01).sum()),
                "residual_within_cent": int((g.parsed_default - g[column]).abs().le(0.01).sum()),
                "ratios_within_one_percent": int((ratio - 1).abs().le(0.01).sum()),
                "median_ratio": float(ratio.median()),
                "median_loss_identity_scale": float(scale.median()),
                "p10_scale": float(scale.quantile(0.1)),
                "p90_scale": float(scale.quantile(0.9)),
                "maximum_absolute_scale_departure": float((scale - 1).abs().max()),
            }
        )
    gaps = matched.years_sdq_to_disposition.dropna()
    report = {
        "status": "schedule_and_exposure_basis_audit_not_contract_validation",
        "input_hashes": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                sources / "performing_schedule_cases.parquet",
                sources / "lgd_denominator_reconciliation.parquet",
                root / "lgd-signed-research-v0.1.0/signed_outcomes.parquet",
            ]
        },
        "performing_supported_windows": len(good),
        "one_window_per_loan": len(one),
        "window_choice": "Latest supported performing window, not independent future validation",
        "schedule_by_type": comparison(one, "amortization_type"),
        "convention_wins": convention_wins,
        "exposure_basis": summaries,
        "date_gaps": {
            "matched": len(gaps),
            "median_years": float(gaps.median()),
            "p10_years": float(gaps.quantile(0.1)),
            "p90_years": float(gaps.quantile(0.9)),
            "negative_gaps": int(gaps.lt(0).sum()),
        },
        "accounting_identity_verified_cases": len(matched),
        "limitations": [
            "Residual DefaultAmount minus balance is not identified accrued interest",
            "Dates and participation basis differ; source contractual default date absent",
            "First SDQ includes cured/redefault loans and may not be economic default",
            "One-window diagnostic selected retrospectively; contract/payment documentation absent",
            "Do not change frozen LGD denominator or treat source labels as prospective EAD",
            "Principal model errors not total economic exposure accuracy",
        ],
    }
    output.mkdir(parents=True)
    matched.to_parquet(output / "denominator_cases.parquet", index=False)
    one.to_parquet(output / "schedule_diagnostic_cases.parquet", index=False)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "input_hashes"}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--artifact-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.artifact_root, a.output)
