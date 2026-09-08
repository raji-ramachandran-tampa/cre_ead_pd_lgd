"""Controlled, streaming intake of Fannie Mae MFLPD ZIP releases."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_MAIN_COLUMNS = {
    "Loan Number",
    "Acquisition Date",
    "Credit Event Date",
    "Lifetime Net Credit Loss Amount",
    "Default Amount",
    "Reporting Period Date",
    "UPB - Current",
    "Loan Payment Status",
    "SDQ Indicator",
}
REQUIRED_DSCR_COLUMNS = {"Loan Number", "Year", "Year DSCR"}


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_zip(path: Path, role: str, count_rows: bool = False) -> dict[str, Any]:
    """Inspect one single-CSV archive without extracting or exposing data rows."""
    path = Path(path)
    if role not in {"main", "dscr"}:
        raise ValueError("role must be 'main' or 'dscr'")
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise ValueError(f"Not a valid ZIP file: {path}")

    with zipfile.ZipFile(path) as archive:
        csv_members = [item for item in archive.infolist() if item.filename.lower().endswith(".csv")]
        if len(csv_members) != 1:
            raise ValueError(f"Expected exactly one CSV member in {path.name}")
        member = csv_members[0]
        with archive.open(member) as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
            reader = csv.reader(text)
            raw_columns = next(reader)
            columns = [column.strip() for column in raw_columns]
            row_count = sum(1 for _ in reader) if count_rows else None

    required = REQUIRED_MAIN_COLUMNS if role == "main" else REQUIRED_DSCR_COLUMNS
    expected_count = 62 if role == "main" else 3
    missing = sorted(required.difference(columns))
    if len(columns) != expected_count or missing:
        raise ValueError(
            f"Unexpected {role} schema: {len(columns)} columns; missing required {missing}"
        )

    return {
        "role": role,
        "archive_name": path.name,
        "archive_bytes": path.stat().st_size,
        "archive_sha256": _sha256(path),
        "member_name": member.filename,
        "member_bytes": member.file_size,
        "member_crc32": f"{member.CRC:08x}",
        "column_count": len(columns),
        "columns": columns,
        "data_row_count": row_count,
    }


def build_release_manifest(release_directory: Path, release: str, count_rows: bool = False) -> dict[str, Any]:
    """Build a deterministic-content manifest for one MFLPD quarterly release."""
    release_directory = Path(release_directory)
    main = release_directory / "Multifamily.zip"
    dscr = release_directory / "Multifamily_DSCR.zip"
    return {
        "manifest_schema_version": "1.0.0",
        "source_id": "fannie_mflpd",
        "release": release,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_directory": str(release_directory.resolve()),
        "archives": [
            inspect_zip(main, "main", count_rows=count_rows),
            inspect_zip(dscr, "dscr", count_rows=count_rows),
        ],
    }


def write_manifest(manifest: dict[str, Any], destination: Path) -> Path:
    """Write a new manifest, refusing to replace an existing snapshot record."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Manifest already exists: {destination}")
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return destination.resolve()

