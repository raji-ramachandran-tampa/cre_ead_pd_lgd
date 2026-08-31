"""Minimal DuckDB utilities for controlled CSV and Parquet access."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _duckdb() -> Any:
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise RuntimeError("Install the project dependencies to use DuckDB") from exc
    return duckdb


def csv_to_parquet(source: Path, destination: Path) -> Path:
    """Convert a CSV snapshot to Parquet without mutating the source file."""
    source, destination = Path(source), Path(destination)
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    connection = _duckdb().connect()
    try:
        connection.execute(
            "COPY (SELECT * FROM read_csv_auto(?)) TO ? (FORMAT PARQUET)",
            [str(source), str(destination)],
        )
    finally:
        connection.close()
    return destination


def register_parquet_view(connection: Any, view_name: str, path: Path) -> None:
    """Register a read-only Parquet view using validated identifiers and parameters."""
    if not view_name.isidentifier():
        raise ValueError("view_name must be a valid identifier")
    if not Path(path).is_file():
        raise FileNotFoundError(path)
    connection.execute(
        f'CREATE OR REPLACE VIEW "{view_name}" AS SELECT * FROM read_parquet(?)',
        [str(path)],
    )

