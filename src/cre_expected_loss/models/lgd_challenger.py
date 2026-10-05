"""Small classical research challengers; target and old fit remain unchanged."""

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import TweedieRegressor
from cre_expected_loss.models.lgd_research import fit_two_part, predict_two_part

NUMERIC = ["acquisition_ltv", "underwritten_dscr", "log_acquisition_upb"]


def fit_constant_occurrence(frame, enriched=False):
    y = frame.reported_loss_ratio.to_numpy(float)
    if len(y) < 10 or not np.isfinite(y).all() or (y < 0).any() or not (y > 0).any():
        raise ValueError("Need ten valid outcomes and positive severity cases")
    nums = NUMERIC if enriched else NUMERIC[:2]
    if np.isinf(frame[nums].to_numpy(float)).any() or frame[nums].isna().all().any():
        raise ValueError("Invalid or entirely missing numeric feature")
    transforms = [
        ("numeric", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), nums)
    ]
    if enriched:
        transforms.append(
            (
                "property",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["property_type"],
            )
        )
    model = make_pipeline(
        ColumnTransformer(transforms),
        TweedieRegressor(power=2, alpha=1.0, link="log", max_iter=2000, tol=1e-8),
    )
    model.fit(frame.loc[y > 0], y[y > 0])
    return float((y > 0).mean()), model


def predict_constant_occurrence(model, frame):
    p = model[0] * model[1].predict(frame)
    if not np.isfinite(p).all() or (p < 0).any():
        raise ValueError("Invalid predictions")
    return p


def evaluate(train, test):
    original = predict_two_part(fit_two_part(train), test)[2]
    predictions = {
        "mean_benchmark": np.full(len(test), train.reported_loss_ratio.mean()),
        "original_two_part": original,
        "constant_occurrence": predict_constant_occurrence(fit_constant_occurrence(train), test),
        "enriched_constant_occurrence": predict_constant_occurrence(
            fit_constant_occurrence(train, True), test
        ),
    }
    y = test.reported_loss_ratio.to_numpy()
    metrics = {
        k: {
            "mae": float(np.abs(p - y).mean()),
            "rmse": float(np.sqrt(((p - y) ** 2).mean())),
            "mean_prediction": float(p.mean()),
            "mean_actual": float(y.mean()),
        }
        for k, p in predictions.items()
    }
    return metrics, predictions


