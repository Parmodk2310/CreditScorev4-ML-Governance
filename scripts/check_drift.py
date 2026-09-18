#!/usr/bin/env python3
"""Run Phase 2 pass-through validation and Phase 3 statistical drift detection."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.drift import DriftDetector
from creditscore.drift.report import save_drift_report, save_reference_profile
from creditscore.model.train import load_model
from creditscore.utils.config import load_yaml
from creditscore.validation import DataQualityGate, load_data_contract

ROOT = Path(__file__).resolve().parents[1]


def run_drift_check() -> tuple:
    phase2 = load_yaml(ROOT / "configs" / "phase2.yaml")
    phase3 = load_yaml(ROOT / "configs" / "phase3.yaml")
    reference = pd.read_csv(ROOT / phase3["scenario"]["input"])
    current = pd.read_csv(ROOT / phase3["scenario"]["output"])

    contract = load_data_contract(ROOT / phase2["contract"]["path"])
    quality_gate = DataQualityGate(
        contract,
        evidence_dir=ROOT / phase2["gate"]["evidence_dir"],
        quarantine_dir=ROOT / phase2["gate"]["quarantine_dir"],
    )
    quality = quality_gate.evaluate(current, batch_name="vendor_c_drift", source="vendor_c")
    if not quality.passed:
        raise RuntimeError(f"Vendor C must pass Phase 2 before drift analysis: {quality.failed_rule_ids}")

    model = load_model(ROOT / phase3["paths"]["model"])
    reference_predictions = pd.Series(
        model.predict_proba(reference[MODEL_INPUT_FEATURES])[:, 1],
        name="risk_probability",
    )
    current_predictions = pd.Series(
        model.predict_proba(current[MODEL_INPUT_FEATURES])[:, 1],
        name="risk_probability",
    )

    detector = DriftDetector(phase3)
    report = detector.evaluate(
        reference,
        current,
        reference_predictions=reference_predictions,
        current_predictions=current_predictions,
        approval_threshold=float(phase3["prediction"]["approval_threshold"]),
    )
    save_reference_profile(reference, detector.features, ROOT / phase3["paths"]["reference_profile"])
    save_drift_report(
        report,
        ROOT / phase3["paths"]["evidence_json"],
        ROOT / phase3["paths"]["evidence_csv"],
    )
    return quality, report


def main() -> None:
    quality, report = run_drift_check()
    print("CreditScoreV4 — Phase 3 Drift Check")
    print("=" * 41)
    print(f"Vendor C Phase 2 decision........... {quality.decision}")
    print(f"Overall drift status................ {report.overall_status}")
    print()
    print(f"{'Feature':34} {'PSI':>8} {'KS':>8} {'Status':>10}")
    print("-" * 64)
    for result in report.feature_results:
        print(f"{result.feature:34} {result.psi:8.4f} {result.ks_statistic:8.4f} {result.status:>10}")
    if report.prediction_result is not None:
        result = report.prediction_result
        print(f"{result.feature:34} {result.psi:8.4f} {result.ks_statistic:8.4f} {result.status:>10}")
    print()
    print(f"Critical features: {', '.join(report.critical_features) or 'none'}")
    print(f"Mean risk shift: {report.prediction_summary['mean_risk_shift']:+.4f}")
    print(f"Approval-rate shift: {report.prediction_summary['approval_rate_shift']:+.2%}")


if __name__ == "__main__":
    main()
