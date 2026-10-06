import pytest

from cre_expected_loss.models.lgd_accounting_bridge import discounted_accounting_bridge


def test_accounting_reconciliation_and_positive_net_equivalent():
    assert discounted_accounting_bridge(-0.2, 3, 0) == pytest.approx(-0.2)
    assert discounted_accounting_bridge(0.2, 2, 0.05) == pytest.approx(1 - 0.8 / 1.05**2)


def test_negative_net_equivalent_is_preserved_not_clipped():
    assert discounted_accounting_bridge(1.2, 2, 0.05) == pytest.approx(1 + 0.2 / 1.05**2)
    assert discounted_accounting_bridge(1.2, 2, 0.05) < 1.2


def test_invalid_duration():
    with pytest.raises(ValueError):
        discounted_accounting_bridge(0.2, -1, 0.05)
