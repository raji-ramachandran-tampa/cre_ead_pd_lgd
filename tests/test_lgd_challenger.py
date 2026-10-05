import numpy as np
import pandas as pd
import pytest
from cre_expected_loss.models.lgd_challenger import (
    fit_constant_occurrence,
    predict_constant_occurrence,
)
from cre_expected_loss.ingestion.fannie_dataset import _number_expr_sql


def test_accounting_signs_and_invalid_values():
    import duckdb

    frame = pd.DataFrame(
        {"value": ["$1,200.00", "($1,200.00)", "-12.5", "0", "", None, "(12", "garbage"]}
    )
    con = duckdb.connect()
    con.register("source", frame)
    result = con.execute("SELECT " + _number_expr_sql("value") + " FROM source").fetchall()
    assert [r[0] for r in result] == [1200.0, -1200.0, -12.5, 0.0, None, None, None, None]


def test_constant_occurrence_and_unbounded_output():
    frame = pd.DataFrame(
        {
            "acquisition_ltv": [60.0] * 40,
            "underwritten_dscr": [1.4] * 40,
            "log_acquisition_upb": [14.0] * 40,
            "property_type": ["Multifamily"] * 40,
            "reported_loss_ratio": [0.0] * 10 + [2.0] * 30,
        }
    )
    fitted = fit_constant_occurrence(frame, True)
    assert fitted[0] == 0.75
    np.testing.assert_allclose(predict_constant_occurrence(fitted, frame), 1.5, rtol=1e-5)
    new = frame.copy()
    new["property_type"] = "Previously unseen"
    assert np.isfinite(predict_constant_occurrence(fitted, new)).all()
    assert fitted[0] == 0.75


def test_invalid_targets_fail():
    frame = pd.DataFrame(
        {
            "acquisition_ltv": [60.0] * 20,
            "underwritten_dscr": [1.4] * 20,
            "reported_loss_ratio": [-1.0] * 20,
        }
    )
    with pytest.raises(ValueError):
        fit_constant_occurrence(frame)
