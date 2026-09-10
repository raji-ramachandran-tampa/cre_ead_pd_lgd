"""Build typed, modeling-oriented Parquet tables from Fannie MFLPD ZIPs."""

from __future__ import annotations

import json
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .duckdb_io import _duckdb


def _sql_path(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def _extract_single_csv(archive_path: Path, directory: Path) -> Path:
    with zipfile.ZipFile(archive_path) as archive:
        members = [item for item in archive.infolist() if item.filename.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected exactly one CSV in {archive_path.name}")
        member = members[0]
        destination = directory / Path(member.filename).name
        with archive.open(member) as source, destination.open("xb") as target:
            while chunk := source.read(8 * 1024 * 1024):
                target.write(chunk)
        return destination


def build_fannie_parquet(
    release_directory: Path,
    processed_directory: Path,
    release: str,
) -> dict[str, Any]:
    """Create standardized monthly and annual-DSCR Parquet tables.

    The transformation reads source fields as strings and uses ``TRY_CAST`` so
    invalid source values become explicit nulls for later quality reporting.
    Raw ZIPs are never modified. A temporary expanded copy is deleted after the
    atomic Parquet build completes.
    """
    release_directory, processed_directory = Path(release_directory), Path(processed_directory)
    main_zip = release_directory / "Multifamily.zip"
    dscr_zip = release_directory / "Multifamily_DSCR.zip"
    for path in (main_zip, dscr_zip):
        if not path.is_file():
            raise FileNotFoundError(path)
    processed_directory.mkdir(parents=True, exist_ok=True)
    monthly = processed_directory / "fannie_monthly.parquet"
    dscr = processed_directory / "fannie_annual_dscr.parquet"
    quality = processed_directory / "quality_summary.json"
    if any(path.exists() for path in (monthly, dscr, quality)):
        raise FileExistsError(f"Processed release already exists: {processed_directory}")

    duckdb = _duckdb()
    with tempfile.TemporaryDirectory(
        prefix="fannie_stage_", dir=processed_directory.parent
    ) as stage:
        stage_path = Path(stage)
        main_csv = _extract_single_csv(main_zip, stage_path)
        dscr_csv = _extract_single_csv(dscr_zip, stage_path)
        monthly_tmp, dscr_tmp = stage_path / monthly.name, stage_path / dscr.name
        connection = duckdb.connect()
        try:
            date_expr = lambda name: (
                f"COALESCE(TRY_STRPTIME(\"{name}\", '%m/%d/%Y')::DATE, "
                f"TRY_STRPTIME(\"{name}\", '%Y-%m-%d')::DATE)"
            )
            number_expr = lambda name: (
                f"TRY_CAST(REGEXP_REPLACE(\"{name}\", '[,$%]', '', 'g') AS DOUBLE)"
            )
            connection.execute(
                f"""
                COPY (
                  WITH base AS (
                  SELECT
                    TRIM("Loan Number") AS loan_id,
                    {date_expr("Reporting Period Date")} AS reporting_date,
                    {date_expr("Acquisition Date")} AS acquisition_date,
                    {date_expr("Note Date")} AS note_date,
                    {date_expr("Maturity Date - Current")} AS maturity_date,
                    {date_expr("Credit Event Date")} AS credit_event_date,
                    NULLIF(TRIM("Credit Event Type"), '') AS credit_event_type,
                    {date_expr("Liquidation/Prepayment Date")} AS liquidation_date,
                    NULLIF(TRIM("Liquidation/Prepayment Code"), '') AS liquidation_code,
                    {number_expr("UPB - Current")} AS current_upb,
                    {number_expr("Default Amount")} AS default_amount,
                    {number_expr("Lifetime Net Credit Loss Amount")} AS lifetime_net_credit_loss_amount,
                    {number_expr("Loan Acquisition LTV")} AS acquisition_ltv,
                    {number_expr("Underwritten DSCR")} AS underwritten_dscr,
                    {number_expr("Original Interest Rate")} AS original_interest_rate,
                    {number_expr("Note Rate")} AS note_rate,
                    {number_expr("Loan Age")} AS loan_age,
                    NULLIF(TRIM("Loan Payment Status"), '') AS payment_status,
                    NULLIF(TRIM("SDQ Indicator"), '') AS sdq_indicator,
                    NULLIF(TRIM("Specific Property Type"), '') AS property_type,
                    NULLIF(TRIM("Property State"), '') AS property_state,
                    NULLIF(TRIM("Amortization Type"), '') AS amortization_type,
                    NULLIF(TRIM("Interest Type"), '') AS interest_type,
                    MIN({date_expr("Credit Event Date")}) OVER
                        (PARTITION BY TRIM("Loan Number")) AS first_credit_event_date,
                    CASE WHEN MIN({date_expr("Credit Event Date")}) OVER
                                      (PARTITION BY TRIM("Loan Number")) IS NOT NULL
                           AND DATE_TRUNC('month', MIN({date_expr("Credit Event Date")}) OVER
                                      (PARTITION BY TRIM("Loan Number")))
                               = DATE_TRUNC('month', {date_expr("Reporting Period Date")})
                         THEN 1 ELSE 0 END AS month_matched_default_event,
                    CASE WHEN {number_expr("Default Amount")} > 0
                         THEN {number_expr("Lifetime Net Credit Loss Amount")}
                              / {number_expr("Default Amount")} END AS provisional_raw_lgd,
                    {number_expr("UPB - Current")} AS benchmark_ead
                  FROM read_csv('{_sql_path(main_csv)}', header=true, all_varchar=true)
                  )
                  SELECT * EXCLUDE (month_matched_default_event),
                         CASE WHEN first_credit_event_date IS NOT NULL
                                   AND reporting_date = MAX(reporting_date) FILTER (
                                       WHERE reporting_date <= first_credit_event_date
                                   ) OVER (PARTITION BY loan_id)
                              THEN 1 ELSE 0 END AS proposed_default_event
                  FROM base
                ) TO '{_sql_path(monthly_tmp)}'
                (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)
                """
            )
            connection.execute(
                f"""
                COPY (
                  SELECT TRIM("Loan Number") AS loan_id,
                         TRY_CAST("Year" AS INTEGER) AS dscr_year,
                         {number_expr("Year DSCR")} AS annual_dscr
                  FROM read_csv('{_sql_path(dscr_csv)}', header=true, all_varchar=true)
                ) TO '{_sql_path(dscr_tmp)}'
                (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)
                """
            )
            summary = connection.execute(
                f"""
                SELECT COUNT(*) AS rows,
                       COUNT(DISTINCT loan_id) AS loans,
                       MIN(reporting_date) AS min_reporting_date,
                       MAX(reporting_date) AS max_reporting_date,
                       SUM(proposed_default_event) AS proposed_default_events,
                       COUNT(*) FILTER (WHERE reporting_date IS NULL) AS invalid_reporting_dates,
                       COUNT(*) FILTER (WHERE current_upb < 0) AS negative_upb_rows,
                       COUNT(*) FILTER (WHERE loan_id IS NULL OR loan_id = '') AS missing_loan_ids
                FROM read_parquet('{_sql_path(monthly_tmp)}')
                """
            ).fetchone()
            dscr_summary = connection.execute(
                f"SELECT COUNT(*), COUNT(DISTINCT loan_id), COUNT(*) FILTER "
                f"(WHERE dscr_year IS NULL OR annual_dscr IS NULL) FROM read_parquet('{_sql_path(dscr_tmp)}')"
            ).fetchone()
        finally:
            connection.close()
        monthly_tmp.replace(monthly)
        dscr_tmp.replace(dscr)

    report = {
        "schema_version": "1.0.0",
        "release": release,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "definition_status": "proposed_not_approved",
        "outcome_version": "fannie_outcomes_0.3.0",
        "monthly": dict(
            zip(
                [
                    "rows",
                    "loans",
                    "min_reporting_date",
                    "max_reporting_date",
                    "proposed_default_events",
                    "invalid_reporting_dates",
                    "negative_upb_rows",
                    "missing_loan_ids",
                ],
                summary,
                strict=True,
            )
        ),
        "annual_dscr": {
            "rows": dscr_summary[0],
            "loans": dscr_summary[1],
            "invalid_rows": dscr_summary[2],
        },
    }
    for section in ("monthly", "annual_dscr"):
        for key, value in report[section].items():
            if hasattr(value, "isoformat"):
                report[section][key] = value.isoformat()
    quality.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {"monthly": monthly, "annual_dscr": dscr, "quality_summary": quality, "summary": report}
