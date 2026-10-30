import numpy as np
import pandas as pd
import pytest

from cre_expected_loss.models.ead_diagnostics import fit_fold
from cre_expected_loss.models.ead_research import FEATURES


def sample(start, year, n=40):
    frame = pd.DataFrame({name: np.linspace(0.1, 1, n) for name in FEATURES})
    frame["loan_id"] = [f"synthetic_{start + i}" for i in range(n)]
    frame["onset_date"] = pd.Timestamp(f"{year}-01-31")
    frame["anchor_upb"] = 100000.0
    frame["onset_scheduled_upb"] = 98000.0 + np.arange(n) * 10
    return frame


def test_evaluation_outcomes_do_not_affect_fold_prediction():
    train = sample(0, 2010)
    test = sample(100, 2012)
    before = fit_fold(train, test)
    test["onset_scheduled_upb"] *= 0.5
    np.testing.assert_allclose(before, fit_fold(train, test), rtol=0, atol=0)


def test_fold_rejects_overlap():
    with pytest.raises(ValueError, match="Overlapping"):
        fit_fold(sample(0, 2010), sample(0, 2012))


def test_fold_rejects_future_training():
    with pytest.raises(ValueError, match="precede"):
        fit_fold(sample(0, 2013), sample(100, 2012))
