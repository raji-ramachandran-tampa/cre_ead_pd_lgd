import numpy as np
import pandas as pd
import pytest
import joblib
from cre_expected_loss.models.lgd_signed_hurdle import SignedHurdle, fit_hurdle, predict_hurdle


def frame():
    return pd.DataFrame(
        {
            "acquisition_ltv": [60.0] * 40,
            "underwritten_dscr": [1.4] * 40,
            "log_acquisition_upb": [14.0] * 40,
            "property_type": ["Multifamily"] * 40,
            "loss_sharing_type": ["Standard DUS"] * 40,
            "signed_ratio": [-4.0] * 20 + [0.0] * 10 + [2.0] * 10,
        }
    )


def test_probability_recombination_zero_and_uncapped_severity():
    data = frame()
    model = fit_hurdle(data)
    p = predict_hurdle(model, data)
    np.testing.assert_allclose(p[["p_zero", "p_positive", "p_negative"]].sum(axis=1), 1.0)
    assert model.zero_probability == 0.25
    np.testing.assert_allclose(p.positive_magnitude, 2.0, rtol=1e-5)
    np.testing.assert_allclose(p.negative_magnitude, 4.0, rtol=1e-5)
    np.testing.assert_allclose(p.prediction, -1.5, atol=1e-4)
    np.testing.assert_allclose(
        p.prediction, p.p_positive * p.positive_magnitude - p.p_negative * p.negative_magnitude
    )


def test_saved_components_reproduce_with_unseen_category(tmp_path):
    data = frame()
    model = fit_hurdle(data)
    path = tmp_path / "model.joblib"
    joblib.dump(vars(model), path)
    loaded = SignedHurdle(**joblib.load(path))
    data["property_type"] = "Unseen"
    data["signed_ratio"] = 100.0
    np.testing.assert_allclose(predict_hurdle(model, data), predict_hurdle(loaded, data))
    assert loaded.zero_probability == 0.25


def test_insufficient_sign_or_invalid_targets_fail():
    data = frame()
    data["signed_ratio"] = 1.0
    with pytest.raises(ValueError, match="positive and three negative"):
        fit_hurdle(data)
    data = frame()
    data.loc[0, "signed_ratio"] = np.nan
    with pytest.raises(ValueError, match="finite"):
        fit_hurdle(data)
