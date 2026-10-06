"""Terminal-recovery approximation; inputs and timing are explicitly assumed."""

from math import isfinite

from .lgd import WorkoutCashFlow, discounted_workout_lgd


def terminal_recovery_proxy(
    balance_proxy: float,
    gross_proceeds: float,
    combined_deductions: float,
    deduction_share: float,
    recovery_years: float,
    deduction_years: float,
    annual_rate: float,
) -> float:
    """Return signed proxy, never an observed label or verified default-EAD LGD.

    deduction_share is an allocation assumption, not an estimated probability.
    Proceeds must be gross of these deductions to avoid duplicate costs.
    """
    if not isfinite(deduction_share) or not 0 <= deduction_share <= 1:
        raise ValueError("Deduction allocation share must be in [0,1]")
    if not isfinite(combined_deductions) or combined_deductions < 0:
        raise ValueError("Combined deductions must be finite and nonnegative")
    return discounted_workout_lgd(
        balance_proxy,
        [
            WorkoutCashFlow(gross_proceeds, recovery_years, "recovery"),
            WorkoutCashFlow(combined_deductions * deduction_share, deduction_years, "cost"),
        ],
        annual_rate,
    )
