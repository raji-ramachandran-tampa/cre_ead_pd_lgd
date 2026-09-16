"""Reproducible comparison of fitted Fannie Mae PD hazard candidates."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_CANDIDATES = {
    "baseline": "pd-hazard-v0.1.1",
    "revised_macro": "pd-hazard-macro-v0.2.0",
    "vintage_macro": "pd-hazard-alfred-v0.3.0",
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _metric_rows(reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate, report in reports.items():
        for sample, metrics in report["metrics"].items():
            rows.append({"candidate": candidate, "sample": sample, **metrics})
    return rows


def _coefficient_summary(candidate: str, path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"candidate": candidate, "available": False}
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    coefficients = [
        (row["transformed_feature"], float(row["log_odds_coefficient"])) for row in rows
    ]
    largest = sorted(coefficients, key=lambda item: abs(item[1]), reverse=True)[:10]
    return {
        "candidate": candidate,
        "available": True,
        "coefficient_count": len(coefficients),
        "positive_count": sum(value > 0 for _, value in coefficients),
        "negative_count": sum(value < 0 for _, value in coefficients),
        "largest_absolute_coefficients": [
            {"feature": feature, "coefficient": value} for feature, value in largest
        ],
    }


def _assessment(reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    test = {name: report["metrics"]["test"] for name, report in reports.items()}
    validation = {name: report["metrics"]["validation"] for name, report in reports.items()}
    best_auc = max(test, key=lambda name: test[name]["roc_auc"])
    best_log_loss = min(test, key=lambda name: test[name]["log_loss"])
    best_brier = min(test, key=lambda name: test[name]["brier_score"])
    best_calibration = min(
        test, key=lambda name: abs(1.0 - test[name]["observed_to_expected"])
    )
    return {
        "test_discrimination_leader": best_auc,
        "test_log_loss_leader": best_log_loss,
        "test_brier_leader": best_brier,
        "test_oe_closest_to_one": best_calibration,
        "performance_stability": {
            name: {
                "auc_change_train_to_test": metrics["roc_auc"]
                - reports[name]["metrics"]["train"]["roc_auc"],
                "auc_change_validation_to_test": metrics["roc_auc"]
                - validation[name]["roc_auc"],
                "test_observed_to_expected": metrics["observed_to_expected"],
            }
            for name, metrics in test.items()
        },
        "conclusion": (
            "No model is automatically selected. Test discrimination and proper scoring rules "
            "must be considered with calibration, temporal stability, data-vintage fitness, "
            "conceptual soundness, limitations, independent validation, and governance approval."
        ),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Fannie Mae PD Candidate Comparison",
        "",
        f"Generated: {report['created_at_utc']}",
        "",
        "Status: development evidence; proposed, not approved.",
        "",
        "## Out-of-time test comparison",
        "",
        "| Candidate | ROC AUC | Average precision | Brier | Log loss | O/E | Events |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["metrics"]:
        if row["sample"] == "test":
            lines.append(
                f"| {row['candidate']} | {row['roc_auc']:.6f} | "
                f"{row['average_precision']:.6f} | {row['brier_score']:.8f} | "
                f"{row['log_loss']:.8f} | {row['observed_to_expected']:.3f} | "
                f"{row['weighted_events']:.0f} |"
            )
    assessment = report["assessment"]
    lines.extend(
        [
            "",
            "## Diagnostic interpretation",
            "",
            f"- Highest test ROC AUC: `{assessment['test_discrimination_leader']}`.",
            f"- Lowest test log loss: `{assessment['test_log_loss_leader']}`.",
            f"- Lowest test Brier score: `{assessment['test_brier_leader']}`.",
            f"- Test O/E closest to one: `{assessment['test_oe_closest_to_one']}`.",
            "- O/E below one indicates overprediction; O/E above one indicates underprediction.",
            (
                "- Coefficients are standardized-log-odds diagnostics and should not be "
                "interpreted as unscaled marginal effects."
            ),
            "",
            "## Selection conclusion",
            "",
            assessment["conclusion"],
            "",
            (
                "The 2023–2026 test period has already been reviewed and is therefore an "
                "out-of-time comparison sample, not a pristine final holdout."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def compare_pd_candidates(
    release_artifact_root: Path,
    output_directory: Path,
    candidates: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Compare existing model reports without refitting or modifying source artifacts."""
    candidate_map = candidates or DEFAULT_CANDIDATES
    reports = {
        name: _read_json(Path(release_artifact_root) / version / "model_report.json")
        for name, version in candidate_map.items()
    }
    cutoffs = {(r["train_end"], r["validation_end"]) for r in reports.values()}
    if len(cutoffs) != 1:
        raise ValueError("Candidate reports do not use identical chronological cutoffs")
    sample_counts = {
        tuple(r["metrics"][sample]["sample_rows"] for sample in ("train", "validation", "test"))
        for r in reports.values()
    }
    if len(sample_counts) != 1:
        raise ValueError("Candidate reports do not use identical sampled populations")

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    for name in ("comparison.json", "metrics.csv", "comparison.md"):
        if (output / name).exists():
            raise FileExistsError(f"Comparison artifact already exists: {output / name}")

    metric_rows = _metric_rows(reports)
    result = {
        "comparison_id": "fannie_pd_candidate_comparison",
        "status": "development_evidence_proposed_not_approved",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "candidate_artifacts": candidate_map,
        "common_train_end": next(iter(cutoffs))[0],
        "common_validation_end": next(iter(cutoffs))[1],
        "metrics": metric_rows,
        "coefficient_diagnostics": [
            _coefficient_summary(
                name, Path(release_artifact_root) / version / "coefficients.csv"
            )
            for name, version in candidate_map.items()
        ],
        "assessment": _assessment(reports),
        "limitations": [
            "Metrics are sampling-weighted estimates from the existing fitted artifacts.",
            (
                "Calibration is summarized by aggregate O/E; reliability-bin and slope/intercept "
                "analysis require retained row-level predictions in a future enhancement."
            ),
            "The test period has already been reviewed and is not a pristine final holdout.",
            "This comparison is development evidence and does not constitute model approval.",
        ],
    }
    (output / "comparison.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "metrics.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(metric_rows[0]))
        writer.writeheader()
        writer.writerows(metric_rows)
    (output / "comparison.md").write_text(_markdown(result), encoding="utf-8")
    return result
