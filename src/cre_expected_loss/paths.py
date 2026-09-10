"""Portable local-path resolution for restricted data."""

from __future__ import annotations

import os
from pathlib import Path


FANNIE_ROOT_ENV = "FANNIE_MFLPD_ROOT"
DEFAULT_FANNIE_DATA_ROOT = Path(r"C:\Users\Rajir\data\fanniemae")


def fannie_data_root() -> Path:
    """Return the configured Fannie root or the project user's local default."""
    configured = os.environ.get(FANNIE_ROOT_ENV)
    return Path(configured).expanduser().resolve() if configured else DEFAULT_FANNIE_DATA_ROOT


def fannie_release_directory(release: str) -> Path:
    """Return the immutable raw directory for a validated YYYYQn release ID."""
    if len(release) != 6 or release[:4].isdigit() is False or release[4] != "Q":
        raise ValueError("release must use YYYYQn format")
    if release[5] not in "1234":
        raise ValueError("release quarter must be Q1 through Q4")
    return fannie_data_root() / "raw" / release
