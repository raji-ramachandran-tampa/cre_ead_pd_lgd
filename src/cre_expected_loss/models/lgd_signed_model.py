"""Signed source net-loss research: chronological ridge benchmarks, no output caps."""

from __future__ import annotations
from pathlib import Path
import json
import hashlib
import tempfile
import csv
import io
import zipfile
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import Ridge


def parse_accounting(value: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    text = text.replace("$", "").replace(",", "").replace("%", "")
    try:
        result = float(text)
    except ValueError:
        return None
    if not np.isfinite(result):
        return None
    return -result if negative else result


def fit_signed(frame: pd.DataFrame, enriched: bool = False, loss_sharing: bool = False):
    y = frame.signed_ratio.to_numpy(float)
    if len(y) < 10 or not np.isfinite(y).all():
        raise ValueError("Need ten finite signed outcomes")
    nums = ["acquisition_ltv", "underwritten_dscr"]
    cats = []
    if enriched:
        nums += ["log_acquisition_upb"]
        cats += ["property_type"]
    if loss_sharing:
        cats += ["loss_sharing_type"]
    if np.isinf(frame[nums].to_numpy(float)).any() or frame[nums].isna().all().any():
        raise ValueError("Invalid numeric features")
    transforms = [
        ("numeric", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), nums)
    ]
    if cats:
        transforms.append(
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cats)
        )
    model = make_pipeline(ColumnTransformer(transforms), Ridge(alpha=10.0))
    model.fit(frame, y)
    return model


def compare(train, test):
    predictions = {"mean_benchmark": np.full(len(test), train.signed_ratio.mean())}
    for name, enriched, sharing in [
        ("ridge_core", False, False),
        ("ridge_enriched", True, False),
        ("ridge_loss_sharing", True, True),
    ]:
        predictions[name] = fit_signed(train, enriched, sharing).predict(test)
    metrics = {}
    y = test.signed_ratio.to_numpy()
    for name, p in predictions.items():
        if not np.isfinite(p).all():
            raise ValueError("Nonfinite predictions")
        metrics[name] = {
            "mae": float(np.abs(p - y).mean()),
            "rmse": float(np.sqrt(((p - y) ** 2).mean())),
            "mean_actual": float(y.mean()),
            "mean_prediction": float(p.mean()),
            "exposure_weighted_mean_actual": float(np.average(y, weights=test.parsed_default)),
            "exposure_weighted_mean_prediction": float(np.average(p, weights=test.parsed_default)),
        }
    return metrics, predictions


