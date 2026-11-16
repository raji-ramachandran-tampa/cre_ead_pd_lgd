"""Audit original Home Credit card schema; no application-to-card label join."""

import argparse
import hashlib
import json
from pathlib import Path

import duckdb

EXPECTED = {
    "SK_ID_PREV",
    "SK_ID_CURR",
    "MONTHS_BALANCE",
    "AMT_BALANCE",
    "AMT_CREDIT_LIMIT_ACTUAL",
    "SK_DPD",
    "SK_DPD_DEF",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(input_root, output):
    if output.exists():
        raise FileExistsError(output)
    source = input_root / "credit_card_balance.csv"
    dictionary = input_root / "HomeCredit_columns_description.csv"
    missing = [p.name for p in [source, dictionary] if not p.is_file()]
    if missing:
        raise FileNotFoundError("Original competition files required: " + ", ".join(missing))
    con = duckdb.connect()
    try:
        columns = [
            r[0]
            for r in con.execute(
                "DESCRIBE SELECT * FROM read_csv(?,header=true,all_varchar=true)", [str(source)]
            ).fetchall()
        ]
        if not EXPECTED.issubset(columns):
            raise ValueError(
                "Expected schema missing: " + ", ".join(sorted(EXPECTED - set(columns)))
            )
        con.execute(
            """CREATE TABLE monthly AS SELECT NULLIF(TRIM(SK_ID_PREV),'') account_id,
            NULLIF(TRIM(SK_ID_CURR),'') application_link,
            TRY_CAST(MONTHS_BALANCE AS DOUBLE) month_index,TRY_CAST(AMT_BALANCE AS DOUBLE) drawn_balance,
            TRY_CAST(AMT_CREDIT_LIMIT_ACTUAL AS DOUBLE) credit_limit,
            TRY_CAST(SK_DPD AS DOUBLE) dpd,TRY_CAST(SK_DPD_DEF AS DOUBLE) dpd_def
            FROM read_csv(?,header=true,all_varchar=true)""",
            [str(source)],
        )
        quality = (
            con.execute("""SELECT COUNT(*) rows_count,COUNT(DISTINCT account_id) accounts,
            COUNT(DISTINCT application_link) application_links,
            COUNT(*) FILTER(WHERE account_id IS NULL OR application_link IS NULL) missing_ids,
            COUNT(*) FILTER(WHERE month_index IS NULL OR NOT isfinite(month_index) OR month_index<>floor(month_index)) bad_month_index,
            COUNT(*) FILTER(WHERE drawn_balance IS NULL OR NOT isfinite(drawn_balance)) invalid_balance,
            COUNT(*) FILTER(WHERE credit_limit IS NULL OR NOT isfinite(credit_limit)) invalid_limit,
            COUNT(*) FILTER(WHERE drawn_balance<0) negative_balance,
            COUNT(*) FILTER(WHERE credit_limit<0) negative_limit,
            COUNT(*) FILTER(WHERE credit_limit<=drawn_balance) no_positive_undrawn,
            COUNT(*) FILTER(WHERE dpd IS NULL OR NOT isfinite(dpd) OR dpd<0) unknown_dpd,
            COUNT(*) FILTER(WHERE dpd>=90) candidate_90dpd_rows FROM monthly""")
            .fetchdf()
            .iloc[0]
            .to_dict()
        )
        duplicate_keys = con.execute(
            "SELECT COUNT(*) FROM (SELECT account_id,month_index FROM monthly GROUP BY 1,2 HAVING COUNT(*)>1)".replace(
                "GROUP BY 1", "GROUP BY 1"
            )
        ).fetchone()[0]
        crosslinks = con.execute(
            "SELECT COUNT(*) FROM (SELECT account_id FROM monthly GROUP BY 1 HAVING COUNT(DISTINCT application_link)>1)".replace(
                "GROUP BY 1", "GROUP BY 1"
            )
        ).fetchone()[0]
    finally:
        con.close()
    report = {
        "status": "schema_audit_only_target_semantics_not_verified",
        "source_sha256": sha256(source),
        "dictionary_sha256": sha256(dictionary),
        "columns": columns,
        "quality": {k: int(v) for k, v in quality.items()},
        "duplicate_account_month_keys": duplicate_keys,
        "accounts_multiple_application_links": crosslinks,
        "access_terms_verified": False,
        "dictionary_semantics_reviewed": False,
        "calendar_dates_available": "not_established_months_are_relative",
        "limits": [
            "Expected column mapping is provisional until official dictionary reviewed",
            "Application TARGET is not a historical card default/EAD label",
            "SK_DPD threshold is a proposed proxy, not verified contractual default",
            "SK_ID_CURR application linkage does not prove ultimate borrower identity",
            "No target building, model fitting, CCF clipping or CRE integration in audit",
        ],
    }
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, allow_nan=False))
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.input_root, a.output)
