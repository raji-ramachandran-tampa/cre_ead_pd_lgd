import numpy as np
import pandas as pd
import pytest
from cre_expected_loss.models.lgd_signed_model import parse_accounting, fit_signed, compare


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("($1,234.50)", -1234.5),
        ("$0.00", 0.0),
        ("-2", -2.0),
        ("($0.00)", 0.0),
        ("", None),
        ("abc", None),
        ("(12", None),
        ("NaN", None),
    ],
)
def test_signed_accounting(raw, expected):
    assert parse_accounting(raw) == expected


def frame():
    return pd.DataFrame(
        {
            "acquisition_ltv": [60.0] * 20,
            "underwritten_dscr": [1.4] * 20,
            "log_acquisition_upb": [14.0] * 20,
            "property_type": ["Multifamily"] * 20,
            "loss_sharing_type": ["Standard DUS"] * 20,
            "parsed_default": [100.0] * 20,
            "signed_ratio": [-2.0] * 10 + [0.0] * 5 + [1.0] * 5,
        }
    )


def test_signed_predictions_not_floored_and_train_only_benchmark():
    training = frame()
    test = frame()
    test["signed_ratio"] = 10.0
    test["property_type"] = "Unknown type"
    metrics, predictions = compare(training, test)
    np.testing.assert_allclose(predictions["mean_benchmark"], -0.75)
    assert (predictions["ridge_core"] < 0).all()
    assert np.isfinite(predictions["ridge_enriched"]).all()
    assert metrics["mean_benchmark"]["mean_actual"] == 10.0


def test_nonfinite_target_rejected():
    data = frame()
    data.loc[0, "signed_ratio"] = np.nan
    with pytest.raises(ValueError):
        fit_signed(data)
