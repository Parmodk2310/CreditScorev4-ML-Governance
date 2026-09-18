from __future__ import annotations

import pandas as pd

from creditscore.incidents.vendor_d_group_stress import VendorDGroupStressScenario, VendorDStressConfig


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "application_id": ["A", "B", "C"],
            "synthetic_demographic_group": ["group_a", "group_c", "group_c"],
            "sex": ["female", "male", "female"],
            "age_group": ["30-44", "30-44", "45-59"],
            "device_risk_score": [0.2, 0.4, None],
            "credit_utilization": [0.3, 0.4, 0.5],
            "bank_transaction_risk": [0.2, 0.3, 0.4],
            "default_30d": [0, 1, 0],
        }
    )


def test_vendor_d_changes_only_stressed_group_proxies() -> None:
    reference = _frame()
    current = VendorDGroupStressScenario(VendorDStressConfig()).apply(reference)

    assert current.loc[0, "device_risk_score"] == reference.loc[0, "device_risk_score"]
    assert current.loc[1, "device_risk_score"] > reference.loc[1, "device_risk_score"]
    assert pd.isna(current.loc[2, "device_risk_score"])
    assert reference["synthetic_demographic_group"].equals(current["synthetic_demographic_group"])
    assert reference["sex"].equals(current["sex"])
    assert reference["age_group"].equals(current["age_group"])
    assert reference["default_30d"].equals(current["default_30d"])
