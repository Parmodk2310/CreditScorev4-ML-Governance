"""Vendor E intersectional proxy-stress scenario for Phase 12."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class VendorEStressConfig:
    """Shift non-protected model inputs for one evaluation-only intersection."""

    sex_value: str = "female"
    demographic_group_value: str = "group_c"
    device_risk_score_shift: float = 0.12
    credit_utilization_shift: float = 0.06
    bank_transaction_risk_shift: float = 0.05


class VendorEIntersectionalProxyStressScenario:
    """Create a contract-valid intersectional proxy-stress fixture."""

    def __init__(self, config: VendorEStressConfig):
        self.config = config

    def target_mask(self, frame: pd.DataFrame) -> pd.Series:
        required = {"sex", "synthetic_demographic_group"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"Missing intersection columns: {missing}")

        return frame["sex"].astype(str).eq(self.config.sex_value) & frame[
            "synthetic_demographic_group"
        ].astype(str).eq(self.config.demographic_group_value)

    def apply(self, frame: pd.DataFrame) -> pd.DataFrame:
        shifted = frame.copy(deep=True)
        stressed = self.target_mask(shifted)
        if not bool(stressed.any()):
            raise ValueError("Configured Phase 12 stressed intersection is absent")

        present_device = stressed & shifted["device_risk_score"].notna()
        shifted.loc[present_device, "device_risk_score"] = (
            shifted.loc[present_device, "device_risk_score"] + self.config.device_risk_score_shift
        ).clip(0.0, 1.0)
        shifted.loc[stressed, "credit_utilization"] = (
            shifted.loc[stressed, "credit_utilization"] + self.config.credit_utilization_shift
        ).clip(0.01, 0.99)
        shifted.loc[stressed, "bank_transaction_risk"] = (
            shifted.loc[stressed, "bank_transaction_risk"] + self.config.bank_transaction_risk_shift
        ).clip(0.0, 1.0)
        return shifted
