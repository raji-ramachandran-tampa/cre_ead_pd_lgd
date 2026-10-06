"""Assumption-based discounting of a terminal net accounting equivalent."""

from math import isfinite


def discounted_accounting_bridge(signed_ratio: float, years: float, rate: float) -> float:
    """1-(1-L)/(1+r)^T; neither a reconstructed gross recovery nor observed LGD.

    Assumes the accounting net recovery equivalent is received at resolution.
    Costs, interest and allocation cannot be separately identified in this bridge.
    """
    if not all(isfinite(v) for v in [signed_ratio, years, rate]):
        raise ValueError("Finite inputs required")
    if years < 0 or rate < 0:
        raise ValueError("Nonnegative duration and illustrative rate required")
    return 1 - (1 - signed_ratio) / (1 + rate) ** years
