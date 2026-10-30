import pytest

from cre_expected_loss.models.ead_amortization import scheduled_balance


def test_annuity_matches_payment_recursion():
    balance = 100000.0
    rate = 0.06 / 12
    payment = balance * rate / (1 - (1 + rate) ** -360)
    expected = balance
    for _ in range(12):
        expected = expected * (1 + rate) - payment
    assert scheduled_balance(balance, 0.06, 360, 12) == pytest.approx(expected)


def test_io_transition_zero_rate_and_completion():
    assert scheduled_balance(120, 0, 120, 12, 6) == pytest.approx(114)
    assert scheduled_balance(120, 0.05, 120, 12, 12) == 120
    assert scheduled_balance(120, 0.05, 12, 12) == 0


@pytest.mark.parametrize(
    "args",
    [
        (-1, 0.05, 12, 1),
        (100, -0.1, 12, 1),
        (100, 0.05, 0, 1),
        (100, 0.05, 12, 1.5),
        (100, float("nan"), 12, 1),
    ],
)
def test_invalid_inputs(args):
    with pytest.raises(ValueError):
        scheduled_balance(*args)


def test_schedule_predictors_do_not_depend_on_outcome_balance():
    import pandas as pd

    from cre_expected_loss.models.ead_research import FEATURES, prepare

    frame = pd.DataFrame(
        [
            {
                "anchor_date": pd.Timestamp("2017-01-31"),
                "onset_date": pd.Timestamp("2018-01-31"),
                "maturity_date": pd.Timestamp("2027-01-31"),
                "modification_date": pd.NaT,
                "interest_type": "Fixed",
                "loan_age": 24.0,
                "note_rate": 5.0,
                "amortization_months": 360.0,
                "anchor_upb": 100000.0,
                "io_months": 12.0,
                "amortization_type": "Interest Only/Amortizing/Balloon",
                "io_end_date": pd.Timestamp("2016-01-31"),
                "horizon_months": 12,
                "onset_scheduled_upb": 98000.0,
            }
        ]
    )
    before = prepare(frame)
    frame.loc[0, "onset_scheduled_upb"] = 50000
    after = prepare(frame)
    pd.testing.assert_frame_equal(before[FEATURES], after[FEATURES])
    frame.loc[0, "maturity_date"] = pd.Timestamp("2018-01-31")
    assert prepare(frame).schedule_status.iloc[0] == "at_or_beyond_maturity"
