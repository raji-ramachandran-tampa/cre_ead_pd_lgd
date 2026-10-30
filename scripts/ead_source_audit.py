"""EAD field audit and balance-hold benchmark; first SDQ is an onset proxy."""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from cre_expected_loss.ingestion.fannie_dataset import _extract_single_csv, _number_expr_sql


def run(root: Path, output: Path):
    if output.exists():
        raise FileExistsError(output)
    raw = root / "raw/2026Q1/Multifamily.zip"
    labels = root / "artifacts/2026Q1/lgd-signed-research-v0.1.0/signed_outcomes.parquet"
    if not labels.exists():
        matches = list((root / "artifacts/2026Q1").glob("*/signed_outcomes.parquet"))
        if len(matches) != 1:
            raise ValueError("Specify an unambiguous frozen signed-outcome source")
        labels = matches[0]
    with tempfile.TemporaryDirectory(prefix="ead_audit_") as tmp:
        csv = _extract_single_csv(raw, Path(tmp))
        con = duckdb.connect()
        path = str(csv).replace("'", "''")

        def date(name):
            return f"COALESCE(TRY_STRPTIME(\"{name}\", '%m/%d/%Y')::DATE, TRY_STRPTIME(\"{name}\", '%Y-%m-%d')::DATE)"

        nums = {
            "UPB - Current": "current_upb",
            "Delinquency UPB": "delinquency_upb",
            "Default Amount": "default_amount",
            "Amortization Term": "amortization_months",
            "Original I/O Term": "io_months",
            "Note Rate": "note_rate",
            "Loan Age": "loan_age",
        }
        fields = [
            'TRIM("Loan Number") loan_id',
            date("Reporting Period Date") + " reporting_date",
            date("I/O End Date") + " io_end_date",
            date("Maturity Date - Current") + " maturity_date",
            date("Most Recent Modification Date") + " modification_date",
            'TRIM("Amortization Type") amortization_type',
            'TRIM("Interest Type") interest_type',
            'TRIM("Loan Product Type") product_type',
            'TRIM("Loan Payment Status") payment_status',
            'TRIM("SDQ Indicator") sdq_indicator',
        ]
        fields += [_number_expr_sql(k) + " " + v for k, v in nums.items()]
        con.execute(
            "CREATE TABLE monthly AS SELECT "
            + ", ".join(fields)
            + f" FROM read_csv('{path}', header=true, all_varchar=true)"
        )
        duplicate = con.execute(
            "SELECT COUNT(*) FROM (SELECT loan_id,reporting_date FROM monthly GROUP BY 1,2 HAVING COUNT(*)>1)"
        ).fetchone()[0]
        raw_rows = con.execute("SELECT COUNT(*) FROM monthly").fetchone()[0]
        con.execute("CREATE TABLE unique_projected AS SELECT DISTINCT * FROM monthly")
        unique_rows = con.execute("SELECT COUNT(*) FROM unique_projected").fetchone()[0]
        con.execute(
            "CREATE TABLE conflict_loans AS SELECT DISTINCT loan_id FROM (SELECT loan_id,reporting_date FROM unique_projected GROUP BY 1,2 HAVING COUNT(*)>1)"
        )
        conflicts = con.execute("SELECT COUNT(*) FROM conflict_loans").fetchone()[0]
        con.execute("DROP TABLE monthly")
        con.execute(
            "CREATE TABLE monthly AS SELECT * FROM unique_projected WHERE loan_id NOT IN (SELECT loan_id FROM conflict_loans)"
        )
        quality = (
            con.execute(
                "SELECT COUNT(*) row_count,COUNT(DISTINCT loan_id) loans, COUNT(*) FILTER(WHERE reporting_date IS NULL) missing_dates, COUNT(*) FILTER(WHERE current_upb IS NULL) missing_upb,COUNT(*) FILTER(WHERE current_upb<0) negative_upb,COUNT(*) FILTER(WHERE amortization_months IS NULL) missing_amortization_term, COUNT(*) FILTER(WHERE io_end_date IS NOT NULL) io_end_present,COUNT(*) FILTER(WHERE delinquency_upb IS NOT NULL) delinquency_upb_present FROM monthly"
            )
            .fetchdf()
            .iloc[0]
            .to_dict()
        )
        products = (
            con.execute(
                "SELECT product_type, COUNT(DISTINCT loan_id) loans FROM monthly GROUP BY 1"
            )
            .fetchdf()
            .to_dict("records")
        )
        con.execute(
            "CREATE TABLE onset AS SELECT * FROM monthly WHERE sdq_indicator='Y' OR payment_status IN ('60-89 Days Delinquent','90+ Days Delinquent') QUALIFY ROW_NUMBER() OVER(PARTITION BY loan_id ORDER BY reporting_date)=1"
        )
        cases = con.execute(
            "SELECT o.*, (SELECT COUNT(*) FROM monthly m WHERE m.loan_id=o.loan_id AND m.reporting_date<o.reporting_date) prior_rows FROM onset o"
        ).fetchdf()
        # Exact month offsets; no nearest-row substitution across missing history.
        frames = []
        for horizon in [3, 12]:
            frame = con.execute(
                f"SELECT o.loan_id,o.reporting_date onset_date,o.current_upb onset_scheduled_upb,o.delinquency_upb onset_participation_upb,o.product_type,m.reporting_date anchor_date,m.current_upb anchor_upb,m.payment_status anchor_status,m.sdq_indicator anchor_sdq,m.amortization_type,m.amortization_months,m.io_months,m.loan_age,m.interest_type,m.io_end_date,m.note_rate,m.maturity_date,m.modification_date FROM onset o LEFT JOIN monthly m ON o.loan_id=m.loan_id AND date_trunc('month',m.reporting_date)=date_trunc('month',o.reporting_date)-INTERVAL '{horizon} months'"
            ).fetchdf()
            frame["horizon_months"] = horizon
            frame["partition"] = np.select(
                [frame.onset_date.dt.year.le(2018), frame.onset_date.dt.year.le(2022)],
                ["through_2018", "2019_2022"],
                default="2023_onward",
            )
            frame["eligible"] = (
                frame.anchor_upb.gt(0)
                & frame.onset_scheduled_upb.gt(0)
                & frame.anchor_status.eq("Current")
                & frame.anchor_sdq.ne("Y")
                & frame.product_type.ne("Credit Facility")
            )
            frame["balance_hold_prediction"] = frame.anchor_upb
            frames.append(frame)
        benchmarks = pd.concat(frames, ignore_index=True)
        performing = con.execute("""SELECT a.loan_id,a.reporting_date anchor_date,
            b.reporting_date onset_date,a.current_upb anchor_upb,b.current_upb onset_scheduled_upb,
            a.amortization_type,a.amortization_months,a.io_months,a.loan_age,a.interest_type,
            a.io_end_date,a.note_rate,a.maturity_date,a.modification_date,12 horizon_months
            FROM monthly a JOIN monthly b ON a.loan_id=b.loan_id
            AND date_trunc('month',b.reporting_date)=date_trunc('month',a.reporting_date)+INTERVAL '12 months'
            LEFT JOIN onset o ON a.loan_id=o.loan_id
            WHERE hash(a.loan_id)%100=0 AND a.product_type<>'Credit Facility'
            AND a.payment_status='Current' AND b.payment_status='Current'
            AND a.sdq_indicator='N' AND b.sdq_indicator='N'
            AND (o.reporting_date IS NULL OR b.reporting_date<o.reporting_date)
            AND a.current_upb>0 AND b.current_upb>0
            AND a.maturity_date=b.maturity_date AND a.note_rate=b.note_rate
            AND a.modification_date IS NOT DISTINCT FROM b.modification_date
            AND NOT EXISTS (SELECT 1 FROM monthly x WHERE x.loan_id=a.loan_id
                AND x.reporting_date>a.reporting_date AND x.reporting_date<b.reporting_date
                AND (x.payment_status<>'Current' OR x.sdq_indicator='Y'))
            """).fetchdf()
        con.close()
    signed = pd.read_parquet(labels)
    matched = signed[["loan_id", "default_amount"]].merge(
        cases[["loan_id", "reporting_date", "current_upb", "delinquency_upb", "prior_rows"]],
        on="loan_id",
        how="left",
        validate="one_to_one",
    )
    reconciliations = []
    for column in ["current_upb", "delinquency_upb"]:
        g = matched[matched[column].gt(0) & matched.default_amount.gt(0)]
        ratio = g.default_amount / g[column]
        reconciliations.append(
            {
                "balance": column,
                "matched_positive": len(g),
                "median_default_to_balance_ratio": float(ratio.median()),
                "p10_ratio": float(ratio.quantile(0.1)),
                "p90_ratio": float(ratio.quantile(0.9)),
                "within_one_percent": int((ratio - 1).abs().le(0.01).sum()),
            }
        )
    scores = []
    for (horizon, partition), g in benchmarks.groupby(["horizon_months", "partition"]):
        eligible = g[g.eligible]
        err = eligible.balance_hold_prediction - eligible.onset_scheduled_upb
        scores.append(
            {
                "horizon_months": int(horizon),
                "partition": partition,
                "onsets": len(g),
                "eligible": len(eligible),
                "mae_dollars": float(err.abs().mean()),
                "aggregate_absolute_error_over_actual": float(
                    err.abs().sum() / eligible.onset_scheduled_upb.sum()
                ),
                "mean_relative_error": float((err / eligible.onset_scheduled_upb).mean()),
            }
        )
    report = {
        "status": "source_audit_and_scheduled_balance_hold_benchmark_only",
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "labels_sha256": hashlib.sha256(labels.read_bytes()).hexdigest(),
        "label_source": labels.parent.name,
        "quality": {k: int(v) for k, v in quality.items()},
        "raw_projected_rows": raw_rows,
        "duplicate_keys_before_projection_dedup": duplicate,
        "identical_projected_rows_removed": raw_rows - unique_rows,
        "conflicting_projected_loans_excluded": conflicts,
        "products": products,
        "first_observed_sdq_loans": len(cases),
        "performing_schedule_sample_rows": len(performing),
        "performing_sample_rule": "DuckDB hash loan modulo100=0; repeated overlapping 12m windows; not independent",
        "first_sdq_without_prior_history": int(cases.prior_rows.eq(0).sum()),
        "signed_lgd_cases": len(signed),
        "signed_cases_with_sdq": int(matched.reporting_date.notna().sum()),
        "denominator_reconciliation": reconciliations,
        "balance_hold_scores": scores,
        "definitions": {
            "onset": "First observed SDQ Y or 60+ payment status; proposed proxy, not contractual default date",
            "target": "Scheduled/stated current UPB at onset; not verified actual funded exposure",
            "benchmark": "Hold the positive scheduled anchor balance constant, conditional on later first SDQ",
            "anchors": "Exact 3/12 month earlier report; Current, not SDQ; exclude Credit Facility",
            "default_amount": "Principal plus accrued interest, timing and participation unverified",
            "missing_components": "Separate accrued interest, advances, commitments and draw schedules absent",
            "availability": "Revised snapshot, row availability not verified; research only",
            "evaluation": "Descriptive chronological comparisons, no model fit, no independent validation",
        },
    }
    output.mkdir(parents=True)
    performing.to_parquet(output / "performing_schedule_cases.parquet", index=False)
    benchmarks.to_parquet(output / "benchmark_cases.parquet", index=False)
    matched.to_parquet(output / "lgd_denominator_reconciliation.parquet", index=False)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.output)
