"""Reproducible aggregate diagnostics; retain loan-level data outside Git."""

from pathlib import Path
import json
import platform
import hashlib
import numpy as np
import pandas as pd
import sklearn
import joblib
from cre_expected_loss.models.lgd_research import fit_two_part, predict_two_part

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--artifact-root", type=Path, required=True)
ROOT = parser.parse_args().artifact_root
FIT = ROOT / "lgd-research-v0.1.0"
OUT = ROOT / "lgd-research-diagnostics-v0.1.0"
if OUT.exists():
    raise FileExistsError(OUT)
frame = pd.read_parquet(FIT / "predictions.parquet")
assert frame.loan_id.is_unique and len(frame) == 584
assert (frame.feature_date < frame.credit_event_date).all()
np.testing.assert_allclose(
    frame.two_part_prediction, frame.positive_loss_probability * frame.conditional_severity
)
train = frame.loc[frame["sample"].eq("train")]
np.testing.assert_allclose(frame.mean_benchmark_prediction, train.reported_loss_ratio.mean())
models = joblib.load(FIT / "model.joblib")["models"]
np.testing.assert_allclose(predict_two_part(models, frame)[2], frame.two_part_prediction)
rng = np.random.default_rng(20260901)


def metrics(g):
    y = g.reported_loss_ratio.to_numpy()
    result = {
        "loans": len(g),
        "zeros": int((y == 0).sum()),
        "above_one": int((y > 1).sum()),
        "mean_actual": float(y.mean()),
    }
    for col in ["mean_benchmark_prediction", "two_part_prediction"]:
        p = g[col].to_numpy()
        result[col] = {
            "mean": float(p.mean()),
            "mae": float(np.abs(p - y).mean()),
            "rmse": float(np.sqrt(np.mean((p - y) ** 2))),
            "exposure_weighted_actual": float(np.average(y, weights=g.default_amount)),
            "exposure_weighted_prediction": float(np.average(p, weights=g.default_amount)),
        }
    return result


bootstrap = {}
for sample, g in frame.groupby("sample"):
    y = g.reported_loss_ratio.to_numpy()
    p = g.two_part_prediction.to_numpy()
    b = g.mean_benchmark_prediction.to_numpy()
    idx = rng.integers(0, len(g), size=(5000, len(g)))
    samples = {
        "mean_actual": y[idx].mean(axis=1),
        "mae_difference_candidate_minus_benchmark": (np.abs(p - y)[idx] - np.abs(b - y)[idx]).mean(
            axis=1
        ),
        "mean_prediction_minus_actual": (p - y)[idx].mean(axis=1),
    }
    bootstrap[sample] = {
        k: [float(v) for v in np.quantile(values, [0.025, 0.975])] for k, values in samples.items()
    }

sensitivities = {}
# Hold the fitted severity fixed and remove occurrence feature effects.
fixed_prob = float((train.reported_loss_ratio > 0).mean())
for sample, g in frame.groupby("sample"):
    pred = fixed_prob * g.conditional_severity.to_numpy()
    sensitivities[sample] = {
        "constant_occurrence_probability": fixed_prob,
        "mean_prediction": float(pred.mean()),
        "mae": float(np.abs(pred - g.reported_loss_ratio).mean()),
    }
# A diagnostic refit excludes training ratios above one; raw labels remain untouched.
tail_models = fit_two_part(train.loc[train.reported_loss_ratio <= 1])
tail_sensitivity = {}
for sample, g in frame.groupby("sample"):
    pred = predict_two_part(tail_models, g)[2]
    tail_sensitivity[sample] = {
        "mean_prediction": float(pred.mean()),
        "mae_on_all_original_cases": float(np.abs(pred - g.reported_loss_ratio).mean()),
    }

report = {
    "status": "research_diagnostics_not_model_selection",
    "seed": 20260901,
    "bootstrap_replicates": 5000,
    "bootstrap_scope": "Paired within-period loan resampling with fixed fitted predictions; excludes parameter uncertainty and temporal dependence. Six-case intervals are especially weak.",
    "runtime": {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "sklearn": sklearn.__version__,
    },
    "prediction_file_sha256": hashlib.sha256(
        (FIT / "predictions.parquet").read_bytes()
    ).hexdigest(),
    "reconciliations": {
        "unique_loans": True,
        "pre_disposition_features": True,
        "prediction_recombination": True,
        "training_mean_benchmark": True,
        "saved_model_prediction_reproduction": True,
    },
    "periods": {str(k): metrics(g) for k, g in frame.groupby("sample")},
    "bootstrap_95_percent_intervals": bootstrap,
    "constant_occurrence_sensitivity": sensitivities,
    "training_tail_exclusion_sensitivity": {
        "excluded_training_cases": int((train.reported_loss_ratio > 1).sum()),
        "periods": tail_sensitivity,
    },
    "segments": {
        field: {str(k): metrics(g) for k, g in frame.groupby(field, dropna=False)}
        for field in ["property_type", "property_state"]
    },
    "segment_limitation": "Pooled segment diagnostics are predominantly in-sample; not independent stability evidence.",
    "feature_missingness_by_period": {
        str(k): {c: int(g[c].isna().sum()) for c in ["acquisition_ltv", "underwritten_dscr"]}
        for k, g in frame.groupby("sample")
    },
}
annual = (
    frame.assign(year=frame.credit_event_date.dt.year)
    .groupby(["year", "sample"])
    .agg(
        loans=("loan_id", "size"),
        zero_losses=("reported_loss_ratio", lambda x: int((x == 0).sum())),
        mean_actual=("reported_loss_ratio", "mean"),
        mean_candidate=("two_part_prediction", "mean"),
    )
    .reset_index()
)
OUT.mkdir()
annual.to_csv(OUT / "annual_diagnostics.csv", index=False)
(OUT / "diagnostics.json").write_text(
    json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
)
print(
    json.dumps(
        {
            k: report[k]
            for k in [
                "reconciliations",
                "bootstrap_95_percent_intervals",
                "constant_occurrence_sensitivity",
                "training_tail_exclusion_sensitivity",
                "feature_missingness_by_period",
            ]
        },
        indent=2,
    )
)
