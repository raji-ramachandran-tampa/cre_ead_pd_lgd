"""Small signed LGD rate/spread challengers; revised-macro exploratory research."""

import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from cre_expected_loss.models.lgd_macro_research import (
    CORE,
    FOLDS,
    attach_macro,
    fit,
    macro_panel,
    metrics,
)
from cre_expected_loss.models.lgd_signed_hurdle import diagnostic, predict_hurdle


def attach_rates(frame, rate_root, lag_months=2):
    if lag_months not in [2, 3]:
        raise ValueError("Unsupported timing sensitivity")
    result = frame.copy()
    for series, name in [("DGS10", "treasury_10y"), ("BAA10YM", "baa_treasury_spread")]:
        raw = pd.read_csv(rate_root / (series + ".csv"))
        raw.columns = ["observation_date", "value"]
        raw.observation_date = pd.to_datetime(raw.observation_date, errors="raise")
        raw.value = pd.to_numeric(raw.value, errors="coerce")
        if raw.observation_date.duplicated().any():
            raise ValueError("Duplicate rate observation")
        monthly = raw.set_index("observation_date").value.resample("MS").mean().to_frame(name)
        monthly[name] /= 100.0
        if name == "treasury_10y":
            monthly["treasury_change_6m"] = monthly[name].diff(6)
        monthly[name + "_reference_date"] = monthly.index
        monthly[name + "_assumed_available_date"] = monthly.index + pd.DateOffset(months=lag_months)
        monthly = monthly.reset_index(drop=True)
        result = pd.merge_asof(
            result.sort_values("feature_date"),
            monthly.sort_values(name + "_assumed_available_date"),
            left_on="feature_date",
            right_on=name + "_assumed_available_date",
            direction="backward",
        )
        if (result[name + "_assumed_available_date"] > result.feature_date).any():
            raise ValueError("Forward rate join")
    return result


