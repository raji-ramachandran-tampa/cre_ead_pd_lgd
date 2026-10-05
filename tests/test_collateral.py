import pytest
from cre_expected_loss.models.collateral import (
    SecuredClaim,
    SecurityInterest,
    CollateralSale,
    ExternalRecovery,
    ProRataLossSharing,
    allocate_collateral,
    collateral_workout_lgd,
    allocate_positive_nominal_loss,
)


def sale(proceeds=100.0, costs=10.0, time=1.0, order=0, links=None, property_id="P"):
    return CollateralSale(
        property_id,
        proceeds,
        costs,
        time,
        order,
        tuple(links or [SecurityInterest("senior", 1), SecurityInterest("junior", 2)]),
    )


def test_senior_priority_and_property_reconciliation():
    r = allocate_collateral([SecuredClaim("senior", 80.0), SecuredClaim("junior", 50.0)], [sale()])
    assert [a.amount for a in r.allocations] == [80.0, 10.0]
    assert r.unrecovered_by_claim == {"senior": 0.0, "junior": 40.0}
    assert r.property_reconciliations["P"]["allocated_recovery"] == 90.0
    assert collateral_workout_lgd(r, "junior", 50.0, 0.1) == pytest.approx(1 - 10 / 1.1 / 50)


def test_pari_passu_and_cross_property_no_double_recovery():
    claims = [SecuredClaim("A", 60.0), SecuredClaim("B", 40.0)]
    links = [SecurityInterest("A", 1), SecurityInterest("B", 1)]
    r = allocate_collateral(
        claims, [sale(50.0, 0.0, 1.0, 0, links, "P1"), sale(80.0, 0.0, 2.0, 1, links, "P2")]
    )
    assert [a.amount for a in r.allocations] == [30.0, 20.0, 30.0, 20.0]
    assert r.residual_by_property["P2"] == 30.0
    assert sum(a.amount for a in r.allocations) == 100.0


def test_separate_benefits_costs_and_uncapped_economic_lgd():
    from cre_expected_loss.models.lgd import WorkoutCashFlow

    r = allocate_collateral(
        [SecuredClaim("A", 100.0)], [sale(80.0, 0.0, 0.0, 0, [SecurityInterest("A", 1)])]
    )
    lgd = collateral_workout_lgd(
        r,
        "A",
        100.0,
        0.0,
        external_recoveries=[ExternalRecovery("insurance", 30.0, 0.0)],
        separate_costs=[WorkoutCashFlow(5.0, 0.0, "cost")],
    )
    assert lgd == pytest.approx(-0.05)
    with pytest.raises(ValueError, match="Unique external"):
        collateral_workout_lgd(
            r,
            "A",
            100.0,
            0.0,
            external_recoveries=[ExternalRecovery("x", 1.0, 0.0), ExternalRecovery("x", 1.0, 0.0)],
        )
    with pytest.raises(ValueError, match="Already-net"):
        collateral_workout_lgd(r, "A", 100.0, 0.0, input_basis="source_already_net")


def test_loss_sharing_cap_and_reconciliation():
    assert allocate_positive_nominal_loss(100.0, ProRataLossSharing(0.5, 20.0)) == {
        "lender_loss": 20.0,
        "institution_loss": 80.0,
    }
    with pytest.raises(ValueError):
        allocate_positive_nominal_loss(-1.0, ProRataLossSharing(0.5, None))


def test_invalid_contracts_fail():
    claims = [SecuredClaim("senior", 80.0), SecuredClaim("junior", 50.0)]
    for invalid in [
        sale(-1.0),
        sale(5.0, 10.0),
        sale(time=-1.0),
        sale(links=[SecurityInterest("missing", 1)]),
        sale(links=[SecurityInterest("senior", 1), SecurityInterest("senior", 2)]),
    ]:
        with pytest.raises(ValueError):
            allocate_collateral(claims, [invalid])
    with pytest.raises(ValueError):
        allocate_collateral(claims, [sale(), sale(property_id="P2")])
