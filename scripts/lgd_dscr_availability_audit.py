"""Aggregate evidence audit; never infer DSCR publication from fiscal year."""

import argparse
import csv
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd


def run(root: Path, output: Path):
    if output.exists():
        raise FileExistsError(output)
    source = root / "artifacts/2026Q1/lgd-history-research-v0.1.1/features.parquet"
    raw = root / "raw/2026Q1/Multifamily_DSCR.zip"
    with zipfile.ZipFile(raw) as archive:
        member = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
        with archive.open(member) as stream:
            header = next(csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig")))
    frame = pd.read_parquet(source)
    # Announcement planned late January 2021; Jan 1 is an intentionally
    # optimistic lower boundary, not an asserted exact launch/publication date.
    frame["predates_public_file_introduction_year"] = frame.anchor_date < pd.Timestamp("2021-01-01")
    frame["availability_evidence"] = frame.predates_public_file_introduction_year.map(
        {True: "predates_public_file_introduction_year", False: "row_publication_unverified"}
    )
    summary = []
    for (scope, lag), g in frame.groupby(["scope", "dscr_lag"]):
        summary.append(
            {
                "scope": scope,
                "dscr_lag": int(lag),
                "cases": len(g),
                "anchors_before_2021": int(g.predates_public_file_introduction_year.sum()),
                "before_2021_with_dscr": int(
                    (g.predates_public_file_introduction_year & g.historical_dscr.notna()).sum()
                ),
                "nonmissing_dscr": int(g.historical_dscr.notna().sum()),
                "verified_row_publication_dates": 0,
            }
        )
    report = {
        "status": "availability_not_established_no_model_selection",
        "raw_headers": header,
        "local_raw_release_directories": sorted(
            p.name for p in (root / "raw").iterdir() if p.is_dir()
        ),
        "summary": summary,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "raw_dscr_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "evidence": {
            "announcement_date": "2020-12-18",
            "announced_launch": "late January 2021, planned",
            "public_updates": "quarterly, most recent annual DSCR available",
            "year_field": "year associated with fiscal year-end statement; not availability date",
        },
        "sources": [
            "https://capitalmarkets.fanniemae.com/mortgage-backed-securities/multifamily-loan-performance-data-be-enhanced-additional-data-attributes-and-accompanying-new-file",
            "https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-glossary-file-layout.pdf",
        ],
        "conclusions": [
            "Neither one-year nor two-year lag establishes actual historical publication.",
            "Public historical-file availability is distinct from lender/servicer receipt of financial statements.",
            "Only one local source release is present; first appearance and revisions cannot be reconstructed.",
            "Existing DSCR LGD and PD results remain retrospective research; no accuracy metric altered.",
            "Need dated archived releases for public-data use, or actual receipt/availability records for lender use.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dscr-audit-", dir=output.parent) as temporary:
        stage = Path(temporary) / "output"
        stage.mkdir()
        frame[
            [
                "loan_id",
                "scope",
                "dscr_lag",
                "anchor_date",
                "dscr_reference_year",
                "availability_evidence",
            ]
        ].to_parquet(stage / "availability_audit.parquet", index=False)
        (stage / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        stage.rename(output)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--fannie-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    run(args.fannie_root, args.output)
