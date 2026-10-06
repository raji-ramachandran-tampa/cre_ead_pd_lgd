"""Literature-motivated signed LGD macro challengers; revised-data research only."""

import hashlib
import json
import platform
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge, TweedieRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from cre_expected_loss.models.lgd_signed_hurdle import SignedHurdle, diagnostic, predict_hurdle

CORE = ["acquisition_ltv", "underwritten_dscr", "log_acquisition_upb"]
CATS = ["property_type", "loss_sharing_type"]
FOLDS = [(2008, 2011), (2011, 2014), (2014, 2018), (2018, 2022)]


def macro_panel(input_root: Path, cre_lag_months: int = 6) -> pd.DataFrame:
    """Assumed lags, NOT verified historical publication dates. No forward joins."""

    def read(name):
        f = pd.read_csv(input_root / (name + ".csv"))
        f.columns = ["observation_date", "value"]
        f.observation_date = pd.to_datetime(f.observation_date, errors="raise")
        f.value = pd.to_numeric(f.value, errors="coerce")
        f = f.sort_values("observation_date")
        if f.observation_date.duplicated().any():
            raise ValueError("Duplicate macro observation")
        return f

    cpi = read("CPIAUCSL").set_index("observation_date").asfreq("MS")
    if (cpi.value.dropna() <= 0).any():
        raise ValueError("Nonpositive CPI")
    cpi["cpi_log_change_6m"] = np.log(cpi.value / cpi.value.shift(6))
    cpi["cpi_reference_date"] = cpi.index
    cpi["cpi_assumed_available_date"] = cpi.index + pd.DateOffset(months=2)
    cpi = cpi.reset_index(drop=True).drop(columns="value").dropna()
    cre = read("COMREPUSQ159N").dropna()
    # FRED series is ALREADY year-on-year percent change, not a price index.
    cre["cre_price_yoy"] = cre.value / 100
    cre["cre_reference_date"] = cre.observation_date
    cre["cre_assumed_available_date"] = cre.observation_date + pd.DateOffset(months=cre_lag_months)
    panel = pd.merge_asof(
        cpi.sort_values("cpi_assumed_available_date"),
        cre.sort_values("cre_assumed_available_date"),
        left_on="cpi_assumed_available_date",
        right_on="cre_assumed_available_date",
        direction="backward",
    )
    return panel.drop(columns=["value", "observation_date"])


def attach_macro(frame: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    f = frame.copy()
    if f.feature_date.isna().any() or (f.feature_date > f.credit_event_date).any():
        raise ValueError("Invalid pre-event feature date")
    f["feature_date"] = pd.to_datetime(f.feature_date).astype("datetime64[ns]")
    joined = pd.merge_asof(
        f.sort_values("feature_date"),
        panel.sort_values("cpi_assumed_available_date"),
        left_on="feature_date",
        right_on="cpi_assumed_available_date",
        direction="backward",
    )
    for name in ["cpi", "cre"]:
        available = joined[name + "_assumed_available_date"]
        if (available > joined.feature_date).any():
            raise ValueError("Forward macro join")
    return joined


def fit(frame, extras, hurdle=False):
    nums = CORE + list(extras)
    if frame[nums].isna().any().any() or not np.isfinite(frame[nums]).all().all():
        raise ValueError("Macro comparison requires complete finite numeric inputs")

    def prep():
        return ColumnTransformer(
            [
                (
                    "numeric",
                    make_pipeline(SimpleImputer(strategy="median"), StandardScaler()),
                    nums,
                ),
                ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATS),
            ]
        )

    y = frame.signed_ratio.to_numpy(float)
    if not np.isfinite(y).all() or len(y) < 10:
        raise ValueError("Invalid training outcomes")
    if not hurdle:
        model = make_pipeline(prep(), Ridge(alpha=10.0))
        return model.fit(frame, y)
    pos, neg, nz = y > 0, y < 0, y != 0
    if min(pos.sum(), neg.sum()) < 3:
        raise ValueError("Sparse sign component")
    sign = make_pipeline(prep(), LogisticRegression(C=0.1, max_iter=2000, random_state=20260901))
    sign.fit(frame.loc[nz], pos[nz].astype(int))

    def magnitude(mask):
        model = make_pipeline(
            prep(), TweedieRegressor(power=2, alpha=10.0, link="log", max_iter=2000, tol=1e-8)
        )
        return model.fit(frame.loc[mask], np.abs(y[mask]))

    return SignedHurdle(
        float((y == 0).mean()),
        sign,
        magnitude(pos),
        magnitude(neg),
        {"positive": int(pos.sum()), "negative": int(neg.sum()), "zero": int((y == 0).sum())},
    )


