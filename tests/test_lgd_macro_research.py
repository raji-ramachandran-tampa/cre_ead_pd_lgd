import numpy as np
import pandas as pd
import pytest

from cre_expected_loss.models.lgd_macro_research import attach_macro, fit, macro_panel


def test_transform_units_and_assumed_lags(tmp_path):
    dates = pd.date_range("2000-01-01", periods=24, freq="MS")
    pd.DataFrame({"date": dates, "value": 100 * np.exp(np.arange(24) * 0.01)}).to_csv(
        tmp_path / "CPIAUCSL.csv", index=False
    )
    pd.DataFrame({"date": ["2000-01-01", "2000-04-01"], "value": [10.0, -5.0]}).to_csv(
        tmp_path / "COMREPUSQ159N.csv", index=False
    )
    panel = macro_panel(tmp_path, 6)
    np.testing.assert_allclose(panel.cpi_log_change_6m, 0.06)
    row = panel[panel.cpi_assumed_available_date.eq("2000-09-01")].iloc[0]
    assert row.cre_price_yoy == 0.1
    assert row.cre_assumed_available_date == pd.Timestamp("2000-07-01")
    frame = pd.DataFrame(
        {
            "feature_date": pd.to_datetime(["2000-09-30"]),
            "credit_event_date": pd.to_datetime(["2000-10-31"]),
        }
    )
    joined = attach_macro(frame, panel)
    assert joined.cpi_assumed_available_date.iloc[0] == pd.Timestamp("2000-09-01")
    assert joined.cre_price_yoy.iloc[0] == 0.1


def test_reject_future_feature_date():
    frame = pd.DataFrame(
        {
            "feature_date": pd.to_datetime(["2020-02-01"]),
            "credit_event_date": pd.to_datetime(["2020-01-01"]),
        }
    )
    with pytest.raises(ValueError, match="pre-event"):
        attach_macro(frame, pd.DataFrame())


def test_macro_models_preserve_signed_outcomes_and_train_only_scaling():
    frame = pd.DataFrame(
        {
            "acquisition_ltv": np.arange(20) + 50.0,
            "underwritten_dscr": 1.2,
            "log_acquisition_upb": 15.0,
            "property_type": "MF",
            "loss_sharing_type": "DUS",
            "cpi_log_change_6m": np.linspace(-0.02, 0.05, 20),
            "signed_ratio": np.r_[np.repeat(-1.2, 10), np.repeat(0.4, 10)],
        }
    )
    model = fit(frame, ["cpi_log_change_6m"])
    assert model.predict(frame).min() < 0
    scaler = model[0].named_transformers_["numeric"][1]
    assert scaler.mean_[-1] == pytest.approx(frame.cpi_log_change_6m.mean())
    hurdle = fit(frame, ["cpi_log_change_6m"], True)
    assert hurdle.training_counts == {"positive": 10, "negative": 10, "zero": 0}
