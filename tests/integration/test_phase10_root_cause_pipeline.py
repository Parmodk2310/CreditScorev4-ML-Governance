from __future__ import annotations

import numpy as np

from creditscore.data.generator import (
    SyntheticDataConfig,
    generate_lending_dataset,
)
from creditscore.data.loader import split_train_holdout
from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.incidents.vendor_migration import VendorMigrationConfig
from creditscore.model.train import train_model
from creditscore.root_cause import (
    build_ablation_frames,
    fitted_device_median,
    predict_with_device_value_override,
)


def test_transformed_median_control_reproduces_pipeline_scores() -> None:
    frame = generate_lending_dataset(
        SyntheticDataConfig(
            n_samples=12_000,
            random_seed=42,
            baseline_device_null_rate=0.03,
        )
    )
    train, healthy = split_train_holdout(
        frame,
        test_size=0.30,
        random_state=42,
    )

    model = train_model(
        train,
        target_column="default_30d",
        model_params={
            "n_estimators": 120,
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.90,
            "colsample_bytree": 0.90,
            "min_child_weight": 4,
            "reg_lambda": 2.0,
            "eval_metric": "logloss",
            "n_jobs": 2,
            "random_state": 42,
        },
    )

    frames = build_ablation_frames(
        healthy,
        combined_config=VendorMigrationConfig(
            target_device_null_rate=0.22,
            semantic_attenuation=0.42,
            semantic_bias=-0.04,
            semantic_noise_std=0.12,
            random_seed=43,
        ),
    )

    incident = frames.combined
    current = model.predict_proba(incident[MODEL_INPUT_FEATURES].copy())[:, 1]

    median = fitted_device_median(model)
    replacement = np.full(
        len(incident),
        median,
        dtype=float,
    )
    controlled = predict_with_device_value_override(
        model,
        incident,
        replacement,
    )

    assert np.isfinite(controlled).all()
    assert np.allclose(
        current,
        controlled,
        rtol=1e-10,
        atol=1e-10,
    )
