"""Read immutable ZIP, retaining event-loan acquisition-field evidence externally."""

from pathlib import Path
import csv, io, json, zipfile
import pandas as pd

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--fannie-root", type=Path, required=True)
root = parser.parse_args().fannie_root
audit = pd.read_parquet(
    root / "artifacts/2026Q1/lgd-reconciliation-v0.1.0/loan_reconciliation.parquet"
)
ids = set(audit.loan_id)
fields = [
    "Loan Number",
    "Loan Acquisition UPB",
    "Original Interest Rate",
    "Transaction ID ",
    "Loss Sharing Type",
    "Modified Loss Sharing Percentage",
    "Reporting Period Date",
    "Default Amount",
    "Lifetime Net Credit Loss Amount",
    "Foreclosure Date",
]
records = {}
z = next((root / "raw").rglob("Multifamily.zip"))
with zipfile.ZipFile(z) as a:
    with a.open(next(n for n in a.namelist() if n.lower().endswith(".csv"))) as f:
        reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig"))
        header = next(reader)
        index = {k: header.index(k) for k in fields}
        loan_index = index["Loan Number"]
        for row in reader:
            loan = row[loan_index].strip()
            if loan not in ids:
                continue
            vals = {k: row[i].strip() for k, i in index.items()}
            date = pd.to_datetime(vals["Reporting Period Date"])
            if loan not in records:
                records[loan] = {
                    "earliest": vals,
                    "latest": vals,
                    "earliest_date": date,
                    "latest_date": date,
                    "transactions": set(),
                    "loss_sharing_types": set(),
                    "acquisition_upbs": set(),
                }
            r = records[loan]
            if date < r["earliest_date"]:
                r.update(earliest=vals, earliest_date=date)
            if date > r["latest_date"]:
                r.update(latest=vals, latest_date=date)
            r["transactions"].add(vals["Transaction ID "])
            r["loss_sharing_types"].add(vals["Loss Sharing Type"])
            r["acquisition_upbs"].add(vals["Loan Acquisition UPB"])
rows = []
for loan, r in records.items():
    rows.append(
        {
            "loan_id": loan,
            "acquisition_upb_raw": r["earliest"]["Loan Acquisition UPB"],
            "original_rate_raw": r["earliest"]["Original Interest Rate"],
            "transaction_id": r["earliest"]["Transaction ID "],
            "transaction_values": len(r["transactions"]),
            "loss_sharing_type": r["earliest"]["Loss Sharing Type"],
            "loss_sharing_values": len(r["loss_sharing_types"]),
            "acquisition_upb_values": len(r["acquisition_upbs"]),
            "earliest_reporting_date": r["earliest_date"],
            "raw_default_latest": r["latest"]["Default Amount"],
            "raw_loss_latest": r["latest"]["Lifetime Net Credit Loss Amount"],
            "foreclosure_date_raw": r["latest"]["Foreclosure Date"],
        }
    )
extra = pd.DataFrame(rows)
joined = audit.merge(extra, on="loan_id", how="left", validate="one_to_one")
assert len(joined) == 765 and len(extra) == 765
for raw, new in [
    ("acquisition_upb_raw", "acquisition_upb"),
    ("original_rate_raw", "original_rate"),
]:
    joined[new] = pd.to_numeric(joined[raw].str.replace(r"[,$%]", "", regex=True), errors="coerce")
out = root / "artifacts/2026Q1/lgd-driver-audit-v0.1.0"
if out.exists():
    raise FileExistsError(out)
out.mkdir()
joined.to_parquet(out / "event_driver_audit.parquet", index=False)
joined.groupby(["credit_event_year", "status"]).size().rename("loans").reset_index().to_csv(
    out / "annual_eligibility.csv", index=False
)
recent = joined[joined.credit_event_year >= 2023]
summary = {
    "recent_cases": len(recent),
    "recent_status": recent.status.value_counts().to_dict(),
    "recent_raw_default_strings": recent.raw_default_latest.value_counts().to_dict(),
    "recent_raw_loss_strings": recent.raw_loss_latest.value_counts().head(10).to_dict(),
    "unstable_fields": {
        c: int((joined[c] > 1).sum())
        for c in ["transaction_values", "loss_sharing_values", "acquisition_upb_values"]
    },
    "oot_transactions": joined[
        joined.credit_event_year.ge(2023) & joined.status.eq("research_eligible")
    ][["loan_id", "transaction_id", "loss_sharing_type"]].to_dict("records"),
}
(out / "audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
