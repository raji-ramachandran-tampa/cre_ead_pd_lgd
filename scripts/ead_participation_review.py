"""Date-aligned participation review; no silent EAD or LGD target replacement."""

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


def run(root, output):
    if output.exists():
        raise FileExistsError(output)
    benchmark_path = root / "ead-source-audit-v0.2.0/benchmark_cases.parquet"
    reference_path = root / "ead-schedule-reference-v0.1.0/predictions.parquet"
    denominator_path = root / "ead-schedule-reconciliation-v0.1.0/denominator_cases.parquet"
    labels_path = root / "lgd-signed-research-v0.1.0/signed_outcomes.parquet"
    benchmark = pd.read_parquet(benchmark_path)
    reference = pd.read_parquet(reference_path)
    fields = ["loan_id", "horizon_months", "onset_participation_upb"]
    comparisons = reference.merge(
        benchmark[fields], on=["loan_id", "horizon_months"], validate="one_to_one"
    )
    metrics = []
    for (horizon, partition), g in comparisons.groupby(["horizon_months", "partition"]):
        available = g[g.onset_participation_upb.gt(0)].copy()
        actual = available.onset_participation_upb
        error = available.principal_ead_prediction - actual
        basis = available.onset_scheduled_upb - actual
        metrics.append(
            {
                "horizon_months": int(horizon),
                "partition": partition,
                "initial_eligible": len(g),
                "participation_positive": len(available),
                "missing_or_nonpositive_participation": len(g) - len(available),
                "scheduled_equals_participation_within_cent": int(basis.abs().le(0.01).sum()),
                "median_scheduled_over_participation": float(
                    (available.onset_scheduled_upb / actual).median()
                ),
                "scheduled_vs_participation_absolute_difference_over_actual": float(
                    basis.abs().sum() / actual.sum()
                ),
                "reference_vs_participation_absolute_error_over_actual": float(
                    error.abs().sum() / actual.sum()
                ),
                "reference_vs_participation_bias_over_actual": float(error.sum() / actual.sum()),
            }
        )
    denominator = pd.read_parquet(denominator_path)
    labels = pd.read_parquet(labels_path)
    extra = [
        "loan_id",
        "credit_event_type",
        "liquidation_code",
        "loss_sharing_type",
        "default_amount_values",
        "event_date_values",
        "earliest_reporting_date",
        "period",
    ]
    denominator = denominator.merge(labels[extra], on="loan_id", validate="one_to_one")
    positive = denominator.current_upb.gt(0) & denominator.parsed_default.gt(0)
    denominator["principal_identity_scale"] = np.where(
        positive, denominator.current_upb / denominator.parsed_default, np.nan
    )
    denominator["absolute_scale_departure"] = (denominator.principal_identity_scale - 1).abs()
    denominator["diagnostic_band"] = pd.cut(
        denominator.absolute_scale_departure,
        [-np.inf, 0.01, 0.05, 0.10, np.inf],
        labels=["within_1pct", "1_to_5pct", "5_to_10pct", "above_10pct"],
    )
    # Thresholds descriptive only, not policy limits, exclusions or approval rules.
    large = denominator[denominator.absolute_scale_departure.gt(0.10)].copy()
    large["participation_available"] = large.delinquency_upb.gt(0)
    large["participation_equals_source_within_cent"] = (
        (large.delinquency_upb - large.parsed_default).abs().le(0.01)
    )
    large["participation_equals_scheduled_within_cent"] = (
        (large.delinquency_upb - large.current_upb).abs().le(0.01)
    )
    monthly_path = root.parent.parent / "processed/2026Q1/v0.3.0/fannie_monthly.parquet"
    connection = duckdb.connect()
    connection.register("exceptions", large[["loan_id", "credit_event_date"]])
    history = connection.execute(
        "SELECT m.loan_id,m.reporting_date,m.current_upb,m.payment_status,m.sdq_indicator,m.maturity_date FROM read_parquet(?) m JOIN exceptions e USING(loan_id) WHERE m.reporting_date<e.credit_event_date ORDER BY m.loan_id,m.reporting_date",
        [str(monthly_path)],
    ).fetchdf()
    connection.close()
    histories = []
    for loan, h in history.groupby("loan_id"):
        sdq = h.sdq_indicator.eq("Y") | h.payment_status.isin(
            ["60-89 Days Delinquent", "90+ Days Delinquent"]
        )
        spells = int((sdq & ~sdq.shift(1, fill_value=False)).sum())
        gap = h.reporting_date.dt.to_period("M").astype(int).diff().gt(1)
        start_rows = h.loc[sdq & ~sdq.shift(1, fill_value=False)]
        latest_start_balance = (
            float(start_rows.iloc[-1].current_upb) if not start_rows.empty else np.nan
        )
        histories.append(
            {
                "loan_id": loan,
                "observed_sdq_spells": spells,
                "last_observed_spell_start_principal": latest_start_balance,
                "return_to_non_sdq_transitions": int((~sdq & sdq.shift(1, fill_value=False)).sum()),
                "history_gaps": int(gap.sum()),
                "maturity_values": int(h.maturity_date.nunique()),
                "balance_increase_transitions": int(h.current_upb.diff().gt(0.01).sum()),
            }
        )
    history_flags = pd.DataFrame(histories)
    large = large.merge(history_flags, on="loan_id", validate="one_to_one")
    large["last_spell_scale_departure"] = (
        large.last_observed_spell_start_principal / large.parsed_default - 1
    ).abs()
    report = {
        "status": "participation_comparison_and_exception_audit_only",
        "input_hashes": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [benchmark_path, reference_path, denominator_path, labels_path]
        },
        "same_month_participation_metrics": metrics,
        "signed_cases": len(denominator),
        "positive_scheduled_match": int(positive.sum()),
        "diagnostic_bands": denominator.groupby("diagnostic_band", observed=True).size().to_dict(),
        "large_exceptions": {
            "threshold_description": "Absolute principal/source ratio departure >10%; descriptive, no removal",
            "cases": len(large),
            "principal_exceeds_source": int(large.principal_identity_scale.gt(1).sum()),
            "source_exceeds_principal": int(large.principal_identity_scale.lt(1).sum()),
            "participation_available": int(large.participation_available.sum()),
            "participation_equals_source": int(large.participation_equals_source_within_cent.sum()),
            "participation_equals_scheduled": int(
                large.participation_equals_scheduled_within_cent.sum()
            ),
            "source_default_changed_history": int(large.default_amount_values.gt(1).sum()),
            "source_event_date_changed_history": int(large.event_date_values.gt(1).sum()),
            "median_sdq_to_disposition_years": float(large.years_sdq_to_disposition.median()),
            "multiple_observed_sdq_spells": int(large.observed_sdq_spells.gt(1).sum()),
            "last_spell_smaller_source_departure": int(
                large.last_spell_scale_departure.lt(large.absolute_scale_departure - 1e-9).sum()
            ),
            "any_return_to_non_sdq": int(large.return_to_non_sdq_transitions.gt(0).sum()),
            "history_gap_cases": int(large.history_gaps.gt(0).sum()),
            "multiple_maturity_cases": int(large.maturity_values.gt(1).sum()),
            "balance_increase_cases": int(large.balance_increase_transitions.gt(0).sum()),
            "loss_sharing_counts": large.loss_sharing_type.fillna("missing")
            .value_counts()
            .to_dict(),
        },
        "limitations": [
            "Participation UPB actual at reported delinquency, not established whole-loan exposure",
            "Same reporting month does not establish exact contractual default date",
            "Comparing a scheduled-principal model with participation changes scoring target; not principal accuracy improvement",
            "Missing/nonpositive values excluded from comparison only, not deleted from population",
            "Source DefaultAmount timing, accrual and participation cannot be separately identified",
            "SDQ spell transitions are observed status changes, not approved cure or redefault episodes",
            "History flags use unchanged processed v0.3.0, pre negative-accounting parser rebuild",
            "Large-exception flags not causal explanations, no clipping, no denominator substitution",
            "No fit, no LGD target change, no PD event change, no EL integration",
        ],
    }
    report["history_source_version"] = "processed/2026Q1/v0.3.0"
    report["history_source_sha256"] = hashlib.sha256(monthly_path.read_bytes()).hexdigest()
    output.mkdir(parents=True)
    comparisons.to_parquet(output / "participation_comparison.parquet", index=False)
    large.to_parquet(output / "large_denominator_exceptions.parquet", index=False)
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
