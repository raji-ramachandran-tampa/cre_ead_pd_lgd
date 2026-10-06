import pytest

from cre_expected_loss.models.lgd_discounted_proxy import terminal_recovery_proxy


def test_zero_rate_reconciles_and_timing_changes_value():
    assert terminal_recovery_proxy(100, 80, 5, 1, 2, 0, 0) == pytest.approx(0.25)
    assert terminal_recovery_proxy(100, 80, 5, 1, 2, 0, 0.05) == pytest.approx(
        1 - (80 / 1.05**2 - 5) / 100
    )
    assert terminal_recovery_proxy(100, 80, 5, 0, 0, 0, 0) == pytest.approx(0.2)


def test_signed_values_and_invalid_allocation():
    assert terminal_recovery_proxy(100, 120, 0, 1, 0, 0, 0) == pytest.approx(-0.2)
    with pytest.raises(ValueError, match="allocation"):
        terminal_recovery_proxy(100, 80, 5, 1.1, 2, 0, 0.05)
