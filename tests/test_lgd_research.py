import numpy as np
import pandas as pd
import pytest

from cre_expected_loss.models.lgd_research import fit_lgd_research, fit_two_part, predict_two_part


def test_two_part_preserves_unbounded_severity_and_is_reproducible():
    frame = pd.DataFrame(
        {
            "acquisition_ltv": [60.0] * 40,
            "underwritten_dscr": [1.4] * 40,
            "reported_loss_ratio": [0.0] * 10 + [2.0] * 30,
        }
    )
    first = predict_two_part(fit_two_part(frame), frame)
    second = predict_two_part(fit_two_part(frame), frame)
    np.testing.assert_allclose(first[2], second[2])
    assert (first[1] > 1).all()
    assert (first[2] > 1).all()
    np.testing.assert_allclose(first[2], first[0] * first[1])


def test_fit_requires_explicit_proxy_acknowledgement(tmp_path):
    with pytest.raises(ValueError, match="acknowledgement"):
        fit_lgd_research(tmp_path, tmp_path / "out")


@pytest.mark.parametrize("values", [[0.0] * 20, [1.0] * 20, [np.nan] * 20, [-1.0] * 20])
def test_invalid_or_single_class_targets_fail(values):
    frame = pd.DataFrame(
        {
            "acquisition_ltv": [60.0] * 20,
            "underwritten_dscr": [1.5] * 20,
            "reported_loss_ratio": values,
        }
    )
    with pytest.raises(ValueError):
        fit_two_part(frame)


def test_chronological_pipeline_uses_training_only_and_retains_predictions(tmp_path):
    import json

    from cre_expected_loss.models.lgd_research import fit_lgd_research

    source = tmp_path / "audit"
    source.mkdir()
    frame = pd.DataFrame(
        {
            "loan_id": [str(i) for i in range(60)],
            "acquisition_ltv": [60.0] * 60,
            "underwritten_dscr": [1.5] * 60,
            "reported_loss_ratio": [0.0] * 10 + [0.5] * 30 + [2.0] * 20,
            "default_amount": [100.0] * 60,
            "status": ["research_eligible"] * 60,
            "credit_event_date": pd.to_datetime(
                ["2017-01-01"] * 40 + ["2020-01-01"] * 10 + ["2024-01-01"] * 10
            ),
        }
    )
    frame.to_parquet(source / "loan_reconciliation.parquet")
    (source / "reconciliation.json").write_text(
        json.dumps({"source_sha256": "synthetic", "source_cutoff": "2026-03-01", "limitations": []})
    )
    output = tmp_path / "fit"
    report = fit_lgd_research(source, output, acknowledge_proxy_target=True)
    assert report["benchmark"] == pytest.approx(0.375)
    assert report["metrics"]["train"]["loans"] == 40
    predictions = pd.read_parquet(output / "predictions.parquet")
    assert len(predictions) == 60
    assert predictions["mean_benchmark_prediction"].eq(0.375).all()
    with pytest.raises(FileExistsError):
        fit_lgd_research(source, output, acknowledge_proxy_target=True)
