"""Signed hurdle research: zero mass, conditional sign, and Gamma magnitudes."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import tempfile
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression, TweedieRegressor
from sklearn.metrics import roc_auc_score, log_loss

NUMERIC = ["acquisition_ltv", "underwritten_dscr", "log_acquisition_upb"]
CATEGORICAL = ["property_type", "loss_sharing_type"]


@dataclass
class SignedHurdle:
    zero_probability: float
    sign_model: object
    positive_model: object
    negative_model: object
    training_counts: dict


def preprocessing():
    return ColumnTransformer(
        [
            ("numeric", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUMERIC),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
        ]
    )


def validate_features(frame):
    if np.isinf(frame[NUMERIC].to_numpy(float)).any():
        raise ValueError("Infinite numeric features")
    if frame[CATEGORICAL].isna().any().any():
        raise ValueError("Categorical missing values must be explicitly standardized")


def fit_hurdle(frame: pd.DataFrame) -> SignedHurdle:
    validate_features(frame)
    y = frame.signed_ratio.to_numpy(float)
    if len(y) < 10 or not np.isfinite(y).all():
        raise ValueError("Need ten finite signed outcomes")
    pos, neg, nonzero = y > 0, y < 0, y != 0
    if pos.sum() < 3 or neg.sum() < 3:
        raise ValueError("Need at least three positive and three negative training cases")
    if frame[NUMERIC].isna().all().any():
        raise ValueError("Entirely missing training numeric feature")
    for mask in (pos, neg):
        if frame.loc[mask, NUMERIC].isna().all().any():
            raise ValueError("Entirely missing numeric feature in a severity component")
    sign = make_pipeline(
        preprocessing(), LogisticRegression(C=0.1, max_iter=2000, random_state=20260901)
    )
    sign.fit(frame.loc[nonzero], pos[nonzero].astype(int))

    def magnitude(mask):
        model = make_pipeline(
            preprocessing(),
            TweedieRegressor(power=2, alpha=10.0, link="log", max_iter=2000, tol=1e-8),
        )
        model.fit(frame.loc[mask], np.abs(y[mask]))
        return model

    return SignedHurdle(
        float((y == 0).mean()),
        sign,
        magnitude(pos),
        magnitude(neg),
        {"positive": int(pos.sum()), "negative": int(neg.sum()), "zero": int((y == 0).sum())},
    )


def predict_hurdle(model: SignedHurdle, frame: pd.DataFrame) -> pd.DataFrame:
    validate_features(frame)
    conditional_positive = model.sign_model.predict_proba(frame)[:, 1]
    positive = (1 - model.zero_probability) * conditional_positive
    negative = (1 - model.zero_probability) * (1 - conditional_positive)
    positive_mean = model.positive_model.predict(frame)
    negative_mean = model.negative_model.predict(frame)
    result = pd.DataFrame(
        {
            "p_zero": model.zero_probability,
            "p_positive": positive,
            "p_negative": negative,
            "conditional_positive_probability": conditional_positive,
            "positive_magnitude": positive_mean,
            "negative_magnitude": negative_mean,
            "prediction": positive * positive_mean - negative * negative_mean,
        },
        index=frame.index,
    )
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError("Nonfinite hurdle output")
    np.testing.assert_allclose(
        result[["p_zero", "p_positive", "p_negative"]].sum(axis=1), 1.0, atol=1e-12
    )
    if (result[["p_zero", "p_positive", "p_negative"]] < 0).any().any():
        raise ValueError("Invalid probability")
    if (result[["positive_magnitude", "negative_magnitude"]] <= 0).any().any():
        raise ValueError("Invalid magnitudes")
    return result


def diagnostic(frame, predictions):
    y = frame.signed_ratio.to_numpy()
    p = predictions.prediction.to_numpy()
    result = {
        "cases": len(y),
        "mae": float(np.abs(p - y).mean()),
        "rmse": float(np.sqrt(((p - y) ** 2).mean())),
        "mean_actual": float(y.mean()),
        "mean_prediction": float(p.mean()),
        "exposure_weighted_actual": float(np.average(y, weights=frame.parsed_default)),
        "exposure_weighted_prediction": float(np.average(p, weights=frame.parsed_default)),
    }
    nonzero = y != 0
    observed = (y[nonzero] > 0).astype(int)
    prob = predictions.conditional_positive_probability.to_numpy()[nonzero]
    result["conditional_sign"] = {
        "cases": int(nonzero.sum()),
        "observed_positive_rate": float(observed.mean()),
        "mean_positive_probability": float(prob.mean()),
        "brier": float(((prob - observed) ** 2).mean()),
        "log_loss": float(log_loss(observed, prob, labels=[0, 1])),
        "roc_auc": float(roc_auc_score(observed, prob)) if len(np.unique(observed)) == 2 else None,
    }
    # Reliability bins and logistic intercept/slope are diagnostics, never applied as recalibration.
    bins = pd.DataFrame({"actual": observed, "probability": prob})
    bins["bin"] = pd.qcut(bins.probability, q=min(4, len(bins)), duplicates="drop")
    result["conditional_sign"]["reliability_bins"] = [
        {
            "cases": len(g),
            "predicted": float(g.probability.mean()),
            "observed": float(g.actual.mean()),
        }
        for _, g in bins.groupby("bin", observed=True)
    ]
    try:
        import statsmodels.api as sm
        import warnings
        from statsmodels.tools.sm_exceptions import PerfectSeparationWarning

        logits = np.log(np.clip(prob, 1e-10, 1 - 1e-10) / (1 - np.clip(prob, 1e-10, 1 - 1e-10)))
        with warnings.catch_warnings():
            warnings.simplefilter("error", PerfectSeparationWarning)
            fit = sm.GLM(observed, sm.add_constant(logits), family=sm.families.Binomial()).fit()
        result["conditional_sign"]["calibration_intercept"] = float(fit.params[0])
        result["conditional_sign"]["calibration_slope"] = float(fit.params[1])
    except (ValueError, IndexError, np.linalg.LinAlgError, Warning):
        result["conditional_sign"]["calibration_intercept"] = None
        result["conditional_sign"]["calibration_slope"] = None
        result["conditional_sign"]["calibration_note"] = "Not estimable reliably in this sample"
    for label, mask, column in [
        ("positive", y > 0, "positive_magnitude"),
        ("negative", y < 0, "negative_magnitude"),
    ]:
        actual = np.abs(y[mask])
        pred = predictions[column].to_numpy()[mask]
        result[label + "_severity"] = {
            "cases": len(actual),
            "mean_actual": float(actual.mean()) if len(actual) else None,
            "mean_prediction": float(pred.mean()) if len(actual) else None,
            "mae": float(np.abs(actual - pred).mean()) if len(actual) else None,
            "rmse": float(np.sqrt(((actual - pred) ** 2).mean())) if len(actual) else None,
        }
    result["zero_probability"] = {
        "observed_rate": float((y == 0).mean()),
        "mean_prediction": float(predictions.p_zero.mean()),
    }
    matrix = predictions[["p_negative", "p_zero", "p_positive"]].to_numpy()
    cls = np.where(y < 0, 0, np.where(y == 0, 1, 2))
    actual = np.eye(3)[cls]
    result["three_class_brier_sum"] = float(((matrix - actual) ** 2).sum(axis=1).mean())
    result["three_class_log_loss"] = float(
        -np.log(np.clip(matrix[np.arange(len(y)), cls], 1e-15, 1)).mean()
    )
    return result


def run(artifact_root: Path):
    import joblib, platform, sklearn

    base = artifact_root / "lgd-signed-research-v0.1.0"
    output = artifact_root / "lgd-signed-hurdle-v0.1.1"
    if output.exists():
        raise FileExistsError(output)
    frame = pd.read_parquet(base / "signed_outcomes.parquet")
    frozen_rolling = pd.read_parquet(base / "rolling_predictions.parquet")
    frozen_later = pd.read_parquet(base / "later_predictions.parquet")
    if not frame.loan_id.is_unique:
        raise ValueError("Duplicate loans")
    folds = []
    rolling = []
    for end, next_end in [(2008, 2011), (2011, 2014), (2014, 2018), (2018, 2022)]:
        train = frame[frame.credit_event_year <= end]
        test = frame[(frame.credit_event_year > end) & (frame.credit_event_year <= next_end)]
        overlap = train.group.isin(test.group)
        train = train[~overlap]
        model = fit_hurdle(train)
        prediction = predict_hurdle(model, test)
        prediction = prediction.assign(
            loan_id=test.loan_id, group=test.group, fold=end, actual=test.signed_ratio
        )
        folds.append(
            {
                "train_end": end,
                "evaluation_end": next_end,
                "training_counts": model.training_counts,
                "purged_mbs_overlap": int(overlap.sum()),
                "diagnostics": diagnostic(test, prediction),
            }
        )
        rolling.append(prediction)
    rolling = pd.concat(rolling, ignore_index=True)
    training = frame[frame.period.eq("training")]
    model = fit_hurdle(training)
    later = []
    periods = {}
    for period, test in frame[~frame.period.eq("training")].groupby("period"):
        p = predict_hurdle(model, test)
        periods[period] = diagnostic(test, p)
        later.append(
            p.assign(
                loan_id=test.loan_id, group=test.group, period=period, actual=test.signed_ratio
            )
        )
    later = pd.concat(later, ignore_index=True)

    def benchmark_metrics(predictions):
        return {
            name: {
                "cases": len(g),
                "mae": float(np.abs(g.prediction - g.actual).mean()),
                "rmse": float(np.sqrt(((g.prediction - g.actual) ** 2).mean())),
            }
            for name, g in predictions.groupby("candidate")
        }

    pooled = benchmark_metrics(frozen_rolling)
    pooled["signed_hurdle"] = {
        "cases": len(rolling),
        "mae": float(np.abs(rolling.prediction - rolling.actual).mean()),
        "rmse": float(np.sqrt(((rolling.prediction - rolling.actual) ** 2).mean())),
    }
    comparisons = {}
    rng = np.random.default_rng(20260901)
    for name in ["mean_benchmark", "ridge_loss_sharing"]:
        reference = frozen_rolling[frozen_rolling.candidate.eq(name)][
            ["loan_id", "fold", "prediction", "actual"]
        ]
        joined = rolling.merge(
            reference, on=["loan_id", "fold"], suffixes=("", "_reference"), validate="one_to_one"
        )
        if len(joined) != len(rolling):
            raise ValueError("Benchmark sample mismatch")
        np.testing.assert_allclose(joined.actual, joined.actual_reference)
        joined["difference"] = np.abs(joined.prediction - joined.actual) - np.abs(
            joined.prediction_reference - joined.actual
        )
        groups = joined.groupby("group").agg(
            total=("difference", "sum"), cases=("difference", "size")
        )
        idx = rng.integers(0, len(groups), size=(2000, len(groups)))
        draws = groups.total.to_numpy()[idx].sum(axis=1) / groups.cases.to_numpy()[idx].sum(axis=1)
        comparisons[name] = {
            "mae_difference": float(joined.difference.mean()),
            "95_interval": np.quantile(draws, [0.025, 0.975]).tolist(),
        }
    fixed = {period: benchmark_metrics(g) for period, g in frozen_later.groupby("period")}
    pooled_frame = frame.set_index("loan_id").loc[rolling.loan_id].reset_index()
    pooled_diagnostics = diagnostic(pooled_frame, rolling)
    report = {
        "status": "research_challenger_not_selected",
        "target": "unchanged signed-source-ratio-v0.1.0",
        "formula": "(1-p_zero)*(p_positive_given_nonzero*positive_magnitude-(1-p_positive_given_nonzero)*negative_magnitude)",
        "features": NUMERIC + CATEGORICAL,
        "logistic_C": 0.1,
        "gamma_alpha": 10.0,
        "zero_probability": model.zero_probability,
        "training_counts": model.training_counts,
        "folds": folds,
        "period_diagnostics": periods,
        "pooled_hurdle_diagnostics": pooled_diagnostics,
        "pooled_comparison": pooled,
        "fixed_benchmarks": fixed,
        "paired_bootstrap": comparisons,
        "source_sha256": hashlib.sha256(
            (base / "signed_outcomes.parquet").read_bytes()
        ).hexdigest(),
        "runtime": {"python": platform.python_version(), "sklearn": sklearn.__version__},
        "limitations": [
            "Zero probability constant; no later zero cases to assess it.",
            "72 negative training cases and rare property categories; fixed regularization, no tuning.",
            "Gamma magnitudes strictly positive and unbounded; signed expectation can have either sign.",
            "MBS transaction grouping is not verified borrower grouping.",
            "Bootstrap is conditional on fixed predictions and excludes estimation uncertainty.",
            "Calibration diagnostics are descriptive, especially in eleven OOT cases.",
            "Revised source labels, unknown finalization dates, selection from missing denominators remain.",
            "OOT examined during development; no independent validation or selection evidence.",
        ],
    }
    with tempfile.TemporaryDirectory(prefix="hurdle-stage-", dir=artifact_root) as temporary:
        stage = Path(temporary) / "output"
        stage.mkdir()
        rolling.to_parquet(stage / "rolling_predictions.parquet", index=False)
        later.to_parquet(stage / "later_predictions.parquet", index=False)
        # Persist a plain component dictionary so module execution does not
        # bind the dataclass to __main__ during serialization.
        joblib.dump(vars(model), stage / "model.joblib")
        (stage / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        stage.rename(output)
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "training_counts",
                    "zero_probability",
                    "period_diagnostics",
                    "pooled_comparison",
                    "paired_bootstrap",
                ]
            },
            indent=2,
        )
    )
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    run(parser.parse_args().artifact_root)
