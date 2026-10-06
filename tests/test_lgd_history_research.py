import numpy as np
import pandas as pd
import pytest

from cre_expected_loss.models.lgd_history_research import CATS, CORE, derive_features, fit_history


def inputs():
    cases = pd.DataFrame(
        [
            {
                "loan_id": "synthetic",
                "credit_event_date": pd.Timestamp("2021-03-01"),
                "feature_date": pd.Timestamp("2021-02-01"),
                "earliest_reporting_date": pd.Timestamp("2020-12-01"),
                "original_upb": 100.0,
                "property_count": 1.0,
                "lien_position": "First",
                "underwritten_dscr": 1.5,
                "property_type": "MF",
                "loss_sharing_type": "DUS",
            }
        ]
    )
    monthly = pd.DataFrame(
        {
            "loan_id": "synthetic",
            "reporting_date": pd.to_datetime(["2020-12-01", "2021-01-01", "2021-02-01"]),
            "payment_status": ["Current", "60-89 Days Delinquent", "90+ Days Delinquent"],
            "sdq_indicator": ["N", "Y", "Y"],
            "note_date": pd.Timestamp("2015-01-01"),
            "maturity_date": pd.Timestamp("2025-01-01"),
            "current_upb": [95.0, 94.0, 93.0],
            "note_rate": 5.0,
            "original_interest_rate": 5.0,
            "amortization_type": "Balloon",
            "interest_type": "Fixed",
        }
    )
    annual = pd.DataFrame(
        {
            "loan_id": "synthetic",
            "dscr_year": [2017, 2018, 2019, 2020],
            "annual_dscr": [1.4, 1.3, 1.2, 999.0],
        }
    )
    return cases, monthly, annual


def test_anchors_and_annual_years_exclude_future_information():
    cases, monthly, annual = inputs()
    f = derive_features(cases, monthly, annual, 2).set_index("scope")
    early = f.loc["before_first_observed_sdq"]
    late = f.loc["pre_disposition_update"]
    assert early.anchor_date == pd.Timestamp("2020-12-01")
    assert early.sdq_months_observed == 0
    assert early.historical_dscr == 1.3
    assert late.historical_dscr == 1.2
    assert late.sdq_months_observed == 2
    assert late.balance_to_original == 0.93
    future = monthly.tail(1).copy()
    future["reporting_date"] = pd.Timestamp("2022-01-01")
    future["current_upb"] = 999999.0
    actual = derive_features(cases, pd.concat([monthly, future]), annual, 2)
    pd.testing.assert_frame_equal(f.reset_index(), actual, check_like=True)


def test_conflicting_annual_values_remain_missing():
    cases, monthly, annual = inputs()
    extra = annual[annual.dscr_year.eq(2019)].copy()
    extra["annual_dscr"] = 9.0
    f = derive_features(cases, monthly, pd.concat([annual, extra]), 2)
    row = f[f.scope.eq("pre_disposition_update")].iloc[0]
    assert pd.isna(row.historical_dscr)
    assert row.historical_dscr_missing == 1


def test_duplicate_monthly_rows_and_invalid_lag_rejected():
    cases, monthly, annual = inputs()
    with pytest.raises(ValueError, match="Duplicate monthly"):
        derive_features(cases, pd.concat([monthly, monthly.head(1)]), annual)
    with pytest.raises(ValueError, match="DSCR lag"):
        derive_features(cases, monthly, annual, 0)


def test_training_imputation_does_not_use_evaluation_values():
    f = pd.DataFrame(
        {
            "acquisition_ltv": np.arange(20) + 50.0,
            "underwritten_dscr": 1.2,
            "log_acquisition_upb": 15.0,
            "property_type": "MF",
            "loss_sharing_type": "DUS",
            "historical_dscr": [np.nan] * 10 + [1.0] * 10,
            "signed_ratio": np.r_[np.repeat(-1.2, 10), np.repeat(0.4, 10)],
        }
    )
    model = fit_history(f, CORE + ["historical_dscr"], CATS)
    assert model[0].named_transformers_["numeric"][0].statistics_[-1] == 1.0
    evaluation = f.copy()
    evaluation["historical_dscr"] = 999.0
    assert np.isfinite(model.predict(evaluation)).all()
    assert model[0].named_transformers_["numeric"][0].statistics_[-1] == 1.0
    hurdle = fit_history(f, CORE + ["historical_dscr"], CATS, True)
    assert hurdle.negative_model[0].named_transformers_["numeric"][0].statistics_[-1] == 0.0
