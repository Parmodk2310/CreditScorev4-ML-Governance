"""Schema-compatible upstream vendor migration incident simulation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VendorMigrationConfig:
    target_device_null_rate: float = 0.22
    semantic_attenuation: float = 0.42
    semantic_bias: float = -0.04
    semantic_noise_std: float = 0.12
    random_seed: int = 43


class VendorMigrationIncident:
    """Apply a silent semantic degradation while preserving the external schema.

    The new vendor still sends a numeric score in [0, 1], but its calibration is
    compressed/noisier and missingness rises materially. Missingness is weighted
    toward higher original risk scores, which makes it non-random without using
    the true outcome label.
    """

    def __init__(self, config: VendorMigrationConfig):
        self.config = config

    def apply(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy(deep=True)
        original = result["device_risk_score"].astype(float).copy()
        rng = np.random.default_rng(self.config.random_seed)

        observed = original.notna()
        observed_values = original.loc[observed].to_numpy()
        noise = rng.normal(0.0, self.config.semantic_noise_std, observed.sum())
        migrated = (
            0.50
            + self.config.semantic_attenuation * (observed_values - 0.50)
            + self.config.semantic_bias
            + noise
        )
        result.loc[observed, "device_risk_score"] = np.clip(migrated, 0.0, 1.0)

        target_missing = round(len(result) * self.config.target_device_null_rate)
        existing_missing = int(result["device_risk_score"].isna().sum())
        additional_missing = max(0, target_missing - existing_missing)

        candidates = result.index[result["device_risk_score"].notna()].to_numpy()
        # Weight using pre-migration score only; labels are never consulted.
        original_for_candidates = original.loc[candidates].fillna(original.median()).to_numpy()
        weights = 0.20 + np.power(np.clip(original_for_candidates, 0.0, 1.0), 2.0) * 2.80
        weights = weights / weights.sum()
        chosen = rng.choice(candidates, size=additional_missing, replace=False, p=weights)
        result.loc[chosen, "device_risk_score"] = np.nan

        return result
