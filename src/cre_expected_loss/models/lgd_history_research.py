"""Signed LGD history experiments; observed SDQ anchor is not approved default."""

import hashlib
import json
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
LIFE = [
    "seasoning_months",
    "months_to_maturity",
    "balance_to_original",
    "note_rate",
    "rate_changed",
    "property_count",
]
LIFE_CATS = ["amortization_type", "interest_type", "lien_position"]
DSCR = ["historical_dscr", "dscr_change", "dscr_vs_underwritten"]
HISTORY = [
    "last_delinquency",
    "max_delinquency_12m",
    "delinquency_share_12m",
    "sdq_months_observed",
    "months_since_first_observed_sdq",
    "history_months",
    "history_gap_months",
]
FOLDS = [(2008, 2011), (2011, 2014), (2014, 2018), (2018, 2022)]


def derive_features(cases, monthly, annual, dscr_lag=2):
    """Use only dated rows <= anchor; annual availability remains an assumption."""
    if dscr_lag not in [1, 2]:
        raise ValueError("DSCR lag must be one or two calendar years")
    if not cases.loan_id.is_unique:
        raise ValueError("Duplicate outcome loan")
    if monthly.duplicated(["loan_id", "reporting_date"]).any():
        raise ValueError("Duplicate monthly loan/date")
    monthly = monthly.copy()
    monthly["reporting_date"] = pd.to_datetime(monthly.reporting_date)
    severity = {
        "Current": 0,
        "30-59 Days Delinquent": 1,
        "60-89 Days Delinquent": 2,
        "90+ Days Delinquent": 3,
    }
    monthly["severity"] = monthly.payment_status.map(severity)
    if monthly.severity.isna().any():
        raise ValueError("Unknown payment status requires review")
    monthly["sdq"] = monthly.severity.ge(2) | monthly.sdq_indicator.eq("Y")
    annual = annual.groupby(["loan_id", "dscr_year"]).annual_dscr.agg(["first", "nunique"])
    annual.loc[annual["nunique"].gt(1), "first"] = np.nan
    histories = {loan: g.sort_values("reporting_date") for loan, g in monthly.groupby("loan_id")}
    rows = []
    for _, case in cases.iterrows():
        history = histories.get(case.loan_id)
        if history is None:
            continue
        before = history[history.reporting_date < case.credit_event_date]
        observed_sdq = before.loc[before.sdq, "reporting_date"]
        first_sdq = observed_sdq.min()
        anchors = {"pre_disposition_update": pd.Timestamp(case.feature_date)}
        if pd.notna(first_sdq):
            prior = before[before.reporting_date < first_sdq]
            if not prior.empty:
                anchors["before_first_observed_sdq"] = prior.reporting_date.max()
        for scope, anchor in anchors.items():
            eligible = before[before.reporting_date <= anchor]
            if eligible.empty:
                continue
            latest = eligible.iloc[-1]
            if case.earliest_reporting_date > anchor:
                continue
            row = case.to_dict()
            row.update(
                scope=scope,
                anchor_date=anchor,
                history_source_date=latest.reporting_date,
                first_observed_sdq=first_sdq,
            )
            row["seasoning_months"] = (anchor - pd.Timestamp(latest.note_date)).days / 30.4375
            row["months_to_maturity"] = (pd.Timestamp(latest.maturity_date) - anchor).days / 30.4375
            row["balance_to_original"] = (
                latest.current_upb / case.original_upb if case.original_upb > 0 else np.nan
            )
            row["note_rate"] = latest.note_rate
            row["rate_change"] = latest.note_rate - latest.original_interest_rate
            # A continuous near-constant rate change destabilized the diagnostic
            # first run. Preserve it externally; fit a precision-aware indicator.
            row["rate_changed"] = (
                float(abs(row["rate_change"]) >= 0.01) if pd.notna(row["rate_change"]) else np.nan
            )
            for field in ["amortization_type", "interest_type"]:
                row[field] = latest[field]
            reference_year = anchor.year - dscr_lag

            def dscr(year, loan=case.loan_id):
                key = (loan, year)
                return annual.loc[key, "first"] if key in annual.index else np.nan

            row["dscr_reference_year"] = reference_year
            row["historical_dscr"] = dscr(reference_year)
            row["dscr_change"] = dscr(reference_year) - dscr(reference_year - 1)
            row["dscr_vs_underwritten"] = dscr(reference_year) - case.underwritten_dscr
            recent = eligible[eligible.reporting_date > anchor - pd.DateOffset(months=12)]
            row["last_delinquency"] = latest.severity
            row["max_delinquency_12m"] = recent.severity.max()
            row["delinquency_share_12m"] = recent.severity.gt(0).mean()
            row["sdq_months_observed"] = int(eligible.sdq.sum())
            seen = eligible.loc[eligible.sdq, "reporting_date"].min()
            row["months_since_first_observed_sdq"] = (
                (anchor - seen).days / 30.4375 if pd.notna(seen) else 0.0
            )
            row["history_months"] = len(eligible)
            row["history_gap_months"] = (anchor - latest.reporting_date).days / 30.4375
            rows.append(row)
    result = pd.DataFrame(rows)
    if (result.history_source_date > result.anchor_date).any() or (
        result.anchor_date >= result.credit_event_date
    ).any():
        raise ValueError("Invalid history alignment")
    for col in CATS + LIFE_CATS:
        result[col] = result[col].fillna("").replace("", "Unknown")
    for col in LIFE + DSCR + HISTORY:
        result[col] = pd.to_numeric(result[col], errors="coerce")
        result[col + "_missing"] = result[col].isna().astype(float)
    return result


