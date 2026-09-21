"""Run Phase 2/3 pass-through controls and Phase 4 fairness assessment."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.drift import DriftDetector
from creditscore.fairness import FairnessEvaluator, save_fairness_report
from creditscore.model.train import load_model
from creditscore.utils.config import decision_settings, load_yaml
from creditscore.validation import DataQualityGate, load_data_contract

ROOT = Path(__file__).resolve().parents[1]


def run_fairness_assessment() -> tuple:
    phase2 = load_yaml(ROOT / "configs" / "phase2.yaml")
    phase3 = load_yaml(ROOT / "configs" / "phase3.yaml")
    phase4 = load_yaml(ROOT / "configs" / "phase4.yaml")
    _, decision_threshold = decision_settings(ROOT)

    reference = pd.read_csv(ROOT / phase4["scenario"]["input"])
    current = pd.read_csv(ROOT / phase4["scenario"]["output"])

    contract = load_data_contract(ROOT / phase2["contract"]["path"])
    quality_gate = DataQualityGate(
        contract,
        evidence_dir=ROOT / phase2["gate"]["evidence_dir"],
        quarantine_dir=ROOT / phase2["gate"]["quarantine_dir"],
    )
    quality = quality_gate.evaluate(current, batch_name="vendor_d_fairness", source="vendor_d")
    if not quality.passed:
        raise RuntimeError(f"Vendor D must pass Phase 2: {quality.failed_rule_ids}")

    model = load_model(ROOT / phase4["paths"]["model"])
    reference_probabilities = np.asarray(
        model.predict_proba(reference[MODEL_INPUT_FEATURES])[:, 1], dtype=float
    )
    current_probabilities = np.asarray(model.predict_proba(current[MODEL_INPUT_FEATURES])[:, 1], dtype=float)

    drift_config = deepcopy(phase3)
    drift_config["scenario"]["name"] = "vendor_d_aggregate_drift_check"
    drift_config["scenario"]["source"] = "vendor_d"
    drift_detector = DriftDetector(drift_config)
    drift_report = drift_detector.evaluate(
        reference,
        current,
        reference_predictions=pd.Series(reference_probabilities, name="risk_probability"),
        current_predictions=pd.Series(current_probabilities, name="risk_probability"),
        approval_threshold=decision_threshold,
    )

    evaluator = FairnessEvaluator(phase4)
    fairness_report = evaluator.evaluate(
        reference,
        current,
        reference_probabilities=reference_probabilities,
        current_probabilities=current_probabilities,
        default_threshold=decision_threshold,
    )
    save_fairness_report(
        fairness_report,
        ROOT / phase4["paths"]["fairness_json"],
        ROOT / phase4["paths"]["fairness_csv"],
    )
    return quality, drift_report, fairness_report


def main() -> None:
    quality, drift, report = run_fairness_assessment()
    primary = report.current_primary
    reference_primary = report.reference_primary

    print("CreditScoreV4 — Phase 4 Fairness Assessment")
    print("=" * 47)
    print(f"Vendor D Phase 2 decision.......... {quality.decision}")
    print(f"Vendor D Phase 3 aggregate drift.. {drift.overall_status}")
    print(f"Fairness governance............... {report.overall_status}")
    print()
    print(f"Primary dimension................. {report.primary_sensitive_feature}")
    print(
        "Demographic parity ratio......... "
        f"{reference_primary.demographic_parity_ratio:.4f} -> {primary.demographic_parity_ratio:.4f}"
    )
    print(
        "Selection-rate difference........ "
        f"{reference_primary.demographic_parity_difference:.4f} -> "
        f"{primary.demographic_parity_difference:.4f}"
    )
    print(
        "Equalized-odds difference........ "
        f"{reference_primary.equalized_odds_difference:.4f} -> {primary.equalized_odds_difference:.4f}"
    )
    print()
    print(f"{'Group':18} {'N':>7} {'Approve':>9} {'Mean risk':>10} {'Actual default':>15}")
    print("-" * 66)
    for item in primary.group_metrics:
        print(
            f"{item.group:18} {item.sample_count:7d} {item.approval_rate:9.2%} "
            f"{item.mean_predicted_risk:10.4f} {item.actual_default_rate:15.2%}"
        )


if __name__ == "__main__":
    main()