def run(fannie_root: Path):
    import joblib, platform, sklearn

    artifacts = fannie_root / "artifacts/2026Q1"
    output = artifacts / "lgd-signed-research-v0.1.0"
    if output.exists():
        raise FileExistsError(output)
    source = artifacts / "lgd-signed-feasibility-v0.1.0/signed_outcome_audit.parquet"
    all_cases = pd.read_parquet(source)
    frame = all_cases[all_cases.signed_feasible].copy()
    if not frame.loan_id.is_unique:
        raise ValueError("Duplicate loan IDs")
    # Verify signed source amount consistency across raw histories before fitting.
    histories = {
        loan: {"loss": set(), "default": set(), "invalid_loss": 0} for loan in all_cases.loan_id
    }
    raw = next((fannie_root / "raw").rglob("Multifamily.zip"))
    with zipfile.ZipFile(raw) as archive:
        with archive.open(
            next(n for n in archive.namelist() if n.lower().endswith(".csv"))
        ) as stream:
            reader = csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig"))
            header = next(reader)
            ix = [
                header.index(n)
                for n in ["Loan Number", "Lifetime Net Credit Loss Amount", "Default Amount"]
            ]
            for row in reader:
                loan = row[ix[0]].strip()
                if loan not in histories:
                    continue
                h = histories[loan]
                for name, i in [("loss", ix[1]), ("default", ix[2])]:
                    parsed = parse_accounting(row[i])
                    if parsed is not None:
                        h[name].add(parsed)
                    elif name == "loss" and row[i].strip():
                        h["invalid_loss"] += 1
    conflicts = []
    for _, r in frame.iterrows():
        h = histories[r.loan_id]
        if len(h["loss"]) != 1 or len(h["default"]) != 1 or h["invalid_loss"]:
            conflicts.append(r.loan_id)
            continue
        if not np.isclose(next(iter(h["loss"])), r.signed_loss, rtol=0, atol=1e-8):
            conflicts.append(r.loan_id)
        if not np.isclose(next(iter(h["default"])), r.parsed_default, rtol=0, atol=1e-8):
            conflicts.append(r.loan_id)
    if conflicts:
        raise ValueError(
            f"{len(set(conflicts))} eligible signed-history conflicts require reconciliation"
        )
    if not frame.acquisition_upb.gt(0).all():
        raise ValueError("Invalid acquisition balances")
    frame["log_acquisition_upb"] = np.log(frame.acquisition_upb)
    frame["property_type"] = frame.property_type.fillna("Unknown")
    frame["loss_sharing_type"] = frame.loss_sharing_type.fillna("").replace("", "Unknown")
    frame["group"] = np.where(
        frame.transaction_id.fillna("").ne(""), frame.transaction_id, frame.loan_id
    )
    train = frame[frame.credit_event_year <= 2018]
    fixed = {}
    later = []
    for period, test in frame[frame.credit_event_year > 2018].groupby("period"):
        metrics, predictions = compare(train, test)
        fixed[period] = {
            "cases": len(test),
            "negative_cases": int(test.signed_ratio.lt(0).sum()),
            "metrics": metrics,
        }
        for name, p in predictions.items():
            later.append(
                pd.DataFrame(
                    {
                        "loan_id": test.loan_id,
                        "period": period,
                        "candidate": name,
                        "actual": test.signed_ratio,
                        "prediction": p,
                    }
                )
            )
    folds = []
    predictions = []
    for end, next_end in [(2008, 2011), (2011, 2014), (2014, 2018), (2018, 2022)]:
        tr = frame[frame.credit_event_year <= end]
        te = frame[(frame.credit_event_year > end) & (frame.credit_event_year <= next_end)]
        overlap = tr.group.isin(te.group)
        clean = tr[~overlap]
        if len(clean) < 10 or len(te) == 0:
            raise ValueError("Insufficient fold")
        metrics, preds = compare(clean, te)
        folds.append(
            {
                "train_end": end,
                "evaluation_end": next_end,
                "training_cases": len(clean),
                "evaluation_cases": len(te),
                "purged_mbs_transaction_overlap_cases": int(overlap.sum()),
                "metrics": metrics,
            }
        )
        for name, p in preds.items():
            predictions.append(
                pd.DataFrame(
                    {
                        "loan_id": te.loan_id,
                        "group": te.group,
                        "fold": end,
                        "candidate": name,
                        "actual": te.signed_ratio,
                        "prediction": p,
                    }
                )
            )
    rolling = pd.concat(predictions, ignore_index=True)
    wide = (
        rolling.pivot(index=["loan_id", "group", "fold"], columns="candidate", values="prediction")
        .join(rolling.drop_duplicates("loan_id").set_index(["loan_id", "group", "fold"]).actual)
        .reset_index()
    )
    groups = wide.group.unique()
    sizes = np.array([(wide.group == g).sum() for g in groups])
    rng = np.random.default_rng(20260901)
    idx = rng.integers(0, len(groups), size=(2000, len(groups)))
    pooled = {}
    for name, g in rolling.groupby("candidate"):
        pooled[name] = {
            "cases": len(g),
            "mae": float(np.abs(g.prediction - g.actual).mean()),
            "rmse": float(np.sqrt(((g.prediction - g.actual) ** 2).mean())),
        }
        if name != "mean_benchmark":
            differences = np.array(
                [
                    (
                        (wide[wide.group == group][name] - wide[wide.group == group].actual).abs()
                        - (
                            wide[wide.group == group].mean_benchmark
                            - wide[wide.group == group].actual
                        ).abs()
                    ).sum()
                    for group in groups
                ]
            )
            draws = differences[idx].sum(axis=1) / sizes[idx].sum(axis=1)
            pooled[name]["mae_difference_95_interval"] = np.quantile(draws, [0.025, 0.975]).tolist()
    models = {
        name: fit_signed(train, e, s)
        for name, e, s in [
            ("ridge_core", False, False),
            ("ridge_enriched", True, False),
            ("ridge_loss_sharing", True, True),
        ]
    }
    counts = {
        p: {
            "cases": len(g),
            "negative": int(g.signed_ratio.lt(0).sum()),
            "zero": int(g.signed_ratio.eq(0).sum()),
            "mean": float(g.signed_ratio.mean()),
        }
        for p, g in frame.groupby("period")
    }
    digest = hashlib.sha256()
    with raw.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    report = {
        "status": "signed_source_ratio_research_not_selected_or_approved",
        "target": "uncapped signed source-reported net credit loss / source default amount",
        "authorization": "User explicitly chose full signed source net-loss ratio in chat, October 5, 2026.",
        "outcome_version": "signed-source-ratio-v0.1.0",
        "periods": counts,
        "raw_history_consistency_passed": True,
        "raw_zip_sha256": digest.hexdigest(),
        "driver_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "ridge_alpha": 10.0,
        "fixed_2018_fit": fixed,
        "folds": folds,
        "pooled_backtests": pooled,
        "features": {
            "core": ["acquisition_ltv", "underwritten_dscr"],
            "enriched": [
                "acquisition_ltv",
                "underwritten_dscr",
                "log_acquisition_upb",
                "property_type",
            ],
            "loss_sharing": [
                "acquisition_ltv",
                "underwritten_dscr",
                "log_acquisition_upb",
                "property_type",
                "loss_sharing_type",
            ],
        },
        "sources": [
            "https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-glossary-file-layout.pdf",
            "https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-credit-loss-qrg.pdf",
        ],
        "bootstrap": "2000 fixed-error MBS transaction-group resamples, seed 20260901; excludes fitting uncertainty and unknown borrower grouping.",
        "runtime": {"python": platform.python_version(), "sklearn": sklearn.__version__},
        "limitations": [
            "Source net loss reflects cash flows and loss sharing, not gross borrower economic loss.",
            "Transaction ID identifies securitized MBS transactions, not borrower/workout groups.",
            "Revised source snapshot and unverified publication timing prevent point-in-time claims.",
            "Zero/missing denominators stay excluded; no UPB substitution.",
            "OOT has been used for development hypotheses; no independent selection evidence.",
            "New signed outcome is event-loan-only; original v0.3.0 monthly data remain unchanged.",
        ],
    }
    with tempfile.TemporaryDirectory(prefix="signed-stage-", dir=artifacts) as temporary:
        stage = Path(temporary) / "output"
        stage.mkdir()
        frame.to_parquet(stage / "signed_outcomes.parquet", index=False)
        rolling.to_parquet(stage / "rolling_predictions.parquet", index=False)
        pd.concat(later).to_parquet(stage / "later_predictions.parquet", index=False)
        joblib.dump(models, stage / "models.joblib")
        (stage / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        stage.rename(output)
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "periods",
                    "raw_history_consistency_passed",
                    "fixed_2018_fit",
                    "pooled_backtests",
                ]
            },
            indent=2,
        )
    )
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--fannie-root", type=Path, required=True)
    run(parser.parse_args().fannie_root)
