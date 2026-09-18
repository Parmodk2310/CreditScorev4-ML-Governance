from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from creditscore.data.generator import SyntheticDataConfig, generate_lending_dataset
from creditscore.data.preprocessing import MODEL_INPUT_FEATURES, PROTECTED_EVALUATION_COLUMNS
from creditscore.drift import DriftDetector
from creditscore.fairness import FairnessEvaluator
from creditscore.incidents.vendor_d_group_stress import VendorDGroupStressScenario, VendorDStressConfig
from creditscore.model.train import train_model
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[2]


def test_aggregate_stable_batch_can_fail_fairness_governance() -> None:
    full = generate_lending_dataset(
        SyntheticDataConfig(n_samples=6000, random_seed=42, baseline_device_null_rate=0.03)
    )
    train = full.iloc[:4200].copy()
    reference = full.iloc[4200:].copy()
    model_params = load_yaml(ROOT / "configs" / "phase1.yaml")["model"]["params"]
    model = train_model(train, target_column="default_30d", model_params=model_params)

    current = VendorDGroupStressScenario(
        VendorDStressConfig(
            device_risk_score_shift=0.12,
            credit_utilization_shift=0.05,
            bank_transaction_risk_shift=0.05,
        )
    ).apply(reference)

    reference_probabilities = np.asarray(
        model.predict_proba(reference[MODEL_INPUT_FEATURES])[:, 1], dtype=float
    )
    current_probabilities = np.asarray(model.predict_proba(current[MODEL_INPUT_FEATURES])[:, 1], dtype=float)

    phase3 = load_yaml(ROOT / "configs" / "phase3.yaml")
    drift = DriftDetector(phase3).evaluate(
        reference,
        current,
        reference_predictions=pd.Series(reference_probabilities),
        current_predictions=pd.Series(current_probabilities),
        approval_threshold=0.50,
    )
    fairness = FairnessEvaluator(load_yaml(ROOT / "configs" / "phase4.yaml")).evaluate(
        reference,
        current,
        reference_probabilities=reference_probabilities,
        current_probabilities=current_probabilities,
        default_threshold=0.50,
    )

    assert drift.overall_status == "STABLE"
    assert fairness.overall_status in {"WARNING", "FAIL"}
    assert all(column not in MODEL_INPUT_FEATURES for column in PROTECTED_EVALUATION_COLUMNS)
