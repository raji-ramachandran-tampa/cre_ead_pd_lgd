import numpy as np
import pandas as pd
import pytest

from cre_expected_loss.retail_ead.audit import run
from cre_expected_loss.retail_ead.targets import conversion_factor, proxy_pairs


def panel():
    return pd.DataFrame(
        {
            "account_id": ["synthetic_card"] * 4,
            "month_index": [-4, -3, -2, -1],
            "drawn_balance": [100.0, 120.0, 160.0, 200.0],
            "credit_limit": [300.0] * 4,
            "days_past_due": [0, 0, 30, 90],
        }
    )


def test_ccf_is_not_clipped_and_zero_undrawn_is_undefined():
    assert conversion_factor(100, 300, 200) == 0.5
    assert conversion_factor(100, 300, 400) == 1.5
    assert conversion_factor(100, 300, 50) == -0.25
    assert np.isnan(conversion_factor(100, 100, 150))
    with pytest.raises(ValueError):
        conversion_factor(100, 300, float("nan"))


def test_exact_horizon_and_same_account_event():
    result = proxy_pairs(panel(), horizons=(3,))
    assert result.iloc[0].eligibility == "eligible_delinquency_proxy"
    assert result.iloc[0].ccf == 0.5
    assert result.iloc[0].anchor_balance == 100


def test_missing_history_and_left_censoring_are_retained():
    p = panel().drop(index=1)
    assert proxy_pairs(p, (3,)).iloc[0].eligibility == "history_gap"
    p = panel().iloc[-1:]
    assert proxy_pairs(p, (3,)).iloc[0].eligibility == "left_censored_event"


def test_duplicate_keys_fail_and_fully_drawn_ead_row_remains():
    p = panel()
    with pytest.raises(ValueError, match="duplicate"):
        proxy_pairs(pd.concat([p, p]))
    p.loc[0, "credit_limit"] = 100
    row = proxy_pairs(p, (3,)).iloc[0]
    assert row.eligibility == "eligible_delinquency_proxy"
    assert np.isnan(row.ccf)
    assert row.ccf_status == "fully_drawn_or_overlimit"


def test_audit_on_synthetic_original_schema(tmp_path):
    source = tmp_path / "raw"
    source.mkdir()
    pd.DataFrame(
        {
            "SK_ID_PREV": [1, 1],
            "SK_ID_CURR": [2, 2],
            "MONTHS_BALANCE": [-2, -1],
            "AMT_BALANCE": [100, 200],
            "AMT_CREDIT_LIMIT_ACTUAL": [300, 300],
            "SK_DPD": [0, 90],
            "SK_DPD_DEF": [0, 90],
        }
    ).to_csv(source / "credit_card_balance.csv", index=False)
    (source / "HomeCredit_columns_description.csv").write_text(
        "synthetic_fixture_not_official_dictionary\n"
    )
    report = run(source, tmp_path / "output")
    assert report["quality"]["rows_count"] == 2
    assert report["quality"]["accounts"] == 1
    assert report["quality"]["candidate_90dpd_rows"] == 1
    assert report["dictionary_semantics_reviewed"] is False
    with pytest.raises(FileExistsError):
        run(source, tmp_path / "output")
