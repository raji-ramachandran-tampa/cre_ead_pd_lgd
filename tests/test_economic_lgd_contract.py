from dataclasses import replace
from datetime import date

import pytest

from cre_expected_loss.models.economic_lgd_contract import (
    LedgerEntry,
    WorkoutEpisode,
    reconcile_workout,
)


def inputs():
    episode = WorkoutEpisode(
        "synthetic",
        date(2020, 1, 1),
        date(2022, 1, 1),
        100.0,
        "USD",
        "institution",
        "principal",
        "synthetic default",
        True,
        True,
    )
    entry = LedgerEntry(
        "synthetic",
        "sale",
        "receipt1",
        date(2021, 1, 1),
        80.0,
        "USD",
        "recovery",
        "collateral",
        "synthetic example",
        True,
    )
    return episode, entry


def test_cash_reconciliation_and_discounting():
    episode, entry = inputs()
    cost = replace(
        entry,
        transaction_id="expense",
        underlying_receipt_id="expense1",
        amount=5.0,
        payment_date=episode.default_date,
        kind="cost",
        category="workout_cost",
    )
    result = reconcile_workout(episode, [entry, cost], 0.05, "illustrative", 25.0)
    assert result["nominal_cash_lgd"] == 0.25
    assert result["discounted_economic_lgd_raw"] == pytest.approx(
        1 - (80 / 1.05 ** (366 / 365.25) - 5) / 100
    )
    with pytest.raises(ValueError, match="reconciliation"):
        reconcile_workout(episode, [entry, cost], 0.05, "illustrative", 20.0)


@pytest.mark.parametrize(
    "changes",
    [
        {"observed": False},
        {"already_embedded": True},
        {"currency": "EUR"},
        {"kind": "invalid"},
        {"payment_date": date(2019, 1, 1)},
    ],
)
def test_reject_unsupported_cashflows(changes):
    episode, entry = inputs()
    with pytest.raises(ValueError):
        reconcile_workout(episode, [replace(entry, **changes)], 0.05, "illustrative")


def test_completeness_duplicates_and_perspective():
    episode, entry = inputs()
    with pytest.raises(ValueError, match="finalized"):
        reconcile_workout(replace(episode, ledger_complete=False), [entry], 0.05, "illustrative")
    with pytest.raises(ValueError, match="Duplicate"):
        reconcile_workout(
            episode, [entry, replace(entry, transaction_id="different")], 0.05, "illustrative"
        )
    with pytest.raises(ValueError, match="whole-loan"):
        reconcile_workout(
            replace(episode, perspective="whole_loan"),
            [replace(entry, category="lender")],
            0.05,
            "illustrative",
        )


def test_gains_preserved_and_no_cashflows_not_assumed_zero():
    episode, entry = inputs()
    assert reconcile_workout(episode, [replace(entry, amount=120.0)], 0.0, "illustrative")[
        "discounted_economic_lgd_raw"
    ] == pytest.approx(-0.2)
    with pytest.raises(ValueError, match="empty ledger"):
        reconcile_workout(episode, [], 0.0, "illustrative")
