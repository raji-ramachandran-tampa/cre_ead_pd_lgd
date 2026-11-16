"""Real-data feasibility and first retail EAD benchmarks; not validated defaults."""

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import PoissonRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .audit import sha256
from .targets import proxy_pairs

FEATURES = [
    "log_anchor_balance",
    "log_anchor_limit",
    "anchor_utilization",
    "balance_change_3m",
    "mean_drawings_3m",
    "mean_payments_3m",
]


def held_out(group):
    """Stable split by application link, independent of outcome/horizon/DPD choice."""
    return int(hashlib.sha256(str(group).encode()).hexdigest()[:16], 16) % 5 == 0


def add_features(pairs, history):
    groups = {k: g.sort_values("month_index") for k, g in history.groupby("account_id")}
    result = []
    for r in pairs.itertuples():
        g = groups[r.account_id]
        anchor_month = r.event_month - r.horizon_months
        anchor = g[g.month_index.eq(anchor_month)]
        if anchor.empty:
            continue
        a = anchor.iloc[0]
        prior = g[g.month_index.between(anchor_month - 2, anchor_month)]
        old = g[g.month_index.eq(anchor_month - 3)]
        b, L = r.anchor_balance, r.anchor_limit
        row = r._asdict()
        row.update(
            {
                "application_link": str(a.application_link),
                "log_anchor_balance": np.log1p(b),
                "log_anchor_limit": np.log1p(L),
                "anchor_utilization": b / L if L > 0 else np.nan,
                "balance_change_3m": (b - float(old.iloc[0].drawn_balance)) / L
                if L > 0 and not old.empty
                else np.nan,
                "mean_drawings_3m": float(prior.drawings.mean()) / L
                if L > 0 and len(prior) == 3
                else np.nan,
                "mean_payments_3m": float(prior.payments.mean()) / L
                if L > 0 and len(prior) == 3
                else np.nan,
            }
        )
        row["split"] = "held_out_group" if held_out(a.application_link) else "training_group"
        result.append(row)
    return pd.DataFrame(result).drop(columns="Index", errors="ignore")


def fit_direct(train):
    """Predict nonnegative EAD/anchor-limit, not CCF; transform back to source units."""
    y = train.event_balance / train.anchor_limit
    if not np.isfinite(y).all() or y.lt(0).any() or y.sum() <= 0:
        raise ValueError("Nonnegative, not-all-zero EAD ratio required")
    model = make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
        StandardScaler(),
        PoissonRegressor(alpha=1.0, max_iter=1000, tol=1e-8),
    )
    model.fit(train[FEATURES], y)
    return model


def predict_direct(model, frame):
    values = model.predict(frame[FEATURES]) * frame.anchor_limit
    if not np.isfinite(values).all() or values.lt(0).any():
        raise ValueError("Invalid exposure prediction")
    return values


def metrics(actual, predicted):
    error = np.asarray(predicted) - np.asarray(actual)
    denom = float(np.sum(actual))
    return {
        "cases": len(error),
        "mae_raw_units": float(np.abs(error).mean()),
        "absolute_error_over_event_balance": float(np.abs(error).sum() / denom)
        if denom > 0
        else None,
        "bias_over_event_balance": float(error.sum() / denom) if denom > 0 else None,
        "negative_prediction_cases": int((np.asarray(predicted) < 0).sum()),
    }


