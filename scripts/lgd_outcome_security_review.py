"""Outcome/security evidence only; no automatic default selection or refit."""

from pathlib import Path
import argparse, json, tempfile, hashlib
import numpy as np
import pandas as pd
import duckdb


def run(fannie_root):
    artifacts = fannie_root / "artifacts/2026Q1"
    source = artifacts / "lgd-gain-allocation-audit-v0.1.0/allocation_case_audit.parquet"
    cases = pd.read_parquet(source)
    monthly = fannie_root / "processed/2026Q1/v0.3.0/fannie_monthly.parquet"
    out = artifacts / "lgd-outcome-security-review-v0.1.0"
    if out.exists():
        raise FileExistsError(out)
    c = duckdb.connect()
    c.register("cases", cases[["loan_id", "credit_event_date"]])
    path = str(monthly).replace("'", "''")
    histories = c.execute(f"""
        SELECT m.loan_id,COUNT(*) AS observed_months,
        MIN(m.reporting_date) FILTER(WHERE m.payment_status IN ('60-89 Days Delinquent','90+ Days Delinquent') OR m.sdq_indicator='Y') AS first_reported_sdq,
        COUNT(*) FILTER(WHERE m.payment_status IN ('60-89 Days Delinquent','90+ Days Delinquent') OR m.sdq_indicator='Y') AS sdq_months,
        STRING_AGG(DISTINCT m.payment_status, ', ') AS observed_payment_statuses,
        MIN(m.reporting_date) AS first_month,MAX(m.reporting_date) AS last_month
        FROM read_parquet('{path}') m JOIN cases t USING(loan_id)
        WHERE m.reporting_date<t.credit_event_date GROUP BY m.loan_id
    """).fetchdf()
    c.close()
    d = cases.merge(histories, on="loan_id", validate="one_to_one", how="left")
    assert len(d) == 672 and d.observed_months.notna().all()
    paid = d.liquidation_code.fillna("").str.startswith("Fully Paid")
    workout = d.liquidation_code.isin(
        ["Foreclosure", "Deed-in-Lieu", "Third Party Sale", "Discounted Payoff"]
    )
    d["review_category"] = np.select(
        [paid, ~workout],
        ["fully_paid_credit_event_review", "other_code_review"],
        default="workout_code_source_event",
    )
    d["prior_sdq_observed"] = d.first_reported_sdq.notna()
    # Acquisition LTV includes prior liens for supplemental loans; a raw own-loan
    # UPB/LTV backsolve is not an identified combined collateral valuation.
    d["naive_acquisition_value_proxy"] = np.where(
        d.acquisition_ltv.gt(0), d.acquisition_upb / (d.acquisition_ltv / 100), np.nan
    )
    summary = {
        "status": "proposed_outcome_review_no_population_change",
        "category_counts": pd.crosstab(d.period, d.review_category).to_dict(),
        "fully_paid_cases": json.loads(
            d[paid][
                [
                    "loan_id",
                    "period",
                    "signed_ratio",
                    "liquidation_code",
                    "credit_event_type",
                    "sdq_months",
                    "first_reported_sdq",
                    "observed_payment_statuses",
                ]
            ].to_json(orient="records", date_format="iso")
        ),
        "sdq_by_category": {
            str(k): {"cases": len(g), "prior_sdq_observed": int(g.prior_sdq_observed.sum())}
            for k, g in d.groupby(["period", "review_category"])
        },
        "collateral_coverage": {
            str(k): {
                "cases": len(g),
                "first_liens": int(g.lien_position.eq("First").sum()),
                "multi_property": int(g.property_count.gt(1).sum()),
                "missing_property_count": int(g.property_count.isna().sum()),
                "missing_foreclosure_value": int(g.foreclosure_value.isna().sum()),
                "missing_sale_price": int(g.sale_price.isna().sum()),
            }
            for k, g in d.groupby("period")
        },
        "limitations": [
            "Reported SDQ is evidence of delinquency, not an approved default definition or true onset.",
            "Missing delinquency histories do not prove an absence of past default.",
            "Credit event is source disposition rather than necessarily default.",
            "Collateral net recovery cannot be reconstructed without lien stack, allocated proceeds, costs and dates.",
            "Naive acquisition value proxy is diagnostic only, not a current appraisal or eligible model feature.",
        ],
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    with tempfile.TemporaryDirectory(prefix="outcome-review-", dir=artifacts) as temp:
        stage = Path(temp) / "output"
        stage.mkdir()
        d.to_parquet(stage / "outcome_security_review.parquet", index=False)
        (stage / "report.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        stage.rename(out)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fannie-root", type=Path, required=True)
    run(parser.parse_args().fannie_root)
