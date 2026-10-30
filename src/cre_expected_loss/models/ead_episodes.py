"""Observed serious-delinquency spells; not contractual defaults or cures."""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import duckdb
import pandas as pd

from cre_expected_loss.ingestion.fannie_dataset import _extract_single_csv, _number_expr_sql


def observed_episodes(monthly):
    required = ["loan_id", "reporting_date", "payment_status", "sdq_indicator", "current_upb"]
    if monthly[required[:2]].isna().any().any() or monthly.duplicated(required[:2]).any():
        raise ValueError("Missing or duplicate history keys")
    known = {"Current", "30-59 Days Delinquent", "60-89 Days Delinquent", "90+ Days Delinquent"}
    if (
        not monthly.payment_status.isin(known).all()
        or not monthly.sdq_indicator.isin(["Y", "N"]).all()
    ):
        raise ValueError("Unknown observed payment status")
    episodes = []
    for loan, g in monthly.groupby("loan_id", sort=False):
        g = g.sort_values("reporting_date")
        active = None
        previous = None
        episode_number = 0
        for r in g.itertuples():
            sdq = r.sdq_indicator == "Y" or r.payment_status in [
                "60-89 Days Delinquent",
                "90+ Days Delinquent",
            ]
            gap = (
                previous is not None
                and (
                    r.reporting_date.to_period("M").ordinal
                    - previous.reporting_date.to_period("M").ordinal
                )
                > 1
            )
            if active is not None and (gap or not sdq):
                active["end_observation"] = "history_gap" if gap else "return_to_non_sdq"
                active["following_report_date"] = r.reporting_date
                active["following_payment_status"] = r.payment_status
                episodes.append(active)
                active = None
            if sdq and active is None:
                episode_number += 1
                active = {
                    "loan_id": loan,
                    "episode_number": episode_number,
                    "start_report_date": r.reporting_date,
                    "last_sdq_report_date": r.reporting_date,
                    "observed_sdq_months": 0,
                    "start_scheduled_upb": r.current_upb,
                    "start_participation_upb": getattr(r, "delinquency_upb", float("nan")),
                    "preceding_report_date": pd.NaT
                    if previous is None
                    else previous.reporting_date,
                    "preceding_payment_status": None
                    if previous is None
                    else previous.payment_status,
                    "left_boundary_uncertain": previous is None or gap,
                    "source_resolution_date": getattr(r, "first_credit_event_date", pd.NaT),
                    "end_observation": "history_end",
                    "following_report_date": pd.NaT,
                    "following_payment_status": None,
                }
            if active is not None:
                active["last_sdq_report_date"] = r.reporting_date
                active["observed_sdq_months"] += 1
            previous = r
        if active is not None:
            episodes.append(active)
    return pd.DataFrame(episodes)


def run(root, output):
    if output.exists():
        raise FileExistsError(output)
    monthly_path = root / "processed/2026Q1/v0.3.0/fannie_monthly.parquet"
    raw = root / "raw/2026Q1/Multifamily.zip"
    con = duckdb.connect()
    # Exclude post-resolution reports; source resolution is outcome metadata only.
    history = con.execute(
        """WITH ids AS (SELECT DISTINCT loan_id FROM read_parquet(?) WHERE sdq_indicator='Y' OR payment_status IN ('60-89 Days Delinquent','90+ Days Delinquent'))
        SELECT m.loan_id,m.reporting_date,m.payment_status,m.sdq_indicator,m.current_upb,m.first_credit_event_date
        FROM read_parquet(?) m JOIN ids USING(loan_id)
        WHERE m.first_credit_event_date IS NULL OR m.reporting_date<m.first_credit_event_date""",
        [str(monthly_path), str(monthly_path)],
    ).fetchdf()
    con.register("history_keys", history[["loan_id", "reporting_date"]].drop_duplicates())
    with tempfile.TemporaryDirectory(prefix="ead_episodes_") as tmp:
        csv = _extract_single_csv(raw, Path(tmp))
        source = str(csv).replace("'", "''")
        sql = (
            'SELECT DISTINCT TRIM("Loan Number") loan_id, COALESCE(TRY_STRPTIME("Reporting Period Date",\'%m/%d/%Y\')::DATE,TRY_STRPTIME("Reporting Period Date",\'%Y-%m-%d\')::DATE) reporting_date,'
            + _number_expr_sql("Delinquency UPB")
            + f" delinquency_upb FROM read_csv('{source}',header=true,all_varchar=true)"
        )
        participation = con.execute(
            "SELECT r.* FROM (" + sql + ") r JOIN history_keys h USING(loan_id,reporting_date)"
        ).fetchdf()
    con.close()
    # Four source projected duplicate keys are identical: remove identical key/participation rows.
    history = history.drop_duplicates()
    history = history.merge(participation, on=["loan_id", "reporting_date"], validate="one_to_one")
    episodes = observed_episodes(history)
    if episodes.empty:
        raise ValueError("No observed episodes")
    episodes["last_episode_before_source_resolution"] = False
    resolved = episodes[episodes.source_resolution_date.notna()]
    last = resolved.groupby("loan_id").episode_number.idxmax()
    episodes.loc[last, "last_episode_before_source_resolution"] = True
    report = {
        "status": "observed_spells_not_verified_default_episodes",
        "processed_version": "v0.3.0_not_rebuilt_after_signed_parser_fix",
        "processed_sha256": hashlib.sha256(monthly_path.read_bytes()).hexdigest(),
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "history_rows": len(history),
        "observed_episode_rows": len(episodes),
        "loans_with_episodes": int(episodes.loan_id.nunique()),
        "multiple_episode_loans": int(episodes.groupby("loan_id").size().gt(1).sum()),
        "uncertain_left_boundaries": int(episodes.left_boundary_uncertain.sum()),
        "end_observation_counts": episodes.end_observation.value_counts().to_dict(),
        "episodes_with_positive_participation": int(episodes.start_participation_upb.gt(0).sum()),
        "loans_with_source_resolution": int(resolved.loan_id.nunique()),
        "limits": [
            "SDQ60+ proxy, not contractual default/cure/redefault",
            "Return to30-59 is nonSDQ, not necessarily Current or cured",
            "Gap breaks observed spell with uncertain next boundary",
            "Last pre-resolution episode association is hindsight diagnostic, not verified loss episode",
            "Participation at start is source institution measure, not wholeloan EAD",
            "Pre-resolution history restriction uses outcome metadata; not prospective feature extraction",
            "No LGD denominator change, fit, EL integration or loan-level Git data",
        ],
    }
    output.mkdir(parents=True)
    episodes.to_parquet(output / "observed_episodes.parquet", index=False)
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.root, a.output)
