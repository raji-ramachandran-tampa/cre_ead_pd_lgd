import numpy as np
import pandas as pd

from cre_expected_loss.models.lgd_macro_research import fit
from cre_expected_loss.models.lgd_proxy_model import fit_proxy


def test_proxy_fit_uses_explicit_target_without_duration_features():
    frame = pd.DataFrame(
        {
            "acquisition_ltv": np.arange(20) + 50.0,
            "underwritten_dscr": 1.2,
            "log_acquisition_upb": 15.0,
            "property_type": "MF",
            "loss_sharing_type": "DUS",
            "cpi_log_change_6m": np.linspace(-0.02, 0.05, 20),
            "signed_ratio": np.linspace(-0.3, 0.8, 20),
            "discounted_accounting_proxy": np.linspace(-0.2, 0.9, 20),
            "duration_years": np.linspace(0, 50, 20),
        }
    )
    original = frame.copy(deep=True)
    model = fit_proxy(frame)
    names = model[0].get_feature_names_out()
    assert not any("duration" in name or "proxy" in name for name in names)
    pd.testing.assert_frame_equal(frame, original)
    reference = frame.copy()
    reference["signed_ratio"] = frame.discounted_accounting_proxy
    np.testing.assert_allclose(
        model.predict(frame), fit(reference, ["cpi_log_change_6m"]).predict(frame)
    )