def fit_history(frame, nums, cats, hurdle=False):
    y = frame.signed_ratio.to_numpy(float)
    if len(y) < 10 or not np.isfinite(y).all() or np.isinf(frame[nums].to_numpy(float)).any():
        raise ValueError("Invalid training frame")

    def prep():
        return ColumnTransformer(
            [
                (
                    "numeric",
                    make_pipeline(
                        SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler()
                    ),
                    nums,
                ),
                ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cats),
            ]
        )

    if not hurdle:
        return make_pipeline(prep(), Ridge(alpha=10.0)).fit(frame, y)
    pos, neg, nz = y > 0, y < 0, y != 0
    if min(pos.sum(), neg.sum()) < 3:
        raise ValueError("Sparse training signs")
    sign = make_pipeline(prep(), LogisticRegression(C=0.1, max_iter=2000, random_state=20260901))
    sign.fit(frame.loc[nz], pos[nz].astype(int))

    def magnitude(mask):
        return make_pipeline(
            prep(), TweedieRegressor(power=2, alpha=10.0, link="log", max_iter=2000, tol=1e-8)
        ).fit(frame.loc[mask], abs(y[mask]))

    return SignedHurdle(
        float((y == 0).mean()),
        sign,
        magnitude(pos),
        magnitude(neg),
        {"positive": int(pos.sum()), "negative": int(neg.sum()), "zero": int((y == 0).sum())},
    )


