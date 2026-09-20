from __future__ import annotations

import numpy as np
import pytest

from creditscore.data.generator import (
    SyntheticDataConfig,
    generate_lending_dataset,
)
from creditscore.incidents.vendor_migration import VendorMigrationConfig
from creditscore.root_cause import (
    build_ablation_frames,
    factorial_effect,
)


def test_factorial_effect_reconstructs_expected_components() -> None:
    effects = factorial_effect(10.0, 12.0, 13.0, 18.0)

    assert effects["semantic_main_effect"] == pytest.approx(3.5)
    assert effects["missingness_main_effect"] == pytest.approx(4.5)
    assert effects["interaction_effect"] == pytest.approx(3.0)


def test_ablation_preserves_population_labels_and_masks() -> None:
    healthy = generate_lending_dataset(
        SyntheticDataConfig(
            n_samples=5_000,
            random_seed=42,
            baseline_device_null_rate=0.03,
        )
    )
    config = VendorMigrationConfig(
        target_device_null_rate=0.22,
        semantic_attenuation=0.42,
        semantic_bias=-0.04,
        semantic_noise_std=0.12,
        random_seed=43,
    )

    frames = build_ablation_frames(
        healthy,
        combined_config=config,
    )

    for frame in (
        frames.semantic_only,
        frames.missingness_only,
        frames.combined,
    ):
        assert frame["application_id"].equals(healthy["application_id"])
        assert frame["default_30d"].equals(healthy["default_30d"])

    assert np.array_equal(
        frames.semantic_only["device_risk_score"].isna().to_numpy(),
        healthy["device_risk_score"].isna().to_numpy(),
    )
    assert np.array_equal(
        frames.missingness_only["device_risk_score"].isna().to_numpy(),
        frames.combined["device_risk_score"].isna().to_numpy(),
    )

    assert frames.combined["device_risk_score"].isna().mean() == pytest.approx(0.22, abs=1 / len(healthy))


def test_missingness_only_preserves_observed_healthy_values() -> None:
    healthy = generate_lending_dataset(
        SyntheticDataConfig(
            n_samples=4_000,
            random_seed=42,
            baseline_device_null_rate=0.03,
        )
    )
    frames = build_ablation_frames(
        healthy,
        combined_config=VendorMigrationConfig(
            target_device_null_rate=0.22,
            random_seed=43,
        ),
    )

    observed = frames.missingness_only["device_risk_score"].notna()

    assert np.allclose(
        frames.missingness_only.loc[
            observed,
            "device_risk_score",
        ].to_numpy(),
        healthy.loc[
            observed,
            "device_risk_score",
        ].to_numpy(),
    )
