"""Assumption-based scheduled principal projection; no maturity-payoff inference."""

from math import exp, expm1, isfinite, log1p


def scheduled_balance(
    balance: float,
    annual_rate: float,
    remaining_amortization_months: int,
    horizon_months: int,
    remaining_io_months: int = 0,
) -> float:
    """Level-payment balance; rate is decimal, fixed throughout the horizon.

    IO freezes principal, then a newly computed payment amortizes the current
    balance over supplied remaining months. Caller defines the term convention.
    Do not use across contractual maturity without explicit balloon treatment.
    """
    if not isfinite(balance) or balance < 0 or not isfinite(annual_rate) or annual_rate < 0:
        raise ValueError("Finite nonnegative balance and annual rate required")
    for name, value in [
        ("amortization", remaining_amortization_months),
        ("horizon", horizon_months),
        ("IO", remaining_io_months),
    ]:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} months must be nonnegative integers")
    months = max(0, horizon_months - remaining_io_months)
    if not months or not balance:
        return balance
    n = remaining_amortization_months
    if n <= 0:
        raise ValueError("Positive amortization months required after IO")
    if months >= n:
        return 0.0
    rate = annual_rate / 12
    if rate == 0:
        return balance * (n - months) / n
    # Stable balance fraction from the standard annuity formula.
    return (
        balance
        * exp(months * log1p(rate))
        * expm1((n - months) * log1p(rate))
        / expm1(n * log1p(rate))
    )
