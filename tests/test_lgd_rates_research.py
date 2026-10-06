import numpy as np
import pandas as pd
import pytest

from cre_expected_loss.models.lgd_rates_research import attach_rates


def write_rates(root):
    dates = pd.date_range("2000-01-01", periods=9, freq="MS")
    pd.DataFrame({"observation_date": dates, "value": np.arange(9) + 2.0}).to_csv(
        root / "DGS10.csv", index=False
    )
    pd.DataFrame({"observation_date": dates, "value": 1.5}).to_csv(
        root / "BAA10YM.csv", index=False
    )


def test_rate_units_change_and_backward_lag(tmp_path):
    write_rates(tmp_path)
    f = pd.DataFrame({"feature_date": pd.to_datetime(["2000-08-31", "2000-09-01", "1999-12-01"])})
    result = attach_rates(f, tmp_path).set_index("feature_date")
    assert result.loc["2000-08-31", "treasury_10y"] == 0.07
    assert result.loc["2000-09-01", "treasury_10y"] == 0.08
    assert result.loc["2000-09-01", "baa_treasury_spread"] == 0.015
    assert result.loc["2000-09-01", "treasury_change_6m"] == pytest.approx(0.06)
    assert pd.isna(result.loc["1999-12-01", "treasury_10y"])
    longer = attach_rates(f, tmp_path, 3).set_index("feature_date")
    assert longer.loc["2000-09-01", "treasury_10y"] == 0.07


def test_daily_monthly_mean_excludes_future_month(tmp_path):
    write_rates(tmp_path)
    pd.DataFrame(
        {"observation_date": ["2000-01-01", "2000-01-15", "2000-02-01"], "value": [2.0, 4.0, 99.0]}
    ).to_csv(tmp_path / "DGS10.csv", index=False)
    f = pd.DataFrame({"feature_date": pd.to_datetime(["2000-03-01"])})
    result = attach_rates(f, tmp_path)
    assert result.treasury_10y.iloc[0] == 0.03
    assert result.treasury_10y_reference_date.iloc[0] == pd.Timestamp("2000-01-01")


def test_duplicate_observations_rejected(tmp_path):
    write_rates(tmp_path)
    pd.DataFrame({"observation_date": ["2000-01-01"] * 2, "value": [2.0, 3.0]}).to_csv(
        tmp_path / "DGS10.csv", index=False
    )
    with pytest.raises(ValueError, match="Duplicate"):
        attach_rates(pd.DataFrame({"feature_date": pd.to_datetime(["2000-03-01"])}), tmp_path)