def run(root):
    import joblib, hashlib, sys, sklearn

    out = root / "lgd-challenger-v0.1.0"
    if out.exists():
        raise FileExistsError(out)
    source = root / "lgd-driver-audit-v0.1.0/event_driver_audit.parquet"
    all_cases = pd.read_parquet(source)
    frame = all_cases.loc[all_cases.status.eq("research_eligible")].copy()
    if not frame.loan_id.is_unique:
        raise ValueError("Duplicate loans")
    if (frame.acquisition_upb_values != 1).any() or (frame.acquisition_upb <= 0).any():
        raise ValueError("Acquisition UPB consistency/positivity failure")
    frame["log_acquisition_upb"] = np.log(frame.acquisition_upb)
    # Transaction ID is a source transaction grouping, not established borrower identity.
    frame["group"] = np.where(
        frame.transaction_id.fillna("").str.strip().ne(""), frame.transaction_id, frame.loan_id
    )
    folds = []
    rows = []
    for end, next_end in [(2008, 2011), (2011, 2014), (2014, 2018), (2018, 2022)]:
        tr = frame[frame.credit_event_year <= end]
        te = frame[(frame.credit_event_year > end) & (frame.credit_event_year <= next_end)]
        overlaps = tr.group.isin(te.group)
        clean = tr.loc[~overlaps]
        if len(te) == 0 or len(clean) < 10 or not clean.reported_loss_ratio.eq(0).any():
            folds.append(
                {
                    "train_end": end,
                    "evaluation_end": next_end,
                    "status": "insufficient_after_group_purge",
                }
            )
            continue
        metrics, preds = evaluate(clean, te)
        folds.append(
            {
                "train_end": end,
                "evaluation_end": next_end,
                "train_cases": len(clean),
                "evaluation_cases": len(te),
                "purged_transaction_overlap_cases": int(overlaps.sum()),
                "metrics": metrics,
            }
        )
        for name, p in preds.items():
            rows.append(
                pd.DataFrame(
                    {
                        "loan_id": te.loan_id,
                        "group": te.group,
                        "fold": end,
                        "candidate": name,
                        "actual": te.reported_loss_ratio,
                        "prediction": p,
                    }
                )
            )
    training = frame[frame.credit_event_year <= 2018]
    fixed = {}
    fixed_rows = []
    for label, te in [
        ("validation", frame[(frame.credit_event_year > 2018) & (frame.credit_event_year <= 2022)]),
        ("out_of_time", frame[frame.credit_event_year > 2022]),
    ]:
        metrics, preds = evaluate(training, te)
        fixed[label] = {
            "cases": len(te),
            "training_transaction_overlap": int(training.group.isin(te.group).sum()),
            "metrics": metrics,
        }
        for name, p in preds.items():
            fixed_rows.append(
                pd.DataFrame(
                    {
                        "loan_id": te.loan_id,
                        "period": label,
                        "candidate": name,
                        "actual": te.reported_loss_ratio,
                        "prediction": p,
                    }
                )
            )
    cv = pd.concat(rows, ignore_index=True)
    pooled = {}
    rng = np.random.default_rng(20260901)
    wide = (
        cv.pivot(index=["loan_id", "group", "fold"], columns="candidate", values="prediction")
        .join(cv.drop_duplicates("loan_id").set_index(["loan_id", "group", "fold"]).actual)
        .reset_index()
    )
    groups = wide.group.unique()
    differences = {
        name: np.array(
            [
                (
                    (wide[wide.group == g][name] - wide[wide.group == g].actual).abs()
                    - (wide[wide.group == g].mean_benchmark - wide[wide.group == g].actual).abs()
                ).sum()
                for g in groups
            ]
        )
        for name in ["original_two_part", "constant_occurrence", "enriched_constant_occurrence"]
    }
    sizes = np.array([(wide.group == g).sum() for g in groups])
    idx = rng.integers(0, len(groups), size=(2000, len(groups)))
    for name, g in cv.groupby("candidate"):
        pooled[name] = {
            "cases": len(g),
            "mae": float((g.prediction - g.actual).abs().mean()),
            "rmse": float(np.sqrt(((g.prediction - g.actual) ** 2).mean())),
        }
        if name in differences:
            draws = differences[name][idx].sum(axis=1) / sizes[idx].sum(axis=1)
            pooled[name]["group_bootstrap_mae_difference_95_interval"] = np.quantile(
                draws, [0.025, 0.975]
            ).tolist()
    report = {
        "status": "research_challengers_not_selected",
        "target": "unchanged uncapped source-loss ratio",
        "features_enriched": NUMERIC + ["property_type"],
        "severity_alpha": 1.0,
        "feature_timing": "Acquisition-labelled fields and property type from pre-disposition history; historical publication availability and true pre-default timing remain unverified.",
        "excluded_predictors": [
            "realized_workout_duration",
            "final_event_type",
            "default_amount",
            "modified_loss_sharing_percentage",
            "transaction_id",
        ],
        "folds": folds,
        "pooled_group_purged_backtests": pooled,
        "fixed_2018_fit": fixed,
        "bootstrap": "2000 transaction-group resamples of fixed backtest errors; excludes fitting uncertainty; transaction is not borrower identity.",
        "driver_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "runtime": {"python": sys.version, "sklearn": sklearn.__version__},
        "limitations": [
            "Historical labels are revised; backtests are retrospective.",
            "OOT cases generated hypotheses; OOT cannot independently confirm improvements.",
            "Rare segments and few zero losses.",
            "No macro or default-date drivers added without verified timing.",
        ],
    }
    out.mkdir()
    cv.to_parquet(out / "rolling_predictions.parquet", index=False)
    pd.concat(fixed_rows).to_parquet(out / "later_period_predictions.parquet", index=False)
    joblib.dump(
        {
            "constant": fit_constant_occurrence(training),
            "enriched": fit_constant_occurrence(training, True),
        },
        out / "models.joblib",
    )
    (out / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    run(parser.parse_args().artifact_root)
