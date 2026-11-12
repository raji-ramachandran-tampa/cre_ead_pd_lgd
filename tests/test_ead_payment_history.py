import pytest

from cre_expected_loss.models.ead_payment_history import inferred_payment, project_payment


def test_reconstructs_known_monthly_payment_and_forward_recursion():
    rate = 0.06
    balance = 100000.0
    payment = 700.0
    history = [balance]
    for _ in range(3):
        history.append(history[-1] * (1 + rate / 12) - payment)
    recovered = inferred_payment(history, rate)
    assert recovered == pytest.approx(payment, abs=1e-8)
    expected = history[-1]
    for _ in range(12):
        expected = expected * (1 + rate / 12) - payment
    assert project_payment(history[-1], rate, recovered, 12) == pytest.approx(expected)


def test_zero_rate_and_io_payment():
    assert inferred_payment([1000, 990, 980, 970], 0) == 10
    assert project_payment(970, 0, 10, 12) == 850
    assert inferred_payment([1000] * 4, 0.06) == pytest.approx(5)
    assert project_payment(1000, 0.06, 5, 12) == pytest.approx(1000)


@pytest.mark.parametrize(
    "history",
    [[1000, 990, 800, 790], [1000, 990, 980], [1000, 990, float("nan"), 970], [1000, 990, 980, 0]],
)
def test_bad_or_unstable_history_is_rejected(history):
    with pytest.raises(ValueError):
        inferred_payment(history, 0)


def test_exhaustion_is_not_silently_replaced_by_payoff():
    with pytest.raises(ValueError, match="exhausted"):
        project_payment(10, 0, 20, 1)
    with pytest.raises(ValueError):
        project_payment(10, 0, 1, 1.5)
    with pytest.raises(ValueError):
        inferred_payment([100] * 4, float("nan"))
