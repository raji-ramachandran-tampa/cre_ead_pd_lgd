"""PD term-structure transformations independent of model estimation."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class PDTermStructure:
    """Conditional hazard, marginal PD, cumulative PD, and ending survival."""

    conditional_hazard: tuple[float, ...]
    marginal_pd: tuple[float, ...]
    cumulative_pd: tuple[float, ...]
    survival: tuple[float, ...]


def hazards_to_term_structure(hazards: Iterable[float]) -> PDTermStructure:
    """Convert conditional quarterly hazards into coherent probability paths."""
    conditional = tuple(float(value) for value in hazards)
    if not conditional:
        raise ValueError("At least one hazard is required")
    if any(not isfinite(value) or not 0.0 <= value <= 1.0 for value in conditional):
        raise ValueError("Hazards must be finite probabilities between zero and one")

    survival_to_start = 1.0
    marginal: list[float] = []
    cumulative: list[float] = []
    survival: list[float] = []
    cumulative_probability = 0.0
    for hazard in conditional:
        marginal_probability = survival_to_start * hazard
        cumulative_probability += marginal_probability
        survival_to_start *= 1.0 - hazard
        marginal.append(marginal_probability)
        cumulative.append(min(cumulative_probability, 1.0))
        survival.append(max(survival_to_start, 0.0))
    return PDTermStructure(conditional, tuple(marginal), tuple(cumulative), tuple(survival))

