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