def metrics(f):
    return {
        "cases": len(f),
        "mae": float(abs(f.prediction - f.actual).mean()),
        "rmse": float(np.sqrt(((f.prediction - f.actual) ** 2).mean())),
        "mean_actual": float(f.actual.mean()),
        "mean_prediction": float(f.prediction.mean()),
    }


def run(artifact_root: Path, input_root: Path, output: Path):
    import joblib
    import sklearn

    if output.exists():
        raise FileExistsError(output)
    source = artifact_root / "lgd-signed-research-v0.1.0/signed_outcomes.parquet"
    original = pd.read_parquet(source)
    if not original.loan_id.is_unique:
        raise ValueError("Duplicate loans")
    all_predictions, components, models, coverage, fold_counts = [], [], {}, {}, []
    # lag=0 denotes CPI-only full population; CRE feature not used in that scope.
    for lag in [0, 6, 9]:
        f = attach_macro(original, macro_panel(input_root, lag or 6))
        needed = CORE + ["cpi_log_change_6m"] + (["cre_price_yoy"] if lag else [])
        complete = f[needed].notna().all(axis=1)
        coverage[str(lag)] = {
            "total": len(f),
            "complete": int(complete.sum()),
            "excluded_by_period": {
                k: int(v) for k, v in f.loc[~complete].groupby("period").size().items()
            },
        }
        # Same complete-case population for every candidate in this lag comparison.
        f = f.loc[complete].copy()
        candidates = {
            "baseline": [],
            "cpi": ["cpi_log_change_6m"],
            "cre": ["cre_price_yoy"],
            "cpi_cre": ["cpi_log_change_6m", "cre_price_yoy"],
        }
        if not lag:
            candidates = {k: v for k, v in candidates.items() if k in ["baseline", "cpi"]}
        partitions = [
            (
                "rolling",
                str(end),
                f[f.credit_event_year <= end],
                f[(f.credit_event_year > end) & (f.credit_event_year <= nxt)],
            )
            for end, nxt in FOLDS
        ]
        partitions += [
            ("later", p, f[f.credit_event_year <= 2018], g)
            for p, g in f[f.credit_event_year > 2018].groupby("period")
        ]
        for partition, period, train, test in partitions:
            overlap = (
                train.group.isin(test.group)
                if partition == "rolling"
                else pd.Series(False, index=train.index)
            )
            train = train.loc[~overlap]
            if min(train.signed_ratio.gt(0).sum(), train.signed_ratio.lt(0).sum()) < 3:
                fold_counts.append(
                    {
                        "lag": lag,
                        "partition": partition,
                        "period": period,
                        "status": "not_estimable_all_candidates_skipped_sparse_training_signs",
                        "training": len(train),
                        "evaluation": len(test),
                    }
                )
                continue
            fold_counts.append(
                {
                    "lag": lag,
                    "partition": partition,
                    "period": period,
                    "training": len(train),
                    "evaluation": len(test),
                    "purged": int(overlap.sum()),
                }
            )
            if test.empty:
                raise ValueError("Empty evaluation partition")
            for name, extras in candidates.items():
                for hurdle in [False, True]:
                    candidate = ("hurdle_" if hurdle else "ridge_") + name
                    model = fit(train, extras, hurdle)
                    if hurdle:
                        detail = predict_hurdle(model, test)
                        prediction = detail.prediction.to_numpy()
                        components.append(
                            {
                                "lag": lag,
                                "partition": partition,
                                "period": period,
                                "candidate": candidate,
                                "diagnostics": diagnostic(test, detail),
                            }
                        )
                    else:
                        prediction = model.predict(test)
                    if not np.isfinite(prediction).all():
                        raise ValueError("Nonfinite prediction")
                    all_predictions.append(
                        pd.DataFrame(
                            {
                                "loan_id": test.loan_id,
                                "group": test.group,
                                "lag": lag,
                                "partition": partition,
                                "period": period,
                                "candidate": candidate,
                                "actual": test.signed_ratio,
                                "prediction": prediction,
                            }
                        )
                    )
                    if partition == "later":
                        models[f"{lag}_{candidate}"] = vars(model) if hurdle else model
            all_predictions.append(
                pd.DataFrame(
                    {
                        "loan_id": test.loan_id,
                        "group": test.group,
                        "lag": lag,
                        "partition": partition,
                        "period": period,
                        "candidate": "mean_benchmark",
                        "actual": test.signed_ratio,
                        "prediction": train.signed_ratio.mean(),
                    }
                )
            )
    predictions = pd.concat(all_predictions, ignore_index=True)
    summary = []
    for (lag, partition, candidate), g in predictions.groupby(["lag", "partition", "candidate"]):
        lag = int(lag)
        if partition == "rolling":
            summary.append(
                {"lag": lag, "partition": "pooled_rolling", "candidate": candidate, **metrics(g)}
            )
        else:
            for period, group in g.groupby("period"):
                summary.append(
                    {"lag": lag, "partition": period, "candidate": candidate, **metrics(group)}
                )
    bootstrap = []
    rolling = predictions[predictions.partition.eq("rolling")]
    for (lag, candidate), g in rolling.groupby(["lag", "candidate"]):
        lag = int(lag)
        if candidate.endswith("baseline") or candidate == "mean_benchmark":
            continue
        baseline = candidate.split("_")[0] + "_baseline"
        reference = rolling[(rolling.lag == lag) & (rolling.candidate == baseline)]
        paired = g.merge(
            reference, on=["loan_id", "period", "lag"], suffixes=("", "_ref"), validate="one_to_one"
        )
        if len(paired) != len(g):
            raise ValueError("Paired sample mismatch")
        np.testing.assert_allclose(paired.actual, paired.actual_ref)
        paired["difference"] = abs(paired.prediction - paired.actual) - abs(
            paired.prediction_ref - paired.actual
        )
        groups = paired.groupby("group").difference.agg(["sum", "size"])
        rng = np.random.default_rng(20260901)
        idx = rng.integers(0, len(groups), size=(2000, len(groups)))
        draws = groups["sum"].to_numpy()[idx].sum(axis=1) / groups["size"].to_numpy()[idx].sum(
            axis=1
        )
        bootstrap.append(
            {
                "lag": lag,
                "candidate": candidate,
                "reference": baseline,
                "mae_difference": float(paired.difference.mean()),
                "conditional_95_interval": np.quantile(draws, [0.025, 0.975]).tolist(),
            }
        )
    report = {
        "status": "exploratory_revised_macro_not_selected",
        "target": "signed-source-ratio-v0.1.0",
        "prediction_date": "existing pre-event feature_date; not approved default-onset date",
        "features": {
            "cpi": "six-month log change CPIAUCSL, decimal",
            "cre": "COMREPUSQ159N already YoY change, divided by 100",
        },
        "timing": {
            "cpi_lag_months": 2,
            "cre_lag_months": [6, 9],
            "status": "assumed delays from observation start, not verified release dates",
        },
        "coverage": coverage,
        "fold_counts": fold_counts,
        "metrics": summary,
        "paired_bootstrap": bootstrap,
        "component_diagnostics": components,
        "hyperparameters": {
            "ridge_alpha": 10,
            "logistic_C": 0.1,
            "gamma_alpha": 10,
            "zero": "training constant",
        },
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "macro_manifest": json.loads((input_root / "manifest.json").read_text()),
        "runtime": {"python": platform.python_version(), "sklearn": sklearn.__version__},
        "limitations": [
            "Revised macro values can contain future revisions; NOT point-in-time validation.",
            "National all-CRE price change is a proxy for local multifamily prices.",
            "No observed future recovery-period macros used; assumed lags tested, not verified.",
            "Outcome finalization/borrower grouping unknown; existing OOT already examined.",
            "Bootstrap conditional on fixed predictions; excludes fitting uncertainty.",
            "Many exploratory comparisons; no model selection or EL integration.",
            "Frozen baseline untouched; complete-case baselines refitted for matched comparison.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="macro-stage-", dir=output.parent) as tmp:
        stage = Path(tmp) / "output"
        stage.mkdir()
        predictions.to_parquet(stage / "predictions.parquet", index=False)
        joblib.dump(models, stage / "models.joblib")
        (stage / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        stage.rename(output)
    print(
        json.dumps(
            {"coverage": coverage, "metrics": summary, "paired_bootstrap": bootstrap}, indent=2
        )
    )
    return report


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--artifact-root", type=Path, required=True)
    p.add_argument("--input-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    run(args.artifact_root, args.input_root, args.output)
