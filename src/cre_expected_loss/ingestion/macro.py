"""Controlled FRED CSV snapshots and point-in-time-lagged macro features."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FRED_SERIES = {
    "UNRATE": {"feature": "unemployment_rate", "frequency": "monthly", "lag_months": 1},
    "NFCI": {"feature": "financial_conditions", "frequency": "weekly", "lag_months": 1},
    "DGS10": {"feature": "treasury_10y", "frequency": "daily", "lag_months": 1},
    "BAA10YM": {"feature": "baa_treasury_spread", "frequency": "monthly", "lag_months": 1},
    "RRVRUSQ156N": {"feature": "rental_vacancy_rate", "frequency": "quarterly", "lag_months": 2},
    "CUSR0000SEHA": {"feature": "rent_cpi", "frequency": "monthly", "lag_months": 1},
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_fred_snapshot(root: Path, snapshot_date: str) -> dict[str, Any]:
    """Download immutable FRED graph CSVs and write a source manifest."""
    destination = Path(root) / "raw" / "fred" / snapshot_date
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(root) / "manifests" / f"fred_{snapshot_date}.json"
    if manifest_path.exists() or any(destination.iterdir()):
        raise FileExistsError(f"FRED snapshot already exists: {snapshot_date}")
    files = []
    for series_id, specification in FRED_SERIES.items():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        path = destination / f"{series_id}.csv"
        request = urllib.request.Request(url, headers={"User-Agent": "cre-expected-loss/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response, path.open("xb") as stream:
            stream.write(response.read())
        files.append(
            {
                "series_id": series_id,
                **specification,
                "url": url,
                "filename": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    manifest = {
        "schema_version": "1.0.0",
        "source": "FRED graph CSV",
        "snapshot_date": snapshot_date,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "vintage_status": "latest_revised_not_historical_vintage",
        "files": files,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_monthly_macro_features(root: Path, snapshot_date: str) -> dict[str, Any]:
    """Create a monthly feature panel using conservative source-specific lags."""
    import pandas as pd

    raw = Path(root) / "raw" / "fred" / snapshot_date
    output = Path(root) / "processed" / snapshot_date
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "macro_monthly.parquet"
    report_path = output / "quality_summary.json"
    if parquet_path.exists() or report_path.exists():
        raise FileExistsError(f"Processed macro snapshot already exists: {snapshot_date}")

    panel = pd.DataFrame({"as_of_date": pd.date_range("1950-01-01", snapshot_date, freq="MS")})
    summary = {}
    for series_id, specification in FRED_SERIES.items():
        frame = pd.read_csv(raw / f"{series_id}.csv")
        frame.columns = ["observation_date", "value"]
        frame["observation_date"] = pd.to_datetime(frame["observation_date"], errors="coerce")
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame = frame.dropna().set_index("observation_date").sort_index()
        monthly = frame["value"].resample("MS").mean().to_frame()
        monthly.index = monthly.index + pd.offsets.MonthBegin(specification["lag_months"])
        monthly = monthly[~monthly.index.duplicated(keep="last")]
        feature = specification["feature"]
        panel = panel.merge(
            monthly.rename(columns={"value": feature}),
            left_on="as_of_date",
            right_index=True,
            how="left",
        )
        if specification["frequency"] == "quarterly":
            panel[feature] = panel[feature].ffill(limit=2)
        summary[series_id] = {
            "feature": feature,
            "nonmissing_months": int(panel[feature].notna().sum()),
            "first_available_month": panel.loc[panel[feature].notna(), "as_of_date"]
            .min()
            .date()
            .isoformat(),
            "last_available_month": panel.loc[panel[feature].notna(), "as_of_date"]
            .max()
            .date()
            .isoformat(),
            "lag_months": specification["lag_months"],
        }
    panel["rent_cpi_yoy"] = panel["rent_cpi"].pct_change(12, fill_method=None) * 100.0
    panel["unemployment_change_12m"] = panel["unemployment_rate"].diff(12)
    panel.to_parquet(parquet_path, index=False)
    report = {
        "snapshot_date": snapshot_date,
        "vintage_status": "latest_revised_not_historical_vintage",
        "rows": len(panel),
        "series": summary,
        "output": str(parquet_path.resolve()),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
