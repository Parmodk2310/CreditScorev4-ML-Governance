"""Contract-valid Vendor C distribution-shift scenario for Phase 3."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VendorCDriftConfig:
    """Deterministic transformations that preserve Phase 2 contracts."""

    random_seed: int = 31415
    device_center: float = 0.50
    device_scale: float = 0.85
    device_shift: float = 0.06
    device_noise_std: float = 0.015
    utilization_shift: float = 0.05
    utilization_noise_std: float = 0.010
    dti_shift: float = 0.035
    dti_noise_std: float = 0.008
    bank_risk_shift: float = 0.06
    bank_risk_noise_std: float = 0.012


class VendorCDriftScenario:
    """Create a schema-compatible, contract-valid but drifted batch."""

    def __init__(self, config: VendorCDriftConfig):
        self.config = config

    def apply(self, frame: pd.DataFrame) -> pd.DataFrame:
        rng = np.random.default_rng(self.config.random_seed)
        shifted = frame.copy(deep=True)

        device = shifted["device_risk_score"].copy()
        present = device.notna()
        transformed_device = (
            self.config.device_center
            + self.config.device_scale * (device.loc[present] - self.config.device_center)
            + self.config.device_shift
            + rng.normal(0.0, self.config.device_noise_std, int(present.sum()))
        )
        shifted.loc[present, "device_risk_score"] = transformed_device.clip(0.0, 1.0)

        shifted["credit_utilization"] = (
            shifted["credit_utilization"]
            + self.config.utilization_shift
            + rng.normal(0.0, self.config.utilization_noise_std, len(shifted))
        ).clip(0.01, 0.99)

        shifted["debt_to_income"] = (
            shifted["debt_to_income"]
            + self.config.dti_shift
            + rng.normal(0.0, self.config.dti_noise_std, len(shifted))
        ).clip(0.02, 0.90)

        shifted["bank_transaction_risk"] = (
            shifted["bank_transaction_risk"]
            + self.config.bank_risk_shift
            + rng.normal(0.0, self.config.bank_risk_noise_std, len(shifted))
        ).clip(0.0, 1.0)

        return shifted
