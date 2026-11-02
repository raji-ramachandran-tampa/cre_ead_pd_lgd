"""Nonlinear schedule-residual EAD research, with temporal calibration."""

import argparse
import hashlib
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor

from .ead_diagnostics import fit_fold
from .ead_research import FEATURES, prepare, score

PARAMETERS = {
    "max_iter": 120,
    "learning_rate": 0.05,
    "max_leaf_nodes": 7,
    "max_depth": 3,
    "min_samples_leaf": 30,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": 20261102,
}
FOLDS = [(2008, 2011), (2011, 2014), (2014, 2018), (2018, 2022)]


def io_guard(frame):
    return frame.remaining_io.ge(frame.horizon_months)


def x_values(frame):
    x = frame[FEATURES].copy()
    x["schedule_fraction"] = frame.io_clock_sensitivity / frame.anchor_upb
    return x


def residual_target(frame):
    return (frame.onset_scheduled_upb - frame.io_clock_sensitivity) / frame.anchor_upb


def fit_residual(train, quantile=None):
    model = HistGradientBoostingRegressor(
        **PARAMETERS,
        loss="squared_error" if quantile is None else "quantile",
        **({} if quantile is None else {"quantile": quantile}),
    )
    model.fit(x_values(train), residual_target(train))
    return model


def predict_residual(model, frame):
    values = model.predict(x_values(frame))
    # IO guard applies to scheduled principal only, not economic/participation exposure.
    return np.where(io_guard(frame), 0.0, values)


def prediction(model, frame):
    p = frame.io_clock_sensitivity.to_numpy() + frame.anchor_upb.to_numpy() * predict_residual(
        model, frame
    )
    p = np.where(io_guard(frame), frame.anchor_upb, p)
    if not np.isfinite(p).all() or (p < 0).any():
        raise ValueError("Invalid EAD prediction, no clipping")
    return p


def conformal_radius(scores, alpha=0.1):
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Finite nonnegative calibration scores required")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between0and1")
    rank = math.ceil((len(values) + 1) * (1 - alpha))
    if rank > len(values):
        raise ValueError("Insufficient calibration cases for finite radius")
    return float(np.partition(values, rank - 1)[rank - 1])


def assert_temporal(train, test):
    if set(train.loan_id) & set(test.loan_id):
        raise ValueError("Overlapping loans")
    if train.onset_date.max() >= test.onset_date.min():
        raise ValueError("Nonchronological outcomes")


def bounds(models, frame, radius):
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("Finite nonnegative calibration radius required")
    qlo = predict_residual(models["q05"], frame)
    qhi = predict_residual(models["q95"], frame)
    crossing = int((qlo > qhi).sum())
    # Explicit interval envelope handles quantile crossing; report raw crossing count.
    lo = frame.io_clock_sensitivity + frame.anchor_upb * (np.minimum(qlo, qhi) - radius)
    hi = frame.io_clock_sensitivity + frame.anchor_upb * (np.maximum(qlo, qhi) + radius)
    lo = np.maximum(0, lo)  # nonnegative exposure domain, not point-prediction clipping
    guard = io_guard(frame)
    lo = np.where(guard, frame.anchor_upb, lo)
    hi = np.where(guard, frame.anchor_upb, hi)
    if not np.isfinite(lo).all() or not np.isfinite(hi).all() or (lo > hi).any():
        raise ValueError("Invalid exposure interval")
    return lo, hi, crossing


