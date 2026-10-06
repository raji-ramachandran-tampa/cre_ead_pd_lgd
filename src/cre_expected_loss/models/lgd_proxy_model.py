"""Ridge/CPI models for assumption-based discounted accounting targets."""

import hashlib
import json
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .lgd_macro_research import FOLDS, attach_macro, fit, macro_panel, metrics


def fit_proxy(frame, use_cpi=True):
    """Reuse train-only preprocessing; proxy and realized duration are not features."""
    training = frame.copy()
    training["signed_ratio"] = training["discounted_accounting_proxy"]
    return fit(training, ["cpi_log_change_6m"] if use_cpi else [])


def run(artifact_root: Path, macro_root: Path, output: Path):
    if output.exists():
        raise FileExistsError(output)
    source = artifact_root / "lgd-signed-research-v0.1.0/signed_outcomes.parquet"
    proxy = artifact_root / "lgd-fannie-accounting-bridge-v0.1.0/sensitivity.parquet"
    original = attach_macro(pd.read_parquet(source), macro_panel(macro_root, 6))
    if not original.loan_id.is_unique:
        raise ValueError("Duplicate source case")
    labels = pd.read_parquet(proxy)
    predictions, counts, models = [], [], {}
    for (rate, fraction), labels_scope in labels.groupby(["rate", "timing_fraction"]):
        if not labels_scope.loan_id.is_unique:
            raise ValueError("Duplicate proxy labels")
        f = original.merge(
            labels_scope[["loan_id", "discounted_accounting_proxy"]],
            on="loan_id",
            validate="one_to_one",
        )
        scope = f"rate_{rate:g}_timing_{fraction:g}"
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
            if len(train) < 10 or test.empty:
                raise ValueError("Insufficient chronological sample")
            counts.append(
                {
                    "scope": scope,
                    "partition": partition,
                    "period": period,
                    "train": len(train),
                    "test": len(test),
                    "purged": int(overlap.sum()),
                }
            )
            fitted = {
                "proxy_ridge": fit_proxy(train, False),
                "proxy_ridge_cpi": fit_proxy(train),
                "source_ridge_cpi": fit(train, ["cpi_log_change_6m"]),
            }
            for candidate, model in fitted.items():
                pred = model.predict(test)
                if not np.isfinite(pred).all():
                    raise ValueError("Nonfinite predictions")
                predictions.append(
                    pd.DataFrame(
                        {
                            "loan_id": test.loan_id,
                            "scope": scope,
                            "partition": partition,
                            "period": period,
                            "candidate": candidate,
                            "actual": test.discounted_accounting_proxy,
                            "prediction": pred,
                        }
                    )
                )
                if partition == "later":
                    models[scope + "_" + candidate] = model
            predictions.append(
                pd.DataFrame(
                    {
                        "loan_id": test.loan_id,
                        "scope": scope,
                        "partition": partition,
                        "period": period,
                        "candidate": "proxy_mean",
                        "actual": test.discounted_accounting_proxy,
                        "prediction": train.discounted_accounting_proxy.mean(),
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
        for period, part in g.groupby("period"):
            scores.append(
                {
                    "scope": scope,
                    "partition": ("fold_" + period if partition == "rolling" else period),
                    "candidate": candidate,
                    **metrics(part),
                }
            )
    # Saved primary model must reproduce later predictions after serialization.
    primary = "rate_0.05_timing_1"
    report = {
        "status": "fitted_research_accounting_proxy_not_observed_economic_LGD",
        "primary_assumption": primary,
        "primary_choice": "5% terminal stated before fitting, not chosen by accuracy",
        "features": "existing loan core, property and loss sharing; optional lagged CPI; NO realized duration feature",
        "training_cutoff": 2018,
        "alpha": 10,
        "fold_counts": counts,
        "metrics": scores,
        "limitations": [
            "First SDQ and source Default Amount are proxies, not reconciled economic default/EAD.",
            "Accounting net equivalent embeds costs, interest and allocation; timing and rate assumed.",
            "Existing pre-disposition feature date may be during workout; not an initial-default model.",
            "Labels finalized on latest snapshots; historical availability unknown; macro revised and lags assumed.",
            "Validation29/OOT11 already examined; no independent performance confirmation.",
            "Target changes: cross-target errors cannot establish predictive improvement; source benchmark scored on SAME proxy labels.",
            "No baseline replacement, no clipping, no OOT tuning, no EL integration.",
        ],
        "hashes": {
            str(p.name): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [source, proxy, macro_root / "CPIAUCSL.csv"]
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="proxy-fit-", dir=output.parent) as tmp:
        stage = Path(tmp) / "out"
        stage.mkdir()
        predictions.to_parquet(stage / "predictions.parquet", index=False)
        joblib.dump(models, stage / "models.joblib")
        loaded = joblib.load(stage / "models.joblib")
        evaluation = original[original.credit_event_year > 2018]
        for candidate in ["proxy_ridge", "proxy_ridge_cpi", "source_ridge_cpi"]:
            observed = (
                predictions[
                    (predictions.scope == primary)
                    & (predictions.partition == "later")
                    & (predictions.candidate == candidate)
                ]
                .set_index("loan_id")
                .loc[evaluation.loan_id, "prediction"]
            )
            np.testing.assert_allclose(
                loaded[primary + "_" + candidate].predict(evaluation), observed, atol=1e-12, rtol=0
            )
        report["saved_model_check"] = (
            "all three primary models reproduce 40 later predictions within 1e-12"
        )
        (stage / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        stage.rename(output)
    print(
        json.dumps(
            [s for s in scores if s["scope"] == primary and not s["partition"].startswith("fold")],
            indent=2,
        )
    )
    return report


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    for name in ["artifact-root", "macro-root", "output"]:
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.artifact_root, a.macro_root, a.output)