def run(artifact_root, macro_root, rate_root, output):
    import joblib

    if output.exists():
        raise FileExistsError(output)
    source = artifact_root / "lgd-signed-research-v0.1.0/signed_outcomes.parquet"
    original = pd.read_parquet(source)
    if not original.loan_id.is_unique:
        raise ValueError("Duplicate outcome")
    predictions = []
    diagnostics = []
    models = {}
    coverage = []
    fold_counts = []
    coefficients = []
    for scope, cre_lag, rate_lag in [("full", 6, 2), ("cre_covered", 6, 2), ("longer_lags", 9, 3)]:
        f = attach_rates(
            attach_macro(original, macro_panel(macro_root, cre_lag)), rate_root, rate_lag
        )
        rates = ["treasury_10y", "baa_treasury_spread"]
        required = CORE + ["cpi_log_change_6m"] + rates + ["treasury_change_6m"]
        if scope != "full":
            required += ["cre_price_yoy"]
        complete = f[required].notna().all(axis=1)
        coverage.append(
            {
                "scope": scope,
                "covered": int(complete.sum()),
                "excluded": int((~complete).sum()),
                "rate_lag_months": rate_lag,
                "cre_lag_months": cre_lag,
            }
        )
        f = f[complete]
        candidates = {
            "baseline": [],
            "cpi": ["cpi_log_change_6m"],
            "treasury": ["treasury_10y"],
            "spread": ["baa_treasury_spread"],
            "rate_change": ["treasury_change_6m"],
            "rates_spread": rates,
            "cpi_rates_spread": ["cpi_log_change_6m"] + rates,
        }
        if scope != "full":
            candidates.update(
                {
                    "cpi_cre": ["cpi_log_change_6m", "cre_price_yoy"],
                    "cpi_cre_rates_spread": ["cpi_log_change_6m", "cre_price_yoy"] + rates,
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
            sparse = min(train.signed_ratio.gt(0).sum(), train.signed_ratio.lt(0).sum()) < 3
            fold_counts.append(
                {
                    "scope": scope,
                    "partition": partition,
                    "period": period,
                    "training": len(train),
                    "evaluation": len(test),
                    "purged": int(overlap.sum()),
                    "skipped_sparse_signs": bool(sparse),
                }
            )
            if sparse:
                continue
            for name, extras in candidates.items():
                for hurdle in [False, True]:
                    candidate = ("hurdle_" if hurdle else "ridge_") + name
                    model = fit(train, extras, hurdle)
                    if hurdle:
                        detail = predict_hurdle(model, test)
                        pred = detail.prediction.to_numpy()
                        diagnostics.append(
                            {
                                "scope": scope,
                                "partition": partition,
                                "period": period,
                                "candidate": candidate,
                                "diagnostics": diagnostic(test, detail),
                            }
                        )
                    else:
                        pred = model.predict(test)
                    if not np.isfinite(pred).all():
                        raise ValueError("Nonfinite rate prediction")
                    predictions.append(
                        pd.DataFrame(
                            {
                                "loan_id": test.loan_id,
                                "group": test.group,
                                "scope": scope,
                                "partition": partition,
                                "period": period,
                                "candidate": candidate,
                                "actual": test.signed_ratio,
                                "prediction": pred,
                            }
                        )
                    )
                    if partition == "later":
                        models[scope + "_" + candidate] = vars(model) if hurdle else model
                        if not hurdle and period == "validation":
                            for feature, value in zip(
                                model[0].get_feature_names_out(), model[-1].coef_
                            ):
                                coefficients.append(
                                    {
                                        "scope": scope,
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
                        "partition": partition,
                        "period": period,
                        "candidate": "mean_benchmark",
                        "actual": test.signed_ratio,
                        "prediction": train.signed_ratio.mean(),
                    }
                )
            )
    predictions = pd.concat(predictions, ignore_index=True)
    scores = []
    for (scope, partition, candidate), g in predictions.groupby(
        ["scope", "partition", "candidate"]
    ):
        if partition == "rolling":
            scores.append(
                {
                    "scope": scope,
                    "partition": "pooled_rolling",
                    "candidate": candidate,
                    **metrics(g),
                }
            )
            for period, group in g.groupby("period"):
                scores.append(
                    {
                        "scope": scope,
                        "partition": "fold_" + period,
                        "candidate": candidate,
                        **metrics(group),
                    }
                )
        else:
            for period, group in g.groupby("period"):
                scores.append(
                    {"scope": scope, "partition": period, "candidate": candidate, **metrics(group)}
                )
    paired_results = []
    rolling = predictions[predictions.partition.eq("rolling")]
    for (scope, candidate), g in rolling.groupby(["scope", "candidate"]):
        if candidate.endswith("baseline") or candidate == "mean_benchmark":
            continue
        family = candidate.split("_")[0]
        # Incremental effect relative to same-sample baseline AND existing CPI reference.
        references = [family + "_baseline", family + "_cpi"]
        if "cre_rates" in candidate:
            references.append(family + "_cpi_cre")
        for reference in references:
            if reference == candidate:
                continue
            ref = rolling[(rolling.scope == scope) & (rolling.candidate == reference)]
            pair = g.merge(
                ref, on=["loan_id", "period"], suffixes=("", "_ref"), validate="one_to_one"
            )
            if len(pair) != len(g):
                raise ValueError("Paired sample mismatch")
            np.testing.assert_allclose(pair.actual, pair.actual_ref)
            pair["difference"] = abs(pair.prediction - pair.actual) - abs(
                pair.prediction_ref - pair.actual
            )
            groups = pair.groupby("group").difference.agg(["sum", "size"])
            rng = np.random.default_rng(20260901)
            idx = rng.integers(0, len(groups), size=(2000, len(groups)))
            draws = groups["sum"].to_numpy()[idx].sum(axis=1) / groups["size"].to_numpy()[idx].sum(
                axis=1
            )
            paired_results.append(
                {
                    "scope": scope,
                    "candidate": candidate,
                    "reference": reference,
                    "mae_difference": float(pair.difference.mean()),
                    "conditional_95_interval": np.quantile(draws, [0.025, 0.975]).tolist(),
                }
            )
    report = {
        "status": "exploratory_rate_spread_challengers_not_selected",
        "target": "signed-source-ratio-v0.1.0",
        "prediction_date": "existing pre-disposition feature_date, may occur during workout",
        "coverage": coverage,
        "fold_counts": fold_counts,
        "metrics": scores,
        "paired_bootstrap": paired_results,
        "component_diagnostics": diagnostics,
        "rate_features": {
            "DGS10": "monthly mean yield divided by 100",
            "BAA10YM": "monthly corporate Baa minus 10y Treasury spread divided by 100; broad credit proxy, not CRE loan spread",
            "treasury_change_6m": "six-month change in decimal yield",
        },
        "hashes": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                source,
                macro_root / "CPIAUCSL.csv",
                macro_root / "COMREPUSQ159N.csv",
                rate_root / "DGS10.csv",
                rate_root / "BAA10YM.csv",
            ]
        },
        "macro_manifest": json.loads((macro_root / "manifest.json").read_text()),
        "rate_snapshot": "existing 2026-09-16 FRED latest-revised snapshot",
        "limitations": [
            "Revised macro values and assumed publication lags; no point-in-time validation.",
            "Loan reporting_date is not public release availability; estimates are retrospective research.",
            "National CRE and corporate Baa spread are proxies; no CRE-specific spread supplied.",
            "Fixed regularization, no tuning or OOT calibration; many exploratory comparisons.",
            "OOT already inspected, eleven eligible loans; not independent selection evidence.",
            "Matched complete-case comparisons; earliest CRE-covered fold skipped for sparse signs.",
            "Bootstrap conditional on fixed errors and MBS groups, excludes fitting uncertainty and unknown borrower groups.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rates-stage-", dir=output.parent) as tmp:
        stage = Path(tmp) / "output"
        stage.mkdir()
        predictions.to_parquet(stage / "predictions.parquet", index=False)
        pd.DataFrame(coefficients).to_csv(stage / "ridge_coefficients.csv", index=False)
        joblib.dump(models, stage / "models.joblib")
        (stage / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        stage.rename(output)
    print(
        json.dumps(
            {
                "coverage": coverage,
                "metrics": [
                    m
                    for m in scores
                    if m["scope"] == "full" and not m["partition"].startswith("fold")
                ],
            },
            indent=2,
        )
    )
    return report


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    for name in ["artifact-root", "macro-root", "rate-root", "output"]:
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    run(args.artifact_root, args.macro_root, args.rate_root, args.output)
