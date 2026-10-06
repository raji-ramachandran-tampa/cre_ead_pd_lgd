"""Verified dated workout ledger contract; no inference from reported net loss."""

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Literal

from .lgd import WorkoutCashFlow, discounted_workout_lgd


@dataclass(frozen=True)
class WorkoutEpisode:
    episode_id: str
    default_date: date
    resolution_date: date
    ead: float
    currency: str
    perspective: Literal["whole_loan", "institution"]
    ead_basis: str
    default_definition: str
    ledger_complete: bool
    finalization_verified: bool


@dataclass(frozen=True)
class LedgerEntry:
    episode_id: str
    transaction_id: str
    underlying_receipt_id: str
    payment_date: date
    amount: float
    currency: str
    kind: Literal["recovery", "cost"]
    category: Literal[
        "borrower", "collateral", "property_income", "insurance", "lender", "workout_cost"
    ]
    source: str
    observed: bool
    already_embedded: bool = False


def reconcile_workout(
    episode: WorkoutEpisode,
    entries: list[LedgerEntry],
    annual_discount_rate: float,
    rate_basis: str,
    expected_nominal_cash_loss: float | None = None,
    tolerance: float = 0.01,
) -> dict:
    """ACT/365.25, annual effective rate; expected loss must share the cash basis.

    Caller must verify completeness, EAD/default definitions and allocation.
    Source accounting loss is not an automatic reconciliation control total.
    """
    if not episode.ledger_complete or not episode.finalization_verified:
        raise ValueError("Complete finalized ledger required")
    if not all(
        [
            episode.episode_id,
            episode.currency,
            episode.ead_basis,
            episode.default_definition,
            rate_basis,
        ]
    ):
        raise ValueError("Explicit episode, currency, EAD/default and rate basis required")
    if episode.perspective not in {"whole_loan", "institution"}:
        raise ValueError("Unknown loss perspective")
    if episode.default_date > episode.resolution_date:
        raise ValueError("Resolution precedes default")
    if not isfinite(tolerance) or tolerance < 0:
        raise ValueError("Invalid reconciliation tolerance")
    if not entries:
        raise ValueError(
            "Explicit ledger entries required; empty ledger is not proof of zero recovery"
        )
    transactions, receipts = set(), set()
    flows = []
    recovery = costs = 0.0
    for entry in entries:
        if entry.episode_id != episode.episode_id or entry.currency != episode.currency:
            raise ValueError("Episode or currency mismatch")
        if not entry.transaction_id or not entry.underlying_receipt_id or not entry.source:
            raise ValueError("Transaction, underlying receipt and source required")
        if entry.transaction_id in transactions or entry.underlying_receipt_id in receipts:
            raise ValueError("Duplicate transaction or underlying receipt")
        transactions.add(entry.transaction_id)
        receipts.add(entry.underlying_receipt_id)
        if not entry.observed or entry.already_embedded:
            raise ValueError("Assumed or already embedded cash flows prohibited")
        if not episode.default_date <= entry.payment_date <= episode.resolution_date:
            raise ValueError("Payment outside workout interval")
        if not isfinite(entry.amount) or entry.amount < 0:
            raise ValueError("Amounts must be finite and nonnegative")
        if entry.kind not in {"recovery", "cost"}:
            raise ValueError("Unknown cash-flow kind")
        valid_recovery = {"borrower", "collateral", "property_income", "insurance", "lender"}
        if (entry.kind == "recovery" and entry.category not in valid_recovery) or (
            entry.kind == "cost" and entry.category != "workout_cost"
        ):
            raise ValueError("Category and cash-flow kind mismatch")
        if episode.perspective == "whole_loan" and entry.category == "lender":
            raise ValueError("Lender loss allocation is not whole-loan borrower recovery")
        years = (entry.payment_date - episode.default_date).days / 365.25
        flows.append(WorkoutCashFlow(entry.amount, years, entry.kind))
        if entry.kind == "recovery":
            recovery += entry.amount
        else:
            costs += entry.amount
    nominal_loss = episode.ead - recovery + costs
    if expected_nominal_cash_loss is not None and (
        not isfinite(expected_nominal_cash_loss)
        or abs(nominal_loss - expected_nominal_cash_loss) > tolerance
    ):
        raise ValueError("Nominal cash-loss reconciliation failed")
    lgd = discounted_workout_lgd(episode.ead, flows, annual_discount_rate)
    return {
        "episode_id": episode.episode_id,
        "perspective": episode.perspective,
        "currency": episode.currency,
        "ead": episode.ead,
        "nominal_recovery": recovery,
        "nominal_cost": costs,
        "nominal_cash_loss": nominal_loss,
        "nominal_cash_lgd": nominal_loss / episode.ead,
        "discounted_economic_lgd_raw": lgd,
        "discounted_net_recovery": episode.ead * (1 - lgd),
        "annual_discount_rate": annual_discount_rate,
        "rate_basis": rate_basis,
        "day_count": "ACT/365.25",
        "compounding": "annual_effective",
        "transaction_count": len(entries),
        "cash_control_reconciled": expected_nominal_cash_loss is not None,
    }
