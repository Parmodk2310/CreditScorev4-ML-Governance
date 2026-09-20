"""Controlled Phase 10 ablations for the Vendor B incident."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.pipeline import Pipeline

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES, NUMERIC_FEATURES
from creditscore.incidents.vendor_migration import (
    VendorMigrationConfig,
    VendorMigrationIncident,
)


@dataclass(frozen=True)
class AblationFrames:
    healthy: pd.DataFrame
    semantic_only: pd.DataFrame
    missingness_only: pd.DataFrame
    combined: pd.DataFrame


def _validate_identity(healthy: pd.DataFrame, candidate: pd.DataFrame) -> None:
    if not healthy["application_id"].astype(str).equals(candidate["application_id"].astype(str)):
        raise ValueError("Ablation changed the ordered applicant population.")

    if not healthy["default_30d"].astype(int).equals(candidate["default_30d"].astype(int)):
        raise ValueError("Ablation changed the outcome labels.")


def build_ablation_frames(
    healthy: pd.DataFrame,
    *,
    combined_config: VendorMigrationConfig,
) -> AblationFrames:
    """Build a controlled 2x2 decomposition of the Vendor B incident.

    healthy:
        baseline semantics + baseline missingness

    semantic_only:
        Vendor B score attenuation/bias/noise + baseline missingness

    missingness_only:
        healthy score semantics + the exact Vendor B missingness mask

    combined:
        Vendor B score attenuation/bias/noise + Vendor B missingness

    The missingness-only scenario intentionally reuses the mask from the
    combined incident. This isolates score semantics from missing-value
    selection without depending on RNG implementation details.
    """

    baseline_null_rate = float(healthy["device_risk_score"].isna().mean())

    semantic_only_config = VendorMigrationConfig(
        target_device_null_rate=baseline_null_rate,
        semantic_attenuation=combined_config.semantic_attenuation,
        semantic_bias=combined_config.semantic_bias,
        semantic_noise_std=combined_config.semantic_noise_std,
        random_seed=combined_config.random_seed,
    )

    semantic_only = VendorMigrationIncident(semantic_only_config).apply(healthy)
    combined = VendorMigrationIncident(combined_config).apply(healthy)

    missingness_only = healthy.copy(deep=True)
    combined_missing = combined["device_risk_score"].isna()
    missingness_only.loc[combined_missing, "device_risk_score"] = np.nan

    for frame in (semantic_only, missingness_only, combined):
        _validate_identity(healthy, frame)

    healthy_missing = healthy["device_risk_score"].isna().to_numpy()
    semantic_missing = semantic_only["device_risk_score"].isna().to_numpy()
    missingness_only_mask = missingness_only["device_risk_score"].isna().to_numpy()
    combined_mask = combined["device_risk_score"].isna().to_numpy()

    if not np.array_equal(healthy_missing, semantic_missing):
        raise ValueError("Semantic-only ablation changed baseline missingness.")

    if not np.array_equal(missingness_only_mask, combined_mask):
        raise ValueError("Missingness-only ablation does not match Vendor B missingness.")

    return AblationFrames(
        healthy=healthy.copy(deep=True),
        semantic_only=semantic_only,
        missingness_only=missingness_only,
        combined=combined,
    )


def factorial_effect(
    f00: float,
    f10: float,
    f01: float,
    f11: float,
) -> dict[str, float]:
    """Return two-factor average main effects and the interaction term."""

    semantic_main = ((f10 - f00) + (f11 - f01)) / 2.0
    missingness_main = ((f01 - f00) + (f11 - f10)) / 2.0
    interaction = f11 - f10 - f01 + f00

    return {
        "semantic_main_effect": float(semantic_main),
        "missingness_main_effect": float(missingness_main),
        "interaction_effect": float(interaction),
    }


def _numeric_imputer(model: Pipeline):
    preprocessor = model.named_steps["preprocessor"]
    numeric_pipeline = preprocessor.named_transformers_["numeric"]

    if list(numeric_pipeline.named_steps) != ["imputer"]:
        raise RuntimeError(
            "Phase 10 transformed-value override assumes the numeric "
            "pipeline contains only the fitted imputer."
        )

    return numeric_pipeline.named_steps["imputer"]


def fitted_device_median(model: Pipeline) -> float:
    """Return the fitted training median used for device_risk_score."""

    imputer = _numeric_imputer(model)
    device_index = NUMERIC_FEATURES.index("device_risk_score")
    return float(imputer.statistics_[device_index])


def predict_with_device_value_override(
    model: Pipeline,
    frame: pd.DataFrame,
    replacement_values: np.ndarray,
) -> np.ndarray:
    """Score missing rows with alternate device values, preserving the indicator.

    The fitted pipeline first performs its ordinary median imputation and
    missing-indicator generation. Only the transformed numeric value for
    device_risk_score is then replaced on raw-missing rows. The fitted
    missingness indicator remains unchanged.

    This is a diagnostic counterfactual for the current pipeline, not a new
    production preprocessing implementation.
    """

    replacement = np.asarray(replacement_values, dtype=float)
    if replacement.ndim != 1 or len(replacement) != len(frame):
        raise ValueError("replacement_values must be one-dimensional and match frame length.")
    if not np.isfinite(replacement).all():
        raise ValueError("replacement_values must be finite.")

    missing = frame["device_risk_score"].isna().to_numpy()
    if not missing.any():
        return model.predict_proba(frame[MODEL_INPUT_FEATURES].copy())[:, 1]

    feature_engineering = model.named_steps["feature_engineering"]
    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]

    _numeric_imputer(model)

    engineered = feature_engineering.transform(frame[MODEL_INPUT_FEATURES].copy())
    transformed = preprocessor.transform(engineered)

    if sparse.issparse(transformed):
        matrix = transformed.toarray()
    else:
        matrix = np.asarray(transformed, dtype=float).copy()

    device_index = NUMERIC_FEATURES.index("device_risk_score")
    matrix[missing, device_index] = replacement[missing]

    probabilities = classifier.predict_proba(matrix)[:, 1]
    return np.asarray(probabilities, dtype=float)
