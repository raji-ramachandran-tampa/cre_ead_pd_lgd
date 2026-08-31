"""Contractual EAD benchmark calculations."""

from __future__ import annotations

from math import isfinite


def project_contractual_ead(
    current_balance: float,
    scheduled_principal: list[float] | tuple[float, ...],
    future_draws: list[float] | tuple[float, ...] | None = None,
    commitment_limit: float | None = None,
) -> tuple[float, ...]:
    """Project nonnegative period-end exposure from payments and approved draws."""
    if not isfinite(current_balance) or current_balance < 0.0:
        raise ValueError("current_balance must be finite and nonnegative")
    draws = tuple(future_draws or [0.0] * len(scheduled_principal))
    if len(draws) != len(scheduled_principal):
        raise ValueError("scheduled_principal and future_draws must have equal lengths")
    if commitment_limit is not None and (
        not isfinite(commitment_limit) or commitment_limit < current_balance
    ):
        raise ValueError("commitment_limit must be finite and at least current balance")

    balance = current_balance
    result: list[float] = []
    for principal, draw in zip(scheduled_principal, draws, strict=True):
        if any(not isfinite(value) or value < 0.0 for value in (principal, draw)):
            raise ValueError("Principal and draws must be finite and nonnegative")
        balance = max(0.0, balance - principal) + draw
        if commitment_limit is not None and balance > commitment_limit:
            raise ValueError("Projected exposure exceeds commitment limit")
        result.append(balance)
    return tuple(result)

