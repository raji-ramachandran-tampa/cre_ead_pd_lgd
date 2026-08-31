"""Workout cash-flow LGD calculations; estimation methods remain proposed."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Literal


@dataclass(frozen=True)
class WorkoutCashFlow:
    """Recovery or directly attributable cost at a fractional year after default."""

    amount: float
    years_after_default: float
    kind: Literal["recovery", "cost"]


def discounted_workout_lgd(
    ead_at_default: float,
    cash_flows: Iterable[WorkoutCashFlow],
    annual_discount_rate: float,
) -> float:
    """Calculate uncapped realized LGD from discounted net workout cash flows."""
    if not isfinite(ead_at_default) or ead_at_default <= 0.0:
        raise ValueError("ead_at_default must be finite and positive")
    if not isfinite(annual_discount_rate) or annual_discount_rate <= -1.0:
        raise ValueError("annual_discount_rate must be finite and greater than -1")
    present_value = 0.0
    for cash_flow in cash_flows:
        if not isfinite(cash_flow.amount) or cash_flow.amount < 0.0:
            raise ValueError("Cash-flow amounts must be finite and nonnegative")
        if not isfinite(cash_flow.years_after_default) or cash_flow.years_after_default < 0.0:
            raise ValueError("Cash-flow timing must be finite and nonnegative")
        sign = 1.0 if cash_flow.kind == "recovery" else -1.0
        present_value += sign * cash_flow.amount / (
            (1.0 + annual_discount_rate) ** cash_flow.years_after_default
        )
    return 1.0 - present_value / ead_at_default

