"""Controlled ingestion utilities."""

from .duckdb_io import csv_to_parquet, register_parquet_view
from .fannie import build_release_manifest, inspect_zip, write_manifest
from .fannie_dataset import build_fannie_parquet
from .macro import (
    build_alfred_initial_release_features,
    build_monthly_macro_features,
    download_alfred_initial_releases,
    download_fred_snapshot,
)

__all__ = [
    "build_alfred_initial_release_features",
    "build_fannie_parquet",
    "build_monthly_macro_features",
    "build_release_manifest",
    "csv_to_parquet",
    "download_alfred_initial_releases",
    "download_fred_snapshot",
    "inspect_zip",
    "register_parquet_view",
    "write_manifest",
]
