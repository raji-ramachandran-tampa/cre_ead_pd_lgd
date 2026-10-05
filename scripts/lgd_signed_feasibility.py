"""Target-feasibility audit only; does not authorize or fit a signed target."""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import duckdb
from cre_expected_loss.ingestion.fannie_dataset import _number_expr_sql

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--artifact-root", type=Path, required=True)
root = parser.parse_args().artifact_root
source = root / "lgd-driver-audit-v0.1.0/event_driver_audit.parquet"
d = pd.read_parquet(source)
c = duckdb.connect()
c.register("raw", d)
parsed = c.execute(
    "SELECT loan_id, "
    + _number_expr_sql("raw_loss_latest")
    + " AS signed_loss, "
    + _number_expr_sql("raw_default_latest")
    + " AS parsed_default FROM raw"
).fetchdf()
d = d.merge(parsed, on="loan_id", validate="one_to_one")
valid = (
    d.disposition_proxy
    & d.feature_date.notna()
    & d.parsed_default.gt(0)
    & np.isfinite(d.parsed_default)
    & np.isfinite(d.signed_loss)
    & d.event_date_values.eq(1)
    & d.default_amount_values.le(1)
    & d.loss_amount_values.le(1)
)
d["signed_feasible"] = valid
d["signed_ratio"] = np.where(d.parsed_default.gt(0), d.signed_loss / d.parsed_default, np.nan)
d["period"] = np.select(
    [d.credit_event_year <= 2018, d.credit_event_year <= 2022],
    ["training", "validation"],
    default="out_of_time",
)
summary = {}
for label, g in d[valid].groupby("period"):
    summary[label] = {
        "cases": len(g),
        "negative": int(g.signed_ratio.lt(0).sum()),
        "zero": int(g.signed_ratio.eq(0).sum()),
        "positive": int(g.signed_ratio.gt(0).sum()),
        "mean": float(g.signed_ratio.mean()),
        "minimum": float(g.signed_ratio.min()),
        "maximum": float(g.signed_ratio.max()),
    }
old = d[d.status.eq("research_eligible")]
np.testing.assert_allclose(old.signed_ratio, old.reported_loss_ratio)
out = root / "lgd-signed-feasibility-v0.1.0"
if out.exists():
    raise FileExistsError(out)
out.mkdir()
d.to_parquet(out / "signed_outcome_audit.parquet", index=False)
report = {
    "status": "feasibility_audit_not_target_approval",
    "periods": summary,
    "existing_584_outcomes_unchanged": True,
    "added_denominator_valid_cases": int(valid.sum() - 584),
    "limitations": [
        "Latest raw source amounts; no full raw-history signed consistency check in this feasibility audit.",
        "Negative source net losses are preserved, not interpreted as borrower profit.",
        "Target and model specification require explicit direction.",
    ],
}
(out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
