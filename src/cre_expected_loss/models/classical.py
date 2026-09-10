"""Transparent classical benchmark estimators for development research.

These estimators are proposed research implementations. They are not approved
for production, accounting, capital, or credit-decision use.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class BinaryMetrics:
    """Out-of-sample binary probability metrics."""

    observations: int
    events: int
    roc_auc: float | None
    average_precision: float | None
    brier_score: float
    log_loss: float


def _sklearn() -> dict[str, Any]:
    try:
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            average_precision_score,
            brier_score_loss,
            log_loss,
            roc_auc_score,
        )
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise RuntimeError("Install the modeling dependencies to fit models") from exc
    return {
        "ColumnTransformer": ColumnTransformer,
        "SimpleImputer": SimpleImputer,
        "LogisticRegression": LogisticRegression,
        "average_precision_score": average_precision_score,
        "brier_score_loss": brier_score_loss,
        "log_loss": log_loss,
        "roc_auc_score": roc_auc_score,
        "Pipeline": Pipeline,
        "OneHotEncoder": OneHotEncoder,
        "StandardScaler": StandardScaler,
    }


def fit_logistic_pd(
    frame: Any,
    target: str,
    numeric_features: Sequence[str],
    categorical_features: Sequence[str] = (),
    *,
    class_weight: str | dict[int, float] | None = "balanced",
    random_state: int = 20260901,
    sample_weight: Any | None = None,
) -> Any:
    """Fit an interpretable logistic one-period PD benchmark pipeline."""
    if target in {*numeric_features, *categorical_features}:
        raise ValueError("Target cannot also be a feature")
    if not numeric_features and not categorical_features:
        raise ValueError("At least one feature is required")
    if frame[target].isna().any() or set(frame[target].unique()) - {0, 1}:
        raise ValueError("PD target must contain only nonmissing zero/one values")
    if frame[target].nunique() != 2:
        raise ValueError("PD fitting requires both event and non-event observations")

    sk = _sklearn()
    numeric = sk["Pipeline"](
        [("impute", sk["SimpleImputer"](strategy="median")), ("scale", sk["StandardScaler"]())]
    )
    categorical = sk["Pipeline"](
        [
            ("impute", sk["SimpleImputer"](strategy="most_frequent")),
            ("encode", sk["OneHotEncoder"](handle_unknown="ignore")),
        ]
    )
    transformer = sk["ColumnTransformer"](
        [
            ("numeric", numeric, list(numeric_features)),
            ("categorical", categorical, list(categorical_features)),
        ]
    )
    model = sk["Pipeline"](
        [
            ("features", transformer),
            (
                "model",
                sk["LogisticRegression"](
                    class_weight=class_weight,
                    max_iter=1_000,
                    random_state=random_state,
                    solver="liblinear",
                ),
            ),
        ]
    )
    fit_parameters = {"model__sample_weight": sample_weight} if sample_weight is not None else {}
    return model.fit(
        frame[list(numeric_features) + list(categorical_features)],
        frame[target],
        **fit_parameters,
    )


def binary_metrics(actual: Any, probability: Any) -> BinaryMetrics:
    """Calculate discrimination and calibration metrics with explicit bounds."""
    sk = _sklearn()
    actual_values = list(actual)
    probabilities = [float(value) for value in probability]
    if len(actual_values) != len(probabilities) or not actual_values:
        raise ValueError("Actuals and probabilities must have equal nonzero length")
    if set(actual_values) - {0, 1}:
        raise ValueError("Actuals must be zero/one")
    if any(not isfinite(value) or not 0.0 <= value <= 1.0 for value in probabilities):
        raise ValueError("Probabilities must be finite and in [0, 1]")
    two_classes = len(set(actual_values)) == 2
    return BinaryMetrics(
        observations=len(actual_values),
        events=sum(actual_values),
        roc_auc=float(sk["roc_auc_score"](actual_values, probabilities)) if two_classes else None,
        average_precision=(
            float(sk["average_precision_score"](actual_values, probabilities))
            if two_classes
            else None
        ),
        brier_score=float(sk["brier_score_loss"](actual_values, probabilities)),
        log_loss=float(sk["log_loss"](actual_values, probabilities, labels=[0, 1])),
    )


def empirical_lgd(loss_amount: float, default_amount: float) -> float:
    """Return uncapped provisional LGD from Fannie's cumulative loss fields."""
    values = (float(loss_amount), float(default_amount))
    if any(not isfinite(value) for value in values) or values[1] <= 0.0:
        raise ValueError("Loss must be finite and default amount finite and positive")
    return values[0] / values[1]


def funded_term_ead(current_upb: float) -> float:
    """Return the current-UPB benchmark EAD for an ordinary fully funded term loan."""
    value = float(current_upb)
    if not isfinite(value) or value < 0.0:
        raise ValueError("Current UPB must be finite and nonnegative")
    return value
