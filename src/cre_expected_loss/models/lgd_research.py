"""Classical two-part source-loss-ratio research candidate, not approved workout LGD."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, TweedieRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ("acquisition_ltv", "underwritten_dscr")


def fit_two_part(frame: pd.DataFrame):
    """Fit positive-loss logistic probability times log-link Gamma severity.

    Loss ratios are nonnegative and unbounded; no tail clipping is applied.
    Inputs deliberately exclude event type, final losses, and resolution fields.
    """
    y = frame.reported_loss_ratio.to_numpy(dtype=float)
    if len(y) < 10 or not np.isfinite(y).all() or (y < 0).any():
        raise ValueError("Need at least ten finite nonnegative outcomes")
    positive = y > 0
    if positive.all() or not positive.any():
        raise ValueError("Two-part fit requires both zero and positive training losses")
    x = frame[list(FEATURES)].astype(float)
    if np.isinf(x.to_numpy()).any() or x.isna().all().any():
        raise ValueError("Features cannot contain infinity or be entirely missing")
    occurrence = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(C=1.0, max_iter=2000, random_state=20260901),
    )
    occurrence.fit(x, positive.astype(int))
    severity = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        TweedieRegressor(power=2, alpha=1.0, link="log", max_iter=2000, tol=1e-8),
    )
    severity.fit(x.loc[positive], y[positive])
    return occurrence, severity


def predict_two_part(models, frame: pd.DataFrame):
    x = frame[list(FEATURES)].astype(float)
    if np.isinf(x.to_numpy()).any():
        raise ValueError("Prediction features cannot contain infinity")
    probability = models[0].predict_proba(x)[:, 1]
    severity = models[1].predict(x)
    prediction = probability * severity
    if not np.isfinite(prediction).all() or (prediction < 0).any():
        raise ValueError("Invalid two-part predictions")
    return probability, severity, prediction


def fit_lgd_research(
    reconciliation_directory: Path,
    output_directory: Path,
    *,
    acknowledge_proxy_target: bool = False,
    train_end: date = date(2018, 12, 31),
    validation_end: date = date(2022, 12, 31),
) -> dict:
    """Write train-only fits and retrospective chronological comparison artifacts."""
    if not acknowledge_proxy_target:
        raise ValueError("Explicit acknowledgement of the proposed source-loss proxy is required")
    if train_end >= validation_end:
        raise ValueError("train_end must precede validation_end")
    source, output = Path(reconciliation_directory), Path(output_directory)
    if output.exists():
        raise FileExistsError(output)
    audit = json.loads((source / "reconciliation.json").read_text(encoding="utf-8"))
    frame = pd.read_parquet(source / "loan_reconciliation.parquet")
    frame = frame.loc[frame.status.eq("research_eligible")].copy()
    frame["sample"] = np.select(
        [
            frame.credit_event_date <= pd.Timestamp(train_end),
            frame.credit_event_date <= pd.Timestamp(validation_end),
        ],
        ["train", "validation"],
        default="comparison",
    )
    training = frame.loc[frame["sample"].eq("train")]
    models = fit_two_part(training)
    probability, severity, prediction = predict_two_part(models, frame)
    frame["positive_loss_probability"] = probability
    frame["conditional_severity"] = severity
    frame["two_part_prediction"] = prediction
    benchmark = float(training.reported_loss_ratio.mean())
    frame["mean_benchmark_prediction"] = benchmark
    metrics = {}
    for sample, group in frame.groupby("sample"):
        y = group.reported_loss_ratio.to_numpy()
        metrics[sample] = {"loans": len(group), "zero_losses": int((y == 0).sum())}
        for candidate in ("mean_benchmark", "two_part"):
            pred = group[candidate + "_prediction"].to_numpy()
            error = pred - y
            metrics[sample][candidate] = {
                "mae": float(np.abs(error).mean()),
                "rmse": float(np.sqrt((error**2).mean())),
                "mean_actual": float(y.mean()),
                "mean_predicted": float(pred.mean()),
                "exposure_weighted_mae": float(
                    np.average(np.abs(error), weights=group.default_amount)
                ),
            }
    report = {
        "status": "research_proposed_not_selected_or_approved",
        "version": "0.1.0",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "target": "source-reported net loss divided by default amount, uncapped",
        "source_sha256": audit["source_sha256"],
        "source_cutoff": audit["source_cutoff"],
        "features": list(FEATURES),
        "train_end": train_end.isoformat(),
        "validation_end": validation_end.isoformat(),
        "benchmark": benchmark,
        "hyperparameters": {"logistic_C": 1.0, "gamma_alpha": 1.0},
        "metrics": metrics,
        "limitations": audit["limitations"]
        + [
            "Retrospective disposition-time comparison; historical final-loss availability is unverified.",
            "Only two acquisition risk features; no downturn or scenario transmission is fitted.",
            "Rare explicit zeros can destabilize the occurrence fit; no final selection is made.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lgd-fit-", dir=output.parent) as temporary:
        import joblib

        stage = Path(temporary) / "artifacts"
        stage.mkdir()
        frame.to_parquet(stage / "predictions.parquet", index=False)
        joblib.dump({"models": models, "features": FEATURES}, stage / "model.joblib")
        (stage / "model_report.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        stage.rename(output)
    return report