def run(fannie_root: Path, output: Path):
    import platform

    import duckdb
    import joblib
    import sklearn

    if output.exists():
        raise FileExistsError(output)
    artifacts = fannie_root / "artifacts/2026Q1"
    source = artifacts / "lgd-signed-research-v0.1.0/signed_outcomes.parquet"
    static_source = artifacts / "lgd-gain-allocation-audit-v0.1.0/allocation_case_audit.parquet"
    cases = pd.read_parquet(source)
    static = pd.read_parquet(static_source)[
        ["loan_id", "original_upb", "property_count", "lien_position"]
    ]
    cases = cases.merge(static, on="loan_id", validate="one_to_one")
    monthly_path = fannie_root / "processed/2026Q1/v0.3.0/fannie_monthly.parquet"
    annual_path = monthly_path.parent / "fannie_annual_dscr.parquet"
    c = duckdb.connect()
    c.register("cases", cases[["loan_id", "credit_event_date"]])
    monthly = c.execute(
        "SELECT m.* FROM read_parquet(?) m JOIN cases t USING(loan_id) WHERE m.reporting_date < t.credit_event_date",
        [str(monthly_path)],
    ).fetchdf()
    annual = c.execute(
        "SELECT a.* FROM read_parquet(?) a JOIN cases t USING(loan_id)", [str(annual_path)]
    ).fetchdf()
    c.close()
    feature_sets = {
        "baseline": ([], []),
        "lifecycle": (LIFE, LIFE_CATS),
        "dscr": (DSCR, []),
        "delinquency": (HISTORY, []),
        "all_history": (LIFE + DSCR + HISTORY, LIFE_CATS),
    }
    features, predictions, detail, coefficients, models, folds, coverage = (
        [],
        [],
        [],
        [],
        {},
        [],
        [],
    )
    for dscr_lag in [2, 1]:
        frame = derive_features(cases, monthly, annual, dscr_lag)
        frame["dscr_lag"] = dscr_lag
        features.append(frame)
        for scope, f in frame.groupby("scope"):
            coverage.append(
                {
                    "scope": scope,
                    "dscr_lag": dscr_lag,
                    "cases": len(f),
                    "counts": {str(k): int(v) for k, v in f.groupby("period").size().items()},
                    "missing_counts": {k: int(f[k].isna().sum()) for k in LIFE + DSCR + HISTORY},
                    "observed_sdq_before_anchor": int(f.sdq_months_observed.gt(0).sum()),
                    "median_anchor_to_event_months": float(
                        ((f.credit_event_date - f.anchor_date).dt.days / 30.4375).median()
                    ),
                }
            )
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
                ("later", period, f[f.credit_event_year <= 2018], g)
                for period, g in f[f.credit_event_year > 2018].groupby("period")
            ]
            for partition, period, train, test in partitions:
                overlap = (
                    train.group.isin(test.group)
                    if partition == "rolling"
                    else pd.Series(False, index=train.index)
                )
                train = train[~overlap]
                folds.append(
                    {
                        "scope": scope,
                        "dscr_lag": dscr_lag,
                        "partition": partition,
                        "period": period,
                        "training": len(train),
                        "evaluation": len(test),
                        "purged": int(overlap.sum()),
                    }
                )
                if (
                    test.empty
                    or min(train.signed_ratio.gt(0).sum(), train.signed_ratio.lt(0).sum()) < 3
                ):
                    raise ValueError("Insufficient history fold")
                for name, (extra, extra_cats) in feature_sets.items():
                    if dscr_lag == 1 and name not in ["baseline", "dscr", "all_history"]:
                        continue
                    nums = CORE + extra + [k + "_missing" for k in extra]
                    cats = CATS + extra_cats
                    for hurdle in [False, True]:
                        candidate = ("hurdle_" if hurdle else "ridge_") + name
                        model = fit_history(train, nums, cats, hurdle)
                        if hurdle:
                            component = predict_hurdle(model, test)
                            pred = component.prediction.to_numpy()
                            detail.append(
                                {
                                    "scope": scope,
                                    "dscr_lag": dscr_lag,
                                    "partition": partition,
                                    "period": period,
                                    "candidate": candidate,
                                    "diagnostics": diagnostic(test, component),
                                }
                            )
                        else:
                            pred = model.predict(test)
                        if not np.isfinite(pred).all():
                            raise ValueError("Nonfinite history predictions")
                        predictions.append(
                            pd.DataFrame(
                                {
                                    "loan_id": test.loan_id,
                                    "group": test.group,
                                    "scope": scope,
                                    "dscr_lag": dscr_lag,
                                    "partition": partition,
                                    "period": period,
                                    "candidate": candidate,
                                    "actual": test.signed_ratio,
                                    "prediction": pred,
                                }
                            )
                        )
                        if partition == "later":
                            models[f"{scope}_{dscr_lag}_{candidate}"] = (
                                vars(model) if hurdle else model
                            )
                            if not hurdle and period == "validation":
                                for feature, value in zip(
                                    model[0].get_feature_names_out(), model[-1].coef_
                                ):
                                    coefficients.append(
                                        {
                                            "scope": scope,
                                            "dscr_lag": dscr_lag,
                                            "candidate": candidate,
                                            "feature": feature,
                                            "coefficient": float(value),
                                        }
                                    )
                predictions.append(
                    pd.DataFrame(
                        {
                            "loan_id": test.loan_id,
                            "group": test.group,
                            "scope": scope,
                            "dscr_lag": dscr_lag,
                            "partition": partition,
                            "period": period,
                            "candidate": "mean_benchmark",
                            "actual": test.signed_ratio,
                            "prediction": train.signed_ratio.mean(),
                        }
                    )
                )
    predictions = pd.concat(predictions, ignore_index=True)

    def metric(g):
        return {
            "cases": len(g),
            "mae": float(abs(g.prediction - g.actual).mean()),
            "rmse": float(np.sqrt(((g.prediction - g.actual) ** 2).mean())),
            "mean_prediction": float(g.prediction.mean()),
            "mean_actual": float(g.actual.mean()),
        }

    scores = []
    for (scope, lag, partition, candidate), g in predictions.groupby(
        ["scope", "dscr_lag", "partition", "candidate"]
    ):
        base = {"scope": scope, "dscr_lag": int(lag), "candidate": candidate}
        if partition == "rolling":
            scores.append({**base, "partition": "pooled_rolling", **metric(g)})
            for period, group in g.groupby("period"):
                scores.append({**base, "partition": "fold_" + period, **metric(group)})
        else:
            for period, group in g.groupby("period"):
                scores.append({**base, "partition": period, **metric(group)})
    bootstrap = []
    rolling = predictions[predictions.partition.eq("rolling")]
    for (scope, lag, candidate), g in rolling.groupby(["scope", "dscr_lag", "candidate"]):
        if candidate.endswith("baseline") or candidate == "mean_benchmark":
            continue
        reference = rolling[
            (rolling.scope == scope)
            & (rolling.dscr_lag == lag)
            & (rolling.candidate == candidate.split("_")[0] + "_baseline")
        ]
        paired = g.merge(
            reference, on=["loan_id", "period"], suffixes=("", "_ref"), validate="one_to_one"
        )
        if len(paired) != len(g):
            raise ValueError("Baseline population mismatch")
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
                "scope": scope,
                "dscr_lag": int(lag),
                "candidate": candidate,
                "mae_difference": float(paired.difference.mean()),
                "conditional_95_interval": np.quantile(draws, [0.025, 0.975]).tolist(),
            }
        )
    report = {
        "status": "history_research_not_selected",
        "target": "signed-source-ratio-v0.1.0",
        "coverage": coverage,
        "fold_counts": folds,
        "metrics": scores,
        "paired_bootstrap": bootstrap,
        "component_diagnostics": detail,
        "feature_sets": {
            k: {"numeric": v[0], "categorical": v[1]} for k, v in feature_sets.items()
        },
        "annual_conflicting_keys": int(
            annual.groupby(["loan_id", "dscr_year"]).annual_dscr.nunique().gt(1).sum()
        ),
        "rate_change_rule": "abs(note_rate-original_interest_rate)>=0.01 percentage point; continuous difference diagnostic only",
        "supersedes": "lgd-history-research-v0.1.0 diagnostic continuous-rate-change instability; retain its artifacts",
        "hashes": {
            str(p.name): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [source, static_source, monthly_path, annual_path]
        },
        "runtime": {"python": platform.python_version(), "sklearn": sklearn.__version__},
        "limitations": [
            "First observed 60+ delinquency/SDQ is an evidence anchor, not approved default onset.",
            "Pre-disposition features may be during workout; not default-time forecasting.",
            "Before-first-observed-SDQ is restricted to loans with earlier monthly history; no eligibility change to baseline.",
            "Annual DSCR publication dates unavailable: two-calendar-year lag primary; one-year lag sensitivity only.",
            "Revised snapshot, unknown loss finalization and event-year splits do not establish operational point-in-time tests.",
            "No independent OOT selection; multiple exploratory comparisons; fixed-error group bootstrap excludes fitting uncertainty.",
            "No post-event valuations, sale proceeds, disposition categories or future ever-delinquent flags used.",
            "Unknown borrower groups and incomplete collateral stack; national macro not included in these feature-block experiments.",
            "Median imputation within each training component; all-missing numeric features imputed zero with explicit missing flags.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="history-stage-", dir=output.parent) as tmp:
        stage = Path(tmp) / "output"
        stage.mkdir()
        pd.concat(features, ignore_index=True).to_parquet(stage / "features.parquet", index=False)
        predictions.to_parquet(stage / "predictions.parquet", index=False)
        pd.DataFrame(coefficients).to_csv(stage / "ridge_coefficients.csv", index=False)
        joblib.dump(models, stage / "models.joblib")
        (stage / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        stage.rename(output)
    print(
        json.dumps(
            {
                "coverage": coverage,
                "pooled_metrics": [s for s in scores if s["partition"] == "pooled_rolling"],
            },
            indent=2,
        )
    )
    return report


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--fannie-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    run(args.fannie_root, args.output)
