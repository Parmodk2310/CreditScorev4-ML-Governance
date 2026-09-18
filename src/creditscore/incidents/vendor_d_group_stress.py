"""Vendor D subgroup proxy-stress scenario for Phase 4 fairness governance."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class VendorDStressConfig:
    """Contract-valid proxy shifts applied only to one evaluation group."""

    sensitive_feature: str = "synthetic_demographic_group"
    stressed_group: str = "group_c"
    device_risk_score_shift: float = 0.11
    credit_utilization_shift: float = 0.05
    bank_transaction_risk_shift: float = 0.05


class VendorDGroupStressScenario:
    """Create a batch with subgroup-level proxy stress but stable aggregate drift."""

    def __init__(self, config: VendorDStressConfig):
        self.config = config

    def apply(self, frame: pd.DataFrame) -> pd.DataFrame:
        if self.config.sensitive_feature not in frame.columns:
            raise ValueError(f"Missing sensitive feature: {self.config.sensitive_feature}")

        shifted = frame.copy(deep=True)
        stressed = shifted[self.config.sensitive_feature].astype(str).eq(self.config.stressed_group)
        if not bool(stressed.any()):
            raise ValueError(f"Stressed group not present: {self.config.stressed_group}")

        device_present = stressed & shifted["device_risk_score"].notna()
        shifted.loc[device_present, "device_risk_score"] = (
            shifted.loc[device_present, "device_risk_score"] + self.config.device_risk_score_shift
        ).clip(0.0, 1.0)

        shifted.loc[stressed, "credit_utilization"] = (
            shifted.loc[stressed, "credit_utilization"] + self.config.credit_utilization_shift
        ).clip(0.01, 0.99)

        shifted.loc[stressed, "bank_transaction_risk"] = (
            shifted.loc[stressed, "bank_transaction_risk"] + self.config.bank_transaction_risk_shift
        ).clip(0.0, 1.0)

        return shifted
