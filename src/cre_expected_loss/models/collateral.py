"""Proposed deterministic collateral waterfall; inputs require verified contracts."""

from __future__ import annotations
from dataclasses import dataclass
from math import isfinite, fsum
from typing import Iterable
from .lgd import WorkoutCashFlow, discounted_workout_lgd


def nonnegative(value: float, name: str) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


@dataclass(frozen=True)
class SecuredClaim:
    claim_id: str
    amount: float


@dataclass(frozen=True)
class SecurityInterest:
    claim_id: str
    rank: int


@dataclass(frozen=True)
class CollateralSale:
    property_id: str
    gross_proceeds: float
    priority_selling_costs: float
    years_after_default: float
    allocation_order: int
    interests: tuple[SecurityInterest, ...]


@dataclass(frozen=True)
class RecoveryAllocation:
    property_id: str
    claim_id: str
    rank: int
    amount: float
    years_after_default: float


@dataclass(frozen=True)
class CollateralResult:
    allocations: tuple[RecoveryAllocation, ...]
    residual_by_property: dict[str, float]
    unrecovered_by_claim: dict[str, float]
    property_reconciliations: dict[str, dict[str, float]]


def allocate_collateral(
    claims: Iterable[SecuredClaim], sales: Iterable[CollateralSale]
) -> CollateralResult:
    """Apply contractual ranking, pari-passu ties and global claim balances.

    Same-rank interests share available proceeds pro rata to remaining claims.
    Sales process chronologically, then explicit allocation_order for ties.
    This tie order is a contractual input, not an inferred optimization; complex
    simultaneous cross-collateral waterfalls require a separate specification.
    Selling costs are deducted here once; they must not re-enter loan cash flows.
    """
    claims, sales = tuple(claims), tuple(sales)
    if not claims or not sales:
        raise ValueError("Claims and collateral sales are required")
    ids = [c.claim_id for c in claims]
    if any(not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("Unique claim IDs required")
    for c in claims:
        nonnegative(c.amount, "claim amount")
    property_ids = [s.property_id for s in sales]
    if any(not x for x in property_ids) or len(set(property_ids)) != len(property_ids):
        raise ValueError("Unique property IDs required")
    orders = [s.allocation_order for s in sales]
    if any(type(o) is not int or o < 0 for o in orders) or len(set(orders)) != len(orders):
        raise ValueError("Explicit unique nonnegative integer allocation orders required")
    for sale in sales:
        for value, name in [
            (sale.gross_proceeds, "gross proceeds"),
            (sale.priority_selling_costs, "selling costs"),
            (sale.years_after_default, "timing"),
        ]:
            nonnegative(value, name)
        if sale.priority_selling_costs > sale.gross_proceeds:
            raise ValueError(
                "Costs above proceeds require a separately funded expense specification"
            )
        links = [x.claim_id for x in sale.interests]
        if not links or len(set(links)) != len(links):
            raise ValueError("Unique security links per property required")
        for interest in sale.interests:
            if interest.claim_id not in ids:
                raise ValueError("Unknown secured claim")
            if type(interest.rank) is not int or interest.rank < 1:
                raise ValueError("Rank must be a positive integer")
    if set(ids) != {x.claim_id for s in sales for x in s.interests}:
        raise ValueError("Every claim needs at least one documented security interest")
    remaining = {c.claim_id: c.amount for c in claims}
    allocations = []
    residuals = {}
    reconciliations = {}
    for sale in sorted(sales, key=lambda s: (s.years_after_default, s.allocation_order)):
        available = sale.gross_proceeds - sale.priority_selling_costs
        distributed = 0.0
        for rank in sorted({x.rank for x in sale.interests}):
            peers = sorted([x.claim_id for x in sale.interests if x.rank == rank])
            total = fsum(remaining[x] for x in peers)
            payout = min(available, total)
            if total > 0 and payout > 0:
                for claim_id in peers:
                    amount = payout * (remaining[claim_id] / total)
                    remaining[claim_id] = max(0.0, remaining[claim_id] - amount)
                    allocations.append(
                        RecoveryAllocation(
                            sale.property_id, claim_id, rank, amount, sale.years_after_default
                        )
                    )
            available = max(0.0, available - payout)
            distributed += payout
        residuals[sale.property_id] = available
        reconciliations[sale.property_id] = {
            "gross_proceeds": sale.gross_proceeds,
            "selling_costs": sale.priority_selling_costs,
            "allocated_recovery": distributed,
            "unallocated_surplus": available,
        }
        if abs(
            sale.gross_proceeds - sale.priority_selling_costs - distributed - available
        ) > 1e-9 * max(1.0, sale.gross_proceeds):
            raise ArithmeticError("Property proceeds do not reconcile")
    return CollateralResult(tuple(allocations), residuals, remaining, reconciliations)


@dataclass(frozen=True)
class ExternalRecovery:
    """Verified benefit or non-collateral recovery with a unique source identifier."""

    source_id: str
    amount: float
    years_after_default: float


def collateral_workout_lgd(
    result: CollateralResult,
    claim_id: str,
    ead_at_default: float,
    annual_discount_rate: float,
    *,
    external_recoveries: Iterable[ExternalRecovery] = (),
    separate_costs: Iterable[WorkoutCashFlow] = (),
    input_basis: str = "gross_before_external_benefits",
) -> float:
    """Compute economic raw LGD; this does not reconcile Fannie reported net loss.

    Only additional loan costs belong in separate_costs, never property selling
    costs already deducted in the waterfall. Net source losses are rejected as
    a basis, preventing benefits from being applied to an already-net outcome.
    """
    if claim_id not in result.unrecovered_by_claim:
        raise ValueError("Unknown claim")
    if input_basis != "gross_before_external_benefits":
        raise ValueError(
            "Already-net inputs require a separate reconciliation; do not reapply benefits"
        )
    benefits = tuple(external_recoveries)
    costs = tuple(separate_costs)
    ids = [b.source_id for b in benefits]
    if any(not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("Unique external recovery source IDs required")
    flows = [
        WorkoutCashFlow(a.amount, a.years_after_default, "recovery")
        for a in result.allocations
        if a.claim_id == claim_id
    ]
    for b in benefits:
        nonnegative(b.amount, "external recovery")
        nonnegative(b.years_after_default, "external timing")
        flows.append(WorkoutCashFlow(b.amount, b.years_after_default, "recovery"))
    if any(c.kind != "cost" for c in costs):
        raise ValueError("Separate costs must be cost flows")
    return discounted_workout_lgd(ead_at_default, flows + list(costs), annual_discount_rate)


@dataclass(frozen=True)
class ProRataLossSharing:
    lender_fraction: float
    lender_cap: float | None


def allocate_positive_nominal_loss(gross_loss: float, rule: ProRataLossSharing) -> dict[str, float]:
    """Separate nominal contractual allocation interface, not a Fannie DUS rule.

    Caller supplies the verified contractual loss basis and contract parameters.
    Allocation amounts are not discounted reimbursements; their actual timing
    must be supplied separately before entering economic workout cash flows.
    """
    nonnegative(gross_loss, "gross nominal loss")
    if not isfinite(rule.lender_fraction) or not 0 <= rule.lender_fraction <= 1:
        raise ValueError("Lender fraction must be in [0,1]")
    if rule.lender_cap is not None:
        nonnegative(rule.lender_cap, "lender cap")
    lender = gross_loss * rule.lender_fraction
    if rule.lender_cap is not None:
        lender = min(lender, rule.lender_cap)
    return {"lender_loss": lender, "institution_loss": gross_loss - lender}
