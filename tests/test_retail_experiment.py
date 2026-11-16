import numpy as np
import pandas as pd

from cre_expected_loss.retail_ead.experiment import (
    FEATURES,
    add_features,
    fit_direct,
    held_out,
    predict_direct,
)


def test_group_assignment_is_stable_and_shared_across_horizons():
    groups = [f"synthetic_application_{i}" for i in range(200)]
    initial = {g: held_out(g) for g in groups}
    assert 0 < sum(initial.values()) < len(groups)
    assert all(initial[g] == held_out(g) for g in reversed(groups))


def test_feature_history_stops_at_anchor():
    h = pd.DataFrame(
        {
            "account_id": [1] * 12,
            "application_link": ["synthetic_app"] * 12,
            "month_index": range(-12, 0),
            "drawn_balance": np.arange(12) + 100.0,
            "drawings": np.arange(12) + 1.0,
            "payments": np.arange(12) + 2.0,
        }
    )
    p = pd.DataFrame(
        [
            {
                "account_id": 1,
                "event_month": -1,
                "horizon_months": 6,
                "anchor_balance": 105.0,
                "anchor_limit": 300.0,
                "event_balance": 111.0,
            }
        ]
    )
    before = add_features(p, h)
    h.loc[h.month_index.gt(-7), ["drawn_balance", "drawings", "payments"]] = 1e9
    after = add_features(p, h)
    pd.testing.assert_frame_equal(before[FEATURES], after[FEATURES])


def test_direct_prediction_needs_no_evaluation_target_and_stays_nonnegative():
    n = 80
    train = pd.DataFrame({name: np.linspace(0, 1, n) for name in FEATURES})
    train["anchor_limit"] = 300.0
    train["event_balance"] = np.linspace(0, 30, n)
    model = fit_direct(train)
    x = train[FEATURES + ["anchor_limit"]].copy()
    values = predict_direct(model, x)
    assert np.isfinite(values).all()
    assert values.ge(0).all()


def test_config_threshold_and_explicit_override(tmp_path):
    import pytest

    from cre_expected_loss.retail_ead.experiment import load_settings

    config = tmp_path / "retail.yaml"
    config.write_text("default_proxy:\n  threshold_days: 60\nhorizons_months: [3, 6, 12]\n")
    assert load_settings(config) == (60, (3, 6, 12))
    assert load_settings(config, 90) == (90, (3, 6, 12))
    with pytest.raises(ValueError):
        load_settings(config, 0)
    with pytest.raises(ValueError):
        load_settings(config, True)


def test_no_threshold_crossings_produce_a_valid_empty_run(tmp_path):
    from cre_expected_loss.retail_ead.experiment import run

    raw = tmp_path / "raw/home-credit-default-risk-2018"
    raw.mkdir(parents=True)
    pd.DataFrame(
        {
            "SK_ID_PREV": [1, 1],
            "SK_ID_CURR": [2, 2],
            "MONTHS_BALANCE": [-2, -1],
            "AMT_BALANCE": [10.0, 20.0],
            "AMT_CREDIT_LIMIT_ACTUAL": [100.0, 100.0],
            "SK_DPD": [0, 0],
            "SK_DPD_DEF": [0, 0],
            "AMT_DRAWINGS_CURRENT": [1.0, 1.0],
            "AMT_PAYMENT_TOTAL_CURRENT": [1.0, 1.0],
        }
    ).to_csv(raw / "credit_card_balance.csv", index=False)
    (raw / "HomeCredit_columns_description.csv").write_text("synthetic_dictionary")
    output = tmp_path / "output"
    run(tmp_path, output, dpd_threshold=60)
    import json

    report = json.loads((output / "report.json").read_text())
    assert report["delinquency_threshold_days"] == 60
    assert all(d["event_accounts"] == 0 for d in report["definitions"])
    assert report["reload_verified_held_out_horizon_cases"] == 0
