"""Synthetic integration checks for outcome reconciliation, never live loan records."""

import pandas as pd
import pytest

from cre_expected_loss.models.lgd_reconciliation import reconcile_lgd


def rows():
    result = []
    for loan, amount, loss in [
        ("zero", 100, 0),
        ("missing", 100, None),
        ("tail", 100, 150),
        ("invalid", 0, 5),
    ]:
        for reporting in ["2017-12-01", "2018-02-01"]:
            result.append(
                {
                    "loan_id": loan,
                    "reporting_date": pd.Timestamp(reporting),
                    "first_credit_event_date": pd.Timestamp("2018-01-01"),
                    "credit_event_type": "Non-REO",
                    "liquidation_date": pd.Timestamp("2018-01-01"),
                    "liquidation_code": "Third Party Sale",
                    "default_amount": amount,
                    "lifetime_net_credit_loss_amount": loss,
                    "acquisition_ltv": 65.0,
                    "underwritten_dscr": 1.5,
                    "property_type": "Multifamily",
                    "property_state": "NY",
                }
            )
    return result


def test_missing_is_not_zero_and_raw_tails_survive(tmp_path):
    source = tmp_path / "monthly.parquet"
    pd.DataFrame(rows()).to_parquet(source)
    output = tmp_path / "output"
    report = reconcile_lgd(source, output)
    assert report["credit_event_loans"] == 4
    assert report["status_counts"]["research_eligible"] == 2
    frame = pd.read_parquet(output / "loan_reconciliation.parquet").set_index("loan_id")
    assert frame.loc["zero", "reported_loss_ratio"] == 0
    assert frame.loc["missing", "status"] == "missing_or_invalid_loss"
    assert pd.isna(frame.loc["missing", "reported_loss_ratio"])
    assert frame.loc["tail", "reported_loss_ratio"] == 1.5
    assert (frame.feature_date < frame.credit_event_date).all()
    with pytest.raises(FileExistsError):
        reconcile_lgd(source, output)


def test_conflicts_and_unverified_disposition_are_not_eligible(tmp_path):
    data = rows()
    data[0]["lifetime_net_credit_loss_amount"] = 2
    data[4]["liquidation_date"] = None
    data[5]["liquidation_date"] = None
    source = tmp_path / "monthly.parquet"
    pd.DataFrame(data).to_parquet(source)
    report = reconcile_lgd(source, tmp_path / "out")
    assert report["status_counts"]["conflicting_history"] == 1
    assert report["status_counts"]["unverified_disposition"] == 1


def test_duplicate_keys_fail_before_outputs(tmp_path):
    data = rows()
    source = tmp_path / "monthly.parquet"
    pd.DataFrame(data + data[:1]).to_parquet(source)
    with pytest.raises(ValueError, match="Duplicate"):
        reconcile_lgd(source, tmp_path / "out")
    assert not (tmp_path / "out").exists()
