"""Portable local-path resolution for restricted data."""

from __future__ import annotations

import os
from pathlib import Path


FANNIE_ROOT_ENV = "FANNIE_MFLPD_ROOT"


def fannie_data_root() -> Path:
    """Return the external Fannie data root configured by the environment."""
    configured = os.environ.get(FANNIE_ROOT_ENV)
    if not configured:
        raise RuntimeError(
            f"Set {FANNIE_ROOT_ENV} to the external Fannie Mae data directory"
        )
    return Path(configured).expanduser().resolve()


def fannie_release_directory(release: str) -> Path:
    """Return the immutable raw directory for a validated YYYYQn release ID."""
    if len(release) != 6 or release[:4].isdigit() is False or release[4] != "Q":
        raise ValueError("release must use YYYYQn format")
    if release[5] not in "1234":
        raise ValueError("release quarter must be Q1 through Q4")
    return fannie_data_root() / "raw" / release

