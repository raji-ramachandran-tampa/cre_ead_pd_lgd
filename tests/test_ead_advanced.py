import numpy as np
import pandas as pd
import pytest

from cre_expected_loss.models.ead_advanced import (
    assert_temporal,
    bounds,
    conformal_radius,
    fit_residual,
    prediction,
    residual_target,
)
from cre_expected_loss.models.ead_research import FEATURES


class ConstantModel:
    def __init__(self, value):
        self.value = value

    def predict(self, x):
        return np.full(len(x), self.value)


def frame(n=80):
    data = pd.DataFrame({name: np.linspace(0.1, 1, n) for name in FEATURES})
    data["anchor_upb"] = 100.0
    data["io_clock_sensitivity"] = 98.0
    data["onset_scheduled_upb"] = 98.0 + np.linspace(0, 0.2, n)
    data["horizon_months"] = 12
    data["remaining_io"] = 0
    data["loan_id"] = [f"synthetic_{i}" for i in range(n)]
    data["onset_date"] = pd.Timestamp("2010-01-31")
    return data


def test_calibration_order_statistic_and_input_validation():
    assert conformal_radius(np.arange(9), 0.1) == 8
    with pytest.raises(ValueError, match="Insufficient"):
        conformal_radius([0, 1], 0.1)
    with pytest.raises(ValueError, match="nonnegative"):
        conformal_radius([-1] * 10)
    with pytest.raises(ValueError):
        conformal_radius([0] * 10, 1)


def test_guard_and_quantile_envelope():
    data = frame(2)
    data.loc[1, "remaining_io"] = 12
    lo, hi, cross = bounds({"q05": ConstantModel(0.02), "q95": ConstantModel(-0.01)}, data, 0.005)
    assert cross == 1  # IO residual forecasts are structurally zero
    assert lo[0] == pytest.approx(96.5)
    assert hi[0] == pytest.approx(100.5)
    assert lo[1] == hi[1] == 100
    assert prediction(ConstantModel(-0.01), data)[1] == 100
    with pytest.raises(ValueError):
        bounds({"q05": ConstantModel(0), "q95": ConstantModel(0)}, data, -1)


def test_residual_fit_does_not_read_evaluation_outcome():
    train = frame()
    test = frame(10)
    np.testing.assert_allclose(residual_target(train), (train.onset_scheduled_upb - 98) / 100)
    model = fit_residual(train)
    before = prediction(model, test)
    test["onset_scheduled_upb"] *= 0.5
    np.testing.assert_array_equal(before, prediction(model, test))


def test_temporal_and_overlap_contracts():
    a = frame(2)
    b = frame(2)
    with pytest.raises(ValueError, match="Overlapping"):
        assert_temporal(a, b)
    b.loan_id = "another" + b.loan_id
    with pytest.raises(ValueError, match="Nonchronological"):
        assert_temporal(a, b)
    b.onset_date = pd.Timestamp("2012-01-31")
    assert_temporal(a, b)
