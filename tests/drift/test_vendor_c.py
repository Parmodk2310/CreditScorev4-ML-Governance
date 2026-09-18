from pathlib import Path

import pandas as pd

from creditscore.incidents.vendor_c_drift import VendorCDriftConfig, VendorCDriftScenario

ROOT = Path(__file__).resolve().parents[2]


def test_vendor_c_preserves_schema_and_missingness() -> None:
    reference = pd.read_csv(ROOT / "data/raw/vendor_a/holdout.csv")
    current = VendorCDriftScenario(VendorCDriftConfig()).apply(reference)
    assert list(current.columns) == list(reference.columns)
    assert current["device_risk_score"].isna().mean() == reference["device_risk_score"].isna().mean()


def test_vendor_c_shifts_selected_features_but_not_control() -> None:
    reference = pd.read_csv(ROOT / "data/raw/vendor_a/holdout.csv")
    current = VendorCDriftScenario(VendorCDriftConfig()).apply(reference)
    assert current["device_risk_score"].mean() > reference["device_risk_score"].mean() + 0.05
    assert current["bank_transaction_risk"].mean() > reference["bank_transaction_risk"].mean() + 0.05
    assert current["annual_income"].equals(reference["annual_income"])
