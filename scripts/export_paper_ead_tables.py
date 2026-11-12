"""Export manuscript aggregate EAD tables from frozen reports; no loan data."""

import argparse
import hashlib
import json
import math
from pathlib import Path

ADVANCED = "ead-advanced-residual-v0.1.1"
PAYMENT = "ead-payment-history-v0.1.1"


def value(row):
    x = row["absolute_error_over_actual"]
    if not math.isfinite(x) or x < 0:
        raise ValueError("Invalid aggregate error")
    return x * 100


def render_advanced(report):
    rows = [
        "| Horizon and cohort | Cases | Amortization | Guarded ridge | Nonlinear residual |",
        "|---|---:|---:|---:|---:|",
    ]
    for cohort, label, key in [
        (None, "historical refits", "historical_metrics"),
        ("2019_2022", "2019–2022", "later_metrics"),
        ("2023_onward", "2023 onward", "later_metrics"),
    ]:
        for horizon in [3, 12]:
            group = {
                m["candidate"]: m
                for m in report[key]
                if m["horizon_months"] == horizon and (cohort is None or m["partition"] == cohort)
            }
            candidates = [
                group[n] for n in ["io_clock_sensitivity", "guarded_ridge", "boosted_residual"]
            ]
            if len({m["cases"] for m in candidates}) != 1:
                raise ValueError("Unmatched table population")
            rows.append(
                f"| {horizon}-month, {label} | {candidates[0]['cases']} | "
                + " | ".join(f"{value(m):.4f}" for m in candidates)
                + " |"
            )
    return "\n".join(rows)


def render_payment(report):
    rows = [
        "| Horizon and cohort | Cases | Routed amortization reference | Prior-payment challenger |",
        "|---|---:|---:|---:|",
    ]
    for cohort, label in [
        ("through_2018", "through 2018"),
        ("2019_2022", "2019–2022"),
        ("2023_onward", "2023 onward"),
    ]:
        for horizon in [3, 12]:
            group = {
                m["candidate"]: m
                for m in report["metrics"]
                if m["horizon_months"] == horizon
                and m["partition"] == cohort
                and m["scope"] == "all_initial_eligible"
            }
            a, b = group["post_io_reference"], group["payment_history_prediction"]
            if a["cases"] != b["cases"]:
                raise ValueError("Unmatched table population")
            rows.append(
                f"| {horizon}-month, {label} | {a['cases']} | {value(a):.5f} | {value(b):.5f} |"
            )
    return "\n".join(rows)


def replace_table(text, marker, table):
    start = f"<!-- {marker}_START -->"
    end = f"<!-- {marker}_END -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("Unique manuscript markers required")
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[:a] + "\n" + table + "\n" + text[b:]


def run(artifact_root, paper_root, update_manuscript=False):
    paths = [artifact_root / ADVANCED / "report.json", artifact_root / PAYMENT / "report.json"]
    reports = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    tables = [render_advanced(reports[0]), render_payment(reports[1])]
    names = ["ead_advanced_comparison.md", "ead_payment_reconstruction.md"]
    manifest = {
        "status": "aggregate_table_export_not_independent_model_validation",
        "units": "100 * sum_absolute_error_dollars / sum_observed_scheduled_principal",
        "inputs": {
            str(p.relative_to(artifact_root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths
        },
        "export_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "populations": "Advanced supported cases; payment table full initially eligible cases; not interchangeable",
    }
    text = (paper_root / "manuscript.md").read_text(encoding="utf-8")
    if update_manuscript:
        for marker, table in zip(["EAD_ADVANCED_TABLE", "EAD_PAYMENT_TABLE"], tables, strict=True):
            text = replace_table(text, marker, table)
    destination = paper_root / "tables"
    destination.mkdir(parents=True, exist_ok=True)
    for name, table in zip(names, tables, strict=True):
        (destination / name).write_text(
            table + "\n\nUnits: aggregate absolute error percent.\n", encoding="utf-8"
        )
    (destination / "ead_table_provenance.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if update_manuscript:
        (paper_root / "manuscript.md").write_text(text, encoding="utf-8")
    print("Exported two aggregate tables with source hashes; no loan-level data read.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--artifact-root", type=Path, required=True)
    p.add_argument("--paper-root", type=Path, required=True)
    p.add_argument("--update-manuscript", action="store_true")
    a = p.parse_args()
    run(a.artifact_root, a.paper_root, a.update_manuscript)
