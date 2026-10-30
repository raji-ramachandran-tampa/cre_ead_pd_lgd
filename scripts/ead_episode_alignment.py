"""First/last spell sensitivity; no closest-balance selection of true default."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def run(root, output):
    if output.exists():
        raise FileExistsError(output)
    ep_path = root / "ead-observed-episodes-v0.1.0/observed_episodes.parquet"
    label_path = root / "lgd-signed-research-v0.1.0/signed_outcomes.parquet"
    ep = pd.read_parquet(ep_path).sort_values(["loan_id", "episode_number"])
    labels = pd.read_parquet(label_path)
    counts = ep.groupby("loan_id").size()
    first = ep.drop_duplicates("loan_id", keep="first")
    last = ep.drop_duplicates("loan_id", keep="last")
    fields = [
        "loan_id",
        "start_report_date",
        "start_scheduled_upb",
        "start_participation_upb",
        "left_boundary_uncertain",
    ]
    f = labels[["loan_id", "parsed_default", "signed_loss", "credit_event_date", "period"]].merge(
        first[fields].rename(columns={c: "first_" + c for c in fields if c != "loan_id"}),
        on="loan_id",
        how="left",
        validate="one_to_one",
    )
    f = f.merge(
        last[fields].rename(columns={c: "last_" + c for c in fields if c != "loan_id"}),
        on="loan_id",
        how="left",
        validate="one_to_one",
    )
    f["observed_spells"] = f.loan_id.map(counts).fillna(0).astype(int)
    multi = f[f.observed_spells.gt(1)].copy()
    multi["years_between_starts"] = (
        multi.last_start_report_date - multi.first_start_report_date
    ).dt.days / 365.25
    metrics = []
    for name in ["scheduled_upb", "participation_upb"]:
        a = multi["first_start_" + name]
        b = multi["last_start_" + name]
        valid = a.gt(0) & b.gt(0) & multi.parsed_default.gt(0)
        g = multi[valid]
        first_departure = (a[valid] / g.parsed_default - 1).abs()
        last_departure = (b[valid] / g.parsed_default - 1).abs()
        metrics.append(
            {
                "basis": name,
                "paired_cases": len(g),
                "first_median_absolute_source_scale_departure": float(first_departure.median()),
                "last_median_absolute_source_scale_departure": float(last_departure.median()),
                "last_smaller_departure": int(last_departure.lt(first_departure - 1e-9).sum()),
                "last_larger_departure": int(last_departure.gt(first_departure + 1e-9).sum()),
                "equal_departure": int((last_departure - first_departure).abs().le(1e-9).sum()),
                "last_matches_source_within_cent": int(
                    (b[valid] - g.parsed_default).abs().le(0.01).sum()
                ),
                "first_matches_source_within_cent": int(
                    (a[valid] - g.parsed_default).abs().le(0.01).sum()
                ),
            }
        )
    f["proposed_first_sdq_year"] = f.first_start_report_date.dt.year
    f["proposed_first_sdq_period"] = np.select(
        [
            f.proposed_first_sdq_year.isna(),
            f.proposed_first_sdq_year.le(2018),
            f.proposed_first_sdq_year.le(2022),
        ],
        ["unmatched", "training", "validation"],
        default="out_of_time",
    )
    report = {
        "status": "episode_alignment_sensitivity_and_timing_proposal_only",
        "input_hashes": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [ep_path, label_path]
        },
        "signed_lgd_cases": len(f),
        "no_pre_resolution_sdq_match": int(f.observed_spells.eq(0).sum()),
        "multiple_spell_cases": len(multi),
        "multiple_cases_by_existing_partition": multi.groupby("period").size().to_dict(),
        "first_to_last_start_years": {
            "median": float(multi.years_between_starts.median()),
            "p90": float(multi.years_between_starts.quantile(0.9)),
        },
        "paired_exposure_metrics": metrics,
        "partition_crosswalk": f.groupby(["period", "proposed_first_sdq_period"])
        .size()
        .reset_index(name="cases")
        .to_dict("records"),
        "limits": [
            "Exposure closeness cannot identify true contractual default or accrual",
            "First/last spell comparisons diagnostic only; last uses hindsight",
            "Repartitioning demonstrates timing impact, not refit performance",
            "Loss labels finalized after onset: chronological onset split alone does not establish label availability",
            "660 resolved-label links not all default population; unresolved SDQ remains in PD/EAD",
            "No existing PD/LGD/EAD baseline, labels or denominator changed",
        ],
    }
    output.mkdir(parents=True)
    f.to_parquet(output / "linked_spell_cases.parquet", index=False)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--artifact-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.artifact_root, a.output)