def run(root, output):
    if output.exists():
        raise FileExistsError(output)
    source = root / "raw/home-credit-default-risk-2018/credit_card_balance.csv"
    dictionary = root / "raw/home-credit-default-risk-2018/HomeCredit_columns_description.csv"
    con = duckdb.connect()
    con.execute(
        """CREATE TABLE monthly AS SELECT SK_ID_PREV account_id,CAST(SK_ID_CURR AS VARCHAR) application_link,
        MONTHS_BALANCE month_index,AMT_BALANCE drawn_balance,AMT_CREDIT_LIMIT_ACTUAL credit_limit,
        SK_DPD dpd,SK_DPD_DEF dpd_tolerance,AMT_DRAWINGS_CURRENT drawings,AMT_PAYMENT_TOTAL_CURRENT payments
        FROM read_csv(?,header=true)""",
        [str(source)],
    )
    history = con.execute(
        "SELECT * FROM monthly WHERE account_id IN (SELECT DISTINCT account_id FROM monthly WHERE dpd>=90 OR dpd_tolerance>=90)"
    ).fetchdf()
    con.close()
    reports = []
    all_pairs = []
    all_predictions = []
    models = {}
    for name, column in [("raw90", "dpd"), ("tolerance90", "dpd_tolerance")]:
        p = proxy_pairs(history.rename(columns={column: "days_past_due"}), horizons=(3, 6, 12))
        p["definition"] = name
        all_pairs.append(p)
        eligible = p[p.eligibility.eq("eligible_delinquency_proxy")]
        enriched = add_features(eligible, history)
        definition_report = {
            "definition": name,
            "event_accounts": int(p.account_id.nunique()),
            "eligibility": p.groupby(["horizon_months", "eligibility"])
            .size()
            .reset_index(name="cases")
            .to_dict("records"),
            "horizons": [],
        }
        for horizon, g in enriched.groupby("horizon_months"):
            valid = g[g.anchor_limit.gt(0)].copy()
            train = valid[valid.split.eq("training_group")]
            test = valid[valid.split.eq("held_out_group")].copy()
            if set(train.application_link) & set(test.application_link):
                raise ValueError("Application overlap")
            positive_undrawn = valid.ccf.notna()
            ccf = valid.loc[positive_undrawn, "ccf"]
            summary = {
                "horizon_months": int(horizon),
                "eligible_pairs": len(g),
                "positive_anchor_limit": len(valid),
                "excluded_zero_anchor_limit_from_ratio_model": int(g.anchor_limit.le(0).sum()),
                "training_cases": len(train),
                "held_out_cases": len(test),
                "training_groups": int(train.application_link.nunique()),
                "held_out_groups": int(test.application_link.nunique()),
                "defined_ccf_pairs": int(positive_undrawn.sum()),
                "ccf_negative": int(ccf.lt(0).sum()),
                "ccf_above_one": int(ccf.gt(1).sum()),
                "median_ccf": float(ccf.median()) if len(ccf) else None,
                "zero_event_balances": int(valid.event_balance.eq(0).sum()),
                "limit_reduced_by_event": int(valid.event_limit.lt(valid.anchor_limit).sum()),
            }
            # Fixed minimum, declared before model results: avoid complex estimates on sparse definitions.
            if (
                train.application_link.nunique() < 60
                or test.application_link.nunique() < 20
                or train.event_balance.sum() <= 0
            ):
                summary["fit_status"] = "skipped_insufficient_groups_or_zero_target"
            else:
                model = fit_direct(train)
                key = f"{name}_{int(horizon)}"
                models[key] = model
                test["direct_poisson_ratio"] = predict_direct(model, test)
                test["hold_balance"] = test.anchor_balance
                test["training_mean_ead"] = train.event_balance.mean()
                test["training_mean_limit_ratio"] = (
                    test.anchor_limit * (train.event_balance / train.anchor_limit).mean()
                )
                summary["fit_status"] = "fitted_exploratory_conditional_delinquency_proxy"
                summary["metrics"] = {
                    c: metrics(test.event_balance, test[c])
                    for c in [
                        "hold_balance",
                        "training_mean_ead",
                        "training_mean_limit_ratio",
                        "direct_poisson_ratio",
                    ]
                }
                # CCF benchmark only on matched positive-undrawn anchors; can imply negative EAD.
                cc_train = train[train.ccf.notna()]
                cc_test = test[test.ccf.notna()]
                if len(cc_train) and len(cc_test):
                    cc_pred = cc_test.anchor_balance + cc_train.ccf.mean() * (
                        cc_test.anchor_limit - cc_test.anchor_balance
                    )
                    summary["unconstrained_training_mean_ccf_benchmark"] = metrics(
                        cc_test.event_balance, cc_pred
                    )
                    summary["ccf_benchmark_warning"] = (
                        "Different positive-undrawn subset; negative predicted EAD invalid, not clipped"
                    )
                test["model_key"] = key
                all_predictions.append(test)
            definition_report["horizons"].append(summary)
        reports.append(definition_report)
    pairs = pd.concat(all_pairs, ignore_index=True)
    predictions = (
        pd.concat(all_predictions, ignore_index=True) if all_predictions else pd.DataFrame()
    )
    report = {
        "status": "first_real_data_proxy_test_not_validated_default_model",
        "source_sha256": sha256(source),
        "dictionary_sha256": sha256(dictionary),
        "code_sha256": sha256(Path(__file__)),
        "split": "SHA256 application link modulo5==0 heldout; same mapping across definitions/horizons; not calendar OOT",
        "target": "AMT_BALANCE at first observed90DPD raw/tolerance proxy; units and interest basis unverified",
        "features": FEATURES,
        "direct_method": "PoissonRegressor alpha1 loglink on EAD/anchorlimit; mean in original source units",
        "minimum_training_groups": 60,
        "minimum_held_out_groups": 20,
        "definitions": reports,
        "limits": [
            "RawDPD mostly ignored by small-debt-tolerant measure, may be immaterial delinquency, not contractual default",
            "ApplicationTARGET not used and not joined",
            "Sample conditioned on observed delinquency and coverage; not unconditional portfolio EAD",
            "Account-relative months do not support calendar OOT or macro backtesting",
            "Application-link groups not established ultimate borrower identity",
            "CCF negative/above1 retained; undefined fully drawn/overlimit cases kept",
            "Zero-limit cases excluded only from ratio fit,not raw pairs",
            "No clipping,parameter search,source-label changes,CRE integration or production approval",
            "No new draws or balances simulated; no real default labels invented",
        ],
    }
    output.mkdir(parents=True)
    pairs.to_parquet(output / "all_proxy_pairs.parquet", index=False)
    predictions.to_parquet(output / "held_out_predictions.parquet", index=False)
    joblib.dump(models, output / "models.joblib")
    loaded = joblib.load(output / "models.joblib")
    if len(predictions):
        for key, g in predictions.groupby("model_key"):
            np.testing.assert_allclose(
                predict_direct(loaded[key], g), g.direct_poisson_ratio, rtol=1e-12, atol=1e-8
            )
    report["reload_verified_held_out_horizon_cases"] = len(predictions)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.root, a.output)
