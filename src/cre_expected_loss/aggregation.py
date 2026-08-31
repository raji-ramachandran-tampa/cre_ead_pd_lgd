"""Deterministic loan-horizon-scenario expected-loss calculations."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class ExpectedLossRow:
    """One validated loan-horizon-scenario expected-loss input and result."""

    loan_id: str
    property_id: str
    horizon: int
    scenario_id: str
    marginal_pd: float
    lgd: float
    ead: float
    discount_factor: float = 1.0

    @property
    def expected_loss(self) -> float:
        """Return marginal PD × LGD × EAD × discount factor."""
        _validate_row(self)
        return self.marginal_pd * self.lgd * self.ead * self.discount_factor


def _validate_row(row: ExpectedLossRow) -> None:
    values = (row.marginal_pd, row.lgd, row.ead, row.discount_factor)
    if not all(isfinite(value) for value in values):
        raise ValueError("Expected-loss inputs must be finite")
    if not 0.0 <= row.marginal_pd <= 1.0:
        raise ValueError("marginal_pd must be between zero and one")
    if not 0.0 <= row.lgd <= 1.0:
        raise ValueError("lgd must be between zero and one for projected output")
    if row.ead < 0.0:
        raise ValueError("ead must be nonnegative")
    if not 0.0 < row.discount_factor <= 1.0:
        raise ValueError("discount_factor must be greater than zero and at most one")
    if row.horizon < 1:
        raise ValueError("horizon must be a positive integer")
    if not row.loan_id or not row.property_id or not row.scenario_id:
        raise ValueError("loan, property, and scenario identifiers are required")


def calculate_expected_loss(rows: Iterable[ExpectedLossRow]) -> list[dict[str, object]]:
    """Calculate and preserve expected loss at loan-horizon-scenario grain."""
    return [
        {
            "loan_id": row.loan_id,
            "property_id": row.property_id,
            "horizon": row.horizon,
            "scenario_id": row.scenario_id,
            "marginal_pd": row.marginal_pd,
            "lgd": row.lgd,
            "ead": row.ead,
            "discount_factor": row.discount_factor,
            "expected_loss": row.expected_loss,
        }
        for row in rows
    ]


def aggregate_scenario_weighted_loss(
    rows: Iterable[ExpectedLossRow], scenario_weights: dict[str, float]
) -> float:
    """Aggregate scenario-specific results only after validating scenario weights."""
    from .scenarios import validate_scenario_weights

    validate_scenario_weights(scenario_weights)
    total = 0.0
    for row in rows:
        if row.scenario_id not in scenario_weights:
            raise ValueError(f"Missing weight for scenario {row.scenario_id!r}")
        total += row.expected_loss * scenario_weights[row.scenario_id]
    return total

