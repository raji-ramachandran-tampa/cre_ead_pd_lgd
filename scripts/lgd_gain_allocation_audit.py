"""Read-only source allocation diagnostics; post-event fields never predictors."""

from pathlib import Path
import argparse, csv, io, json, zipfile, hashlib, tempfile
import numpy as np
import pandas as pd
from cre_expected_loss.models.lgd_signed_model import parse_accounting


def run(fannie_root):
    root = fannie_root / "artifacts/2026Q1"
    source = root / "lgd-signed-research-v0.1.0/signed_outcomes.parquet"
    d = pd.read_parquet(source)
    out = root / "lgd-gain-allocation-audit-v0.1.0"
    if out.exists():
        raise FileExistsError(out)
    ids = set(d.loan_id)
    fields = [
        "Loan Number",
        "Reporting Period Date",
        "Lien Position",
        "Loan Product Type",
        "Original UPB",
        "Number of Properties at Acquisition",
        "Modified Loss Sharing Percentage",
        "Property City",
        "Property Zip Code",
        "Foreclosure Value",
        "Sale Price",
        "Foreclosure Date",
        "Lifetime Net Credit Loss Amount",
        "Default Amount",
        "Liquidation/Prepayment Code",
    ]
    raw = next((fannie_root / "raw").rglob("Multifamily.zip"))
    records = {}
    with zipfile.ZipFile(raw) as a:
        with a.open(next(n for n in a.namelist() if n.lower().endswith(".csv"))) as f:
            reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            header = next(reader)
            ix = {name: header.index(name) for name in fields}
            for row in reader:
                loan = row[ix["Loan Number"]].strip()
                if loan not in ids:
                    continue
                vals = {k: row[i].strip() for k, i in ix.items()}
                date = pd.to_datetime(vals["Reporting Period Date"])
                if loan not in records:
                    records[loan] = {
                        "first": vals,
                        "last": vals,
                        "first_date": date,
                        "last_date": date,
                        "lien_values": set(),
                        "product_values": set(),
                        "loss_sharing_percent_values": set(),
                    }
                r = records[loan]
                if date < r["first_date"]:
                    r.update(first=vals, first_date=date)
                if date > r["last_date"]:
                    r.update(last=vals, last_date=date)
                r["lien_values"].add(vals["Lien Position"])
                r["product_values"].add(vals["Loan Product Type"])
                r["loss_sharing_percent_values"].add(vals["Modified Loss Sharing Percentage"])
    rows = []
    for loan, r in records.items():
        first, last = r["first"], r["last"]
        rows.append(
            {
                "loan_id": loan,
                "lien_position": first["Lien Position"],
                "product_type": first["Loan Product Type"],
                "original_upb": parse_accounting(first["Original UPB"]),
                "property_count": parse_accounting(first["Number of Properties at Acquisition"]),
                "loss_sharing_percentage": parse_accounting(
                    first["Modified Loss Sharing Percentage"]
                ),
                "city": last["Property City"],
                "zip": last["Property Zip Code"],
                "foreclosure_value": parse_accounting(last["Foreclosure Value"]),
                "sale_price": parse_accounting(last["Sale Price"]),
                "foreclosure_date": pd.to_datetime(last["Foreclosure Date"], errors="coerce"),
                "raw_signed_loss": parse_accounting(last["Lifetime Net Credit Loss Amount"]),
                "lien_distinct_values": len(r["lien_values"]),
                "product_distinct_values": len(r["product_values"]),
                "sharing_percentage_distinct_values": len(r["loss_sharing_percent_values"]),
            }
        )
    d = d.merge(pd.DataFrame(rows), on="loan_id", validate="one_to_one")
    assert len(d) == 672 and d.loan_id.is_unique
    np.testing.assert_allclose(d.raw_signed_loss, d.signed_loss)
    d["outcome_sign"] = np.where(
        d.signed_ratio > 0, "positive", np.where(d.signed_ratio < 0, "negative", "zero")
    )
    d["sale_to_default"] = d.sale_price / d.parsed_default
    d["foreclosure_value_to_default"] = d.foreclosure_value / d.parsed_default
    d["foreclosure_to_event_months"] = (d.credit_event_date - d.foreclosure_date).dt.days / 30.4375

    def summarize(g):
        nonzero = g.signed_ratio.ne(0)
        return {
            "cases": len(g),
            "negative_cases": int(g.signed_ratio.lt(0).sum()),
            "negative_share_nonzero": float(g.loc[nonzero, "signed_ratio"].lt(0).mean())
            if nonzero.any()
            else None,
            "mean_signed_ratio": float(g.signed_ratio.mean()),
            "mean_negative_magnitude": float(-g.loc[g.signed_ratio.lt(0), "signed_ratio"].mean())
            if g.signed_ratio.lt(0).any()
            else None,
        }

    segments = {
        field: {str(k): summarize(g) for k, g in d.groupby(["period", field], dropna=False)}
        for field in ["lien_position", "product_type", "loss_sharing_type", "property_type"]
    }
    oot = d[d.period.eq("out_of_time")]
    gains = oot[oot.signed_ratio.lt(0)]
    similarities = []
    train_gains = d[d.period.eq("training") & d.signed_ratio.lt(0)]
    train_scale = d[d.period.eq("training")][
        ["acquisition_ltv", "underwritten_dscr", "log_acquisition_upb"]
    ].std(ddof=0)
    for _, q in gains.iterrows():
        pool = train_gains.copy()
        pool["distance"] = np.sqrt(
            (
                (
                    (
                        pool[["acquisition_ltv", "underwritten_dscr", "log_acquisition_upb"]]
                        - q[["acquisition_ltv", "underwritten_dscr", "log_acquisition_upb"]]
                    )
                    / train_scale
                )
                ** 2
            )
            .sum(axis=1)
            .astype(float)
        )
        same = pool[
            pool.lien_position.eq(q.lien_position) & pool.loss_sharing_type.eq(q.loss_sharing_type)
        ]
        cols = [
            "loan_id",
            "lien_position",
            "loss_sharing_type",
            "property_type",
            "signed_ratio",
            "distance",
        ]
        similarities.append(
            {
                "oot_loan": q.loan_id,
                "same_lien_and_sharing_training_gains": len(same),
                "nearest_same_structure": json.loads(
                    same.nsmallest(3, "distance")[cols].to_json(orient="records")
                ),
            }
        )
    # Candidate collateral clusters are flags only, not borrower identities.
    groups = d.groupby(["property_state", "city", "zip", "credit_event_date"], dropna=False)
    clusters = []
    for key, g in groups:
        if len(g) > 1 and g.period.eq("out_of_time").any():
            clusters.append(
                {
                    "location_event_key": [str(k) for k in key],
                    "loans": g.loan_id.tolist(),
                    "lien_positions": g.lien_position.tolist(),
                    "signed_ratios": g.signed_ratio.tolist(),
                }
            )
    report = {
        "status": "descriptive_source_allocation_audit_no_model_change",
        "period_summary": {k: summarize(g) for k, g in d.groupby("period")},
        "segments": segments,
        "oot_gains": json.loads(
            gains[
                [
                    "loan_id",
                    "property_type",
                    "property_state",
                    "lien_position",
                    "product_type",
                    "loss_sharing_type",
                    "loss_sharing_percentage",
                    "property_count",
                    "parsed_default",
                    "signed_loss",
                    "signed_ratio",
                    "sale_price",
                    "sale_to_default",
                    "foreclosure_value",
                    "foreclosure_value_to_default",
                    "foreclosure_to_event_months",
                    "liquidation_code",
                ]
            ].to_json(orient="records")
        ),
        "training_gain_analogues": similarities,
        "candidate_shared_collateral_clusters": clusters,
        "unstable_fields": {
            k: int(d[k].gt(1).sum())
            for k in [
                "lien_distinct_values",
                "product_distinct_values",
                "sharing_percentage_distinct_values",
            ]
        },
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "sources": [
            "https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-credit-loss-qrg.pdf",
            "https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-glossary-file-layout.pdf",
        ],
        "limitations": [
            "Source-only accounting amounts cannot reconstruct costs, benefits and loan-level gain allocation fully.",
            "Sale proceeds and foreclosure value are post-event diagnostics, prohibited as prospective features.",
            "Location/event matches are candidate clusters, not verified shared property or borrower.",
            "Single 2026Q1 release cannot establish loss finalization or revision stability.",
        ],
    }
    with tempfile.TemporaryDirectory(prefix="gain-audit-", dir=root) as temp:
        stage = Path(temp) / "output"
        stage.mkdir()
        d.to_parquet(stage / "allocation_case_audit.parquet", index=False)
        (stage / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        stage.rename(out)
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "period_summary",
                    "oot_gains",
                    "training_gain_analogues",
                    "candidate_shared_collateral_clusters",
                    "unstable_fields",
                ]
            },
            indent=2,
        )
    )
    print("LIEN PERIOD COUNTS", pd.crosstab(d.period, d.lien_position).to_string())
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fannie-root", type=Path, required=True)
    run(parser.parse_args().fannie_root)
