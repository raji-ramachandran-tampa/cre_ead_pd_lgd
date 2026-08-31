"""Scenario-weight validation."""

from math import isfinite


def validate_scenario_weights(weights: dict[str, float], tolerance: float = 1e-12) -> None:
    """Raise when weights are missing, nonfinite, negative, or do not sum to one."""
    if not weights or any(not name for name in weights):
        raise ValueError("At least one named scenario is required")
    if any(not isfinite(weight) or weight < 0.0 for weight in weights.values()):
        raise ValueError("Scenario weights must be finite and nonnegative")
    if abs(sum(weights.values()) - 1.0) > tolerance:
        raise ValueError("Scenario weights must sum to one")

