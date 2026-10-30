import pandas as pd
import pytest

from cre_expected_loss.models.ead_episodes import observed_episodes


def history(dates, status):
    return pd.DataFrame(
        {
            "loan_id": ["synthetic"] * len(dates),
            "reporting_date": pd.to_datetime(dates),
            "payment_status": status,
            "sdq_indicator": ["Y" if s.startswith("60") else "N" for s in status],
            "current_upb": [100.0] * len(dates),
        }
    )


def test_non_sdq_transition_is_not_called_cure():
    result = observed_episodes(
        history(
            ["2020-01-31", "2020-02-29", "2020-03-31", "2020-04-30"],
            ["Current", "60-89 Days Delinquent", "30-59 Days Delinquent", "60-89 Days Delinquent"],
        )
    )
    assert len(result) == 2
    assert result.iloc[0].end_observation == "return_to_non_sdq"
    assert result.iloc[0].following_payment_status == "30-59 Days Delinquent"
    assert not result.left_boundary_uncertain.any()


def test_gap_does_not_imply_continuous_spell():
    result = observed_episodes(history(["2020-01-31", "2020-03-31"], ["60-89 Days Delinquent"] * 2))
    assert len(result) == 2
    assert result.left_boundary_uncertain.all()
    assert result.iloc[0].end_observation == "history_gap"


def test_duplicate_and_unknown_status_fail():
    frame = history(["2020-01-31"], ["Current"])
    with pytest.raises(ValueError, match="duplicate"):
        observed_episodes(pd.concat([frame, frame]))
    frame.loc[0, "payment_status"] = "unknown"
    with pytest.raises(ValueError, match="Unknown"):
        observed_episodes(frame)
