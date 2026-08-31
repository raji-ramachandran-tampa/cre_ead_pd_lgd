"""Transparent CRE feature formulas with explicit invalid-input behavior."""

from datetime import date
from math import isfinite


def _positive_ratio(numerator: float, denominator: float, name: str) -> float:
    if not all(isfinite(value) for value in (numerator, denominator)):
        raise ValueError(f"{name} inputs must be finite")
    if numerator < 0.0 or denominator <= 0.0:
        raise ValueError(f"{name} requires nonnegative numerator and positive denominator")
    return numerator / denominator


def loan_to_value(exposure: float, property_value: float) -> float:
    """Return exposure divided by eligible property value."""
    return _positive_ratio(exposure, property_value, "loan_to_value")


def debt_service_coverage_ratio(noi: float, annual_debt_service: float) -> float:
    """Return approved annual NOI divided by annual debt service."""
    return _positive_ratio(noi, annual_debt_service, "debt_service_coverage_ratio")


def valuation_age_days(valuation_date: date, as_of_date: date) -> int:
    """Return nonnegative property-valuation age at the prediction date."""
    age = (as_of_date - valuation_date).days
    if age < 0:
        raise ValueError("valuation_date cannot be after as_of_date")
    return age

