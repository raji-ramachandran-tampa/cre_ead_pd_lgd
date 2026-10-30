"""Matched EAD diagnostic/backtest evidence, without selecting a new baseline."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .ead_research import FEATURES, prepare, score

CANDIDATES = [
    "balance_hold_prediction",
    "amortization_prediction",
    "io_clock_sensitivity",
    "ridge_prediction",
]


def fit_fold(train, test):
    """Fit preprocessing and ridge only to prior-onset cohorts."""
    if set(train.loan_id) & set(test.loan_id):
        raise ValueError("Overlapping loans across temporal fold")
    if train.onset_date.max() >= test.onset_date.min():
        raise ValueError("Training outcomes must precede evaluation outcomes")
    model = make_pipeline(StandardScaler(), Ridge(alpha=10))
    model.fit(train[FEATURES], train.onset_scheduled_upb / train.anchor_upb - 1)
    prediction = test.anchor_upb * (1 + model.predict(test[FEATURES]))
    if not np.isfinite(prediction).all() or prediction.lt(0).any():
        raise ValueError("Invalid ridge exposure; no clipping")
    return prediction


def enrich(frame):
    frame = frame.copy()
    is_io = frame.amortization_type.str.contains("Interest Only", na=False)
    frame["io_stage"] = np.select(
        [~is_io, frame.remaining_io.ge(frame.horizon_months), frame.remaining_io.gt(0)],
        ["no_io", "within_io", "crosses_io_end"],
        default="after_io",
    )
    frame["balance_segment"] = pd.cut(
        frame.anchor_upb, [0, 5e6, 20e6, np.inf], labels=["up_to_5m", "5_to_20m", "above_20m"]
    )
    frame["maturity_segment"] = pd.cut(
        frame.months_to_maturity,
        [-np.inf, 12, 36, np.inf],
        labels=["within_12m", "12_to_36m", "above_36m"],
    )
    return frame


def run(source: Path, models: Path, output: Path):
    if output.exists():
        raise FileExistsError(output)
    raw = prepare(pd.read_parquet(source / "benchmark_cases.parquet"))
    frozen = enrich(pd.read_parquet(models / "predictions.parquet"))
    backtests = []
    folds = []
    for horizon, g in frozen.groupby("horizon_months"):
        for end, last in [(2008, 2011), (2011, 2014), (2014, 2018), (2018, 2022)]:
            train = g[g.onset_date.dt.year.le(end)]
            test = g[g.onset_date.dt.year.gt(end) & g.onset_date.dt.year.le(last)].copy()
            if len(train) < 30 or test.empty:
                folds.append(
                    {
                        "horizon_months": int(horizon),
                        "train_through": end,
                        "eval_through": last,
                        "train_cases": len(train),
                        "eval_cases": len(test),
                        "status": "skipped_small_sample",
                    }
                )
                continue
            test["ridge_prediction"] = fit_fold(train, test)
            test["fold_train_through"] = end
            backtests.append(test)
            folds.append(
                {
                    "horizon_months": int(horizon),
                    "train_through": end,
                    "eval_through": last,
                    "train_cases": len(train),
                    "eval_cases": len(test),
                    "status": "evaluated",
                }
            )
    back = pd.concat(backtests, ignore_index=True)
    historical = []
    for horizon, g in back.groupby("horizon_months"):
        for c in CANDIDATES:
            matched = g.dropna(subset=CANDIDATES)
            historical.append({"horizon_months": int(horizon), "candidate": c, **score(matched, c)})
    segments = []
    for (horizon, partition), g in frozen.groupby(["horizon_months", "partition"]):
        for field in ["amortization_type", "io_stage", "balance_segment", "maturity_segment"]:
            for value, s in g.groupby(field, observed=True):
                s = s.dropna(subset=CANDIDATES)
                if s.empty:
                    continue
                for c in CANDIDATES:
                    segments.append(
                        {
                            "horizon_months": int(horizon),
                            "partition": partition,
                            "segment_field": field,
                            "segment": str(value),
                            "candidate": c,
                            **score(s, c),
                        }
                    )
    # Diagnostic maturity cohort retains principal-hold exposure, never assumes balloon paid.
    maturity = []
    for (horizon, partition), g in raw[
        raw.eligible & raw.schedule_status.eq("at_or_beyond_maturity")
    ].groupby(["horizon_months", "partition"]):
        err = (g.balance_hold_prediction - g.onset_scheduled_upb).abs() / g.onset_scheduled_upb
        maturity.append(
            {
                "horizon_months": int(horizon),
                "partition": partition,
                **score(g, "balance_hold_prediction"),
                "max_absolute_relative_error": float(err.max()),
                "outcome_exceeds_anchor_cases": int(g.onset_scheduled_upb.gt(g.anchor_upb).sum()),
            }
        )
    report = {
        "status": "diagnostic_evidence_no_baseline_selection",
        "model_report_sha256": hashlib.sha256((models / "report.json").read_bytes()).hexdigest(),
        "source_report_sha256": hashlib.sha256((source / "report.json").read_bytes()).hexdigest(),
        "folds": folds,
        "historical_refit_metrics": historical,
        "segment_metrics": segments,
        "maturity_hold_metrics": maturity,
        "limits": [
            "First SDQ principal proxy, not verified funded EAD or common PD/LGD default",
            "Chronological first-onset loans disjoint; no borrower/transaction linkage purge available",
            "Expanding evaluations include 2019-2022 validation years, not independent extra evidence",
            "Segments exploratory, small groups unstable, no alpha/convention selection on later outcomes",
            "Maturity cohort descriptive hold benchmark only; no inferred payoff at maturity",
            "Revised source availability remains unverified",
        ],
    }
    output.mkdir(parents=True)
    back.to_parquet(output / "historical_predictions.parquet", index=False)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {k: report[k] for k in ["folds", "historical_refit_metrics", "maturity_hold_metrics"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.models, args.output)