def run(source, output):
    if output.exists():
        raise FileExistsError(output)
    raw = prepare(pd.read_parquet(source / "benchmark_cases.parquet"))
    frame = raw[
        raw.eligible & raw.schedule_status.eq("supported") & raw.io_clock_sensitivity.notna()
    ].copy()
    if frame.duplicated(["loan_id", "horizon_months"]).any():
        raise ValueError("Duplicate target")
    if not np.isfinite(x_values(frame)).all().all():
        raise ValueError("Incomplete predictors")
    all_predictions = []
    historical = []
    models = {}
    metrics = []
    interval_metrics = []
    training_counts = []
    for horizon, g in frame.groupby("horizon_months"):
        g = g.copy()
        train = g[g.onset_date.dt.year.le(2018)]
        later = g[g.onset_date.dt.year.gt(2018)].copy()
        assert_temporal(train, later)
        model = fit_residual(train)
        models[f"mean_{horizon}"] = model
        later["boosted_residual"] = prediction(model, later)
        later["guarded_ridge"] = fit_fold(train, later)
        later.loc[io_guard(later), "guarded_ridge"] = later.loc[io_guard(later), "anchor_upb"]
        # Uncertainty models have an earlier fit cutoff and separate temporal calibration.
        interval_train = g[g.onset_date.dt.year.le(2014)]
        calibration = g[g.onset_date.dt.year.between(2015, 2018)]
        assert_temporal(interval_train, calibration)
        assert_temporal(calibration, later)
        qm = {"q05": fit_residual(interval_train, 0.05), "q95": fit_residual(interval_train, 0.95)}
        a, b, _ = bounds(qm, calibration, 0.0)
        scores = np.maximum.reduce(
            [
                (a - calibration.onset_scheduled_upb) / calibration.anchor_upb,
                (calibration.onset_scheduled_upb - b) / calibration.anchor_upb,
                np.zeros(len(calibration)),
            ]
        )
        radius = conformal_radius(scores)
        lo, hi, cross = bounds(qm, later, radius)
        later["lower_90"] = lo
        later["upper_90"] = hi
        models[f"interval_{horizon}"] = {**qm, "radius": radius}
        training_counts.append(
            {
                "horizon_months": int(horizon),
                "mean_train": len(train),
                "quantile_train": len(interval_train),
                "calibration": len(calibration),
                "calibration_radius_normalized": radius,
                "raw_later_quantile_crossings": cross,
            }
        )
        for partition, s in later.groupby("partition"):
            for column in [
                "balance_hold_prediction",
                "io_clock_sensitivity",
                "guarded_ridge",
                "boosted_residual",
            ]:
                metrics.append(
                    {
                        "horizon_months": int(horizon),
                        "partition": partition,
                        "candidate": column,
                        **score(s, column),
                    }
                )
            y = s.onset_scheduled_upb
            interval_metrics.append(
                {
                    "horizon_months": int(horizon),
                    "partition": partition,
                    "cases": len(s),
                    "coverage": float(((y >= s.lower_90) & (y <= s.upper_90)).mean()),
                    "mean_width_dollars": float((s.upper_90 - s.lower_90).mean()),
                    "width_over_actual": float((s.upper_90 - s.lower_90).sum() / y.sum()),
                    "below_lower": int(y.lt(s.lower_90).sum()),
                    "above_upper": int(y.gt(s.upper_90).sum()),
                }
            )
        all_predictions.append(later)
        for end, last in FOLDS:
            t = g[g.onset_date.dt.year.le(end)]
            v = g[g.onset_date.dt.year.between(end + 1, last)].copy()
            if len(t) < 60 or v.empty:
                continue
            assert_temporal(t, v)
            v["boosted_residual"] = prediction(fit_residual(t), v)
            v["guarded_ridge"] = fit_fold(t, v)
            v.loc[io_guard(v), "guarded_ridge"] = v.loc[io_guard(v), "anchor_upb"]
            v["fold_train_through"] = end
            historical.append(v)
    predictions = pd.concat(all_predictions, ignore_index=True)
    hist = pd.concat(historical, ignore_index=True)
    hist_metrics = []
    for horizon, g in hist.groupby("horizon_months"):
        for column in [
            "balance_hold_prediction",
            "io_clock_sensitivity",
            "guarded_ridge",
            "boosted_residual",
        ]:
            hist_metrics.append(
                {"horizon_months": int(horizon), "candidate": column, **score(g, column)}
            )
    for horizon, g in predictions.groupby("horizon_months"):
        for partition, s in g.groupby("partition"):
            s = s[~io_guard(s)]
            if not s.empty:
                interval_metrics.append(
                    {
                        "horizon_months": int(horizon),
                        "partition": partition,
                        "scope": "non_IO_only",
                        "cases": len(s),
                        "coverage": float(
                            (
                                (s.onset_scheduled_upb >= s.lower_90)
                                & (s.onset_scheduled_upb <= s.upper_90)
                            ).mean()
                        ),
                        "width_over_actual": float(
                            (s.upper_90 - s.lower_90).sum() / s.onset_scheduled_upb.sum()
                        ),
                    }
                )
    report = {
        "status": "advanced_principal_challenger_not_selected",
        "target": "Scheduled principal at first observed SDQ, not participation/CCF/economic EAD",
        "source_sha256": hashlib.sha256(
            (source / "benchmark_cases.parquet").read_bytes()
        ).hexdigest(),
        "source_report_sha256": hashlib.sha256((source / "report.json").read_bytes()).hexdigest(),
        "sklearn_version": sklearn.__version__,
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "parameters": PARAMETERS,
        "features": FEATURES,
        "feature_schedule_fraction": "postIO clock forecast / anchor principal",
        "training": training_counts,
        "later_metrics": metrics,
        "historical_metrics": hist_metrics,
        "interval_metrics": interval_metrics,
        "limits": [
            "Full supported fixed-rate pre-maturity scope only, no extrapolation to fallback/maturity/ARM/modified loans",
            "Point model train<=2018; quantile models train<=2014, temporal calibration2015-18",
            "90percent nominal intervals, temporal nonexchangeability prevents guaranteed coverage",
            "Interval quantile envelope handles crossings; lower bound constrained by nonnegative exposure domain",
            "IO guard holds scheduled principal and interval constant, no actual draw/accrual inference",
            "Historical folds include2019-22, not extra independent observations",
            "Loan disjoint, borrower/MBS dependencies unresolved",
            "Revised source availability unverified, later samples previously examined",
            "No parameter tuning, baseline replacement, PD refit, LGD denominator change or EL integration",
        ],
    }
    output.mkdir(parents=True)
    joblib.dump(models, output / "models.joblib")
    loaded = joblib.load(output / "models.joblib")
    for horizon, g in predictions.groupby("horizon_months"):
        np.testing.assert_allclose(
            prediction(loaded[f"mean_{horizon}"], g), g.boosted_residual, rtol=1e-12, atol=1e-8
        )
        lo, hi, _ = bounds(
            loaded[f"interval_{horizon}"], g, loaded[f"interval_{horizon}"]["radius"]
        )
        np.testing.assert_allclose(lo, g.lower_90, rtol=1e-12, atol=1e-8)
        np.testing.assert_allclose(hi, g.upper_90, rtol=1e-12, atol=1e-8)
    predictions.to_parquet(output / "predictions.parquet", index=False)
    hist.to_parquet(output / "historical_predictions.parquet", index=False)
    report["reload_verified_later_cases"] = len(predictions)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.source, a.output)
