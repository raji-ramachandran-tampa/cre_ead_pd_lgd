"""Controlled ingestion utilities."""

from .duckdb_io import csv_to_parquet, register_parquet_view

__all__ = ["csv_to_parquet", "register_parquet_view"]

