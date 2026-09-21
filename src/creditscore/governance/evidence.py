"""Build and hash the Phase 2-4 evidence consumed by Phase 5."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.drift import DriftDetector
from creditscore.drift.report import save_drift_report
from creditscore.fairness import FairnessEvaluator, save_fairness_report
from creditscore.incidents.vendor_c_drift import VendorCDriftConfig, VendorCDriftScenario
from creditscore.incidents.vendor_d_group_stress import VendorDGroupStressScenario, VendorDStressConfig
from creditscore.model.evaluate import evaluate_model, save_metrics
from creditscore.model.train import load_model
from creditscore.utils.config import decision_threshold, load_yaml
from creditscore.utils.hashing import file_sha256
from creditscore.validation import DataQualityGate, load_data_contract

from .models import EvidenceArtifact, EvidenceBundle

SUPPORTED_SCENARIOS = {"healthy", "vendor_c", "vendor_d"}


def _artifact(name: str, path: Path) -> EvidenceArtifact:
    return EvidenceArtifact(
        name=name,
        path=str(path),
        sha256=file_sha256(path),
        size_bytes=path.stat().st_size,
    )


def verify_artifact(artifact: EvidenceArtifact) -> bool:
    path = Path(artifact.path)
    return (
        path.is_file() and path.stat().st_size == artifact.size_bytes and file_sha256(path) == artifact.sha256
    )


def save_evidence_bundle(bundle: EvidenceBundle, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def _vendor_c_config(phase3: dict[str, Any]) -> VendorCDriftConfig:
    payload = phase3["vendor_c"]
    return VendorCDriftConfig(
        random_seed=int(phase3["project"]["random_seed"]),
        device_center=float(payload["device_risk"]["center"]),
        device_scale=float(payload["device_risk"]["scale"]),
        device_shift=float(payload["device_risk"]["shift"]),
        device_noise_std=float(payload["device_risk"]["noise_std"]),
        utilization_shift=float(payload["credit_utilization"]["shift"]),
        utilization_noise_std=float(payload["credit_utilization"]["noise_std"]),
        dti_shift=float(payload["debt_to_income"]["shift"]),
        dti_noise_std=float(payload["debt_to_income"]["noise_std"]),
        bank_risk_shift=float(payload["bank_transaction_risk"]["shift"]),
        bank_risk_noise_std=float(payload["bank_transaction_risk"]["noise_std"]),
    )


def _vendor_d_config(phase4: dict[str, Any]) -> VendorDStressConfig:
    payload = phase4["vendor_d"]
    return VendorDStressConfig(
        sensitive_feature=str(payload["sensitive_feature"]),
        stressed_group=str(payload["stressed_group"]),
        device_risk_score_shift=float(payload["device_risk_score_shift"]),
        credit_utilization_shift=float(payload["credit_utilization_shift"]),
        bank_transaction_risk_shift=float(payload["bank_transaction_risk_shift"]),
    )


def _scenario_frame(
    root: Path,
    scenario: str,
    reference: pd.DataFrame,
    phase3: dict[str, Any],
    phase4: dict[str, Any],
) -> tuple[pd.DataFrame, str]:
    if scenario == "healthy":
        return reference.copy(deep=True), "vendor_a"
    if scenario == "vendor_c":
        current = VendorCDriftScenario(_vendor_c_config(phase3)).apply(reference)
        output = root / phase3["scenario"]["output"]
        output.parent.mkdir(parents=True, exist_ok=True)
        current.to_csv(output, index=False)
        return current, "vendor_c"
    if scenario == "vendor_d":
        current = VendorDGroupStressScenario(_vendor_d_config(phase4)).apply(reference)
        output = root / phase4["scenario"]["output"]
        output.parent.mkdir(parents=True, exist_ok=True)
        current.to_csv(output, index=False)
        return current, "vendor_d"
    raise ValueError(f"Unsupported governance scenario: {scenario}")


def build_scenario_evidence(root: str | Path, scenario: str) -> EvidenceBundle:
    root = Path(root)
    if scenario not in SUPPORTED_SCENARIOS:
        raise ValueError(f"Unsupported governance scenario: {scenario}")

    phase2 = load_yaml(root / "configs" / "phase2.yaml")
    phase3 = load_yaml(root / "configs" / "phase3.yaml")
    phase4 = load_yaml(root / "configs" / "phase4.yaml")
    phase5 = load_yaml(root / "configs" / "phase5.yaml")

    reference = pd.read_csv(root / phase3["scenario"]["input"])
    current, source = _scenario_frame(root, scenario, reference, phase3, phase4)
    scenario_dir = root / phase5["paths"]["evidence_dir"] / scenario
    scenario_dir.mkdir(parents=True, exist_ok=True)

    contract = load_data_contract(root / phase2["contract"]["path"])
    quality_gate = DataQualityGate(
        contract,
        evidence_dir=scenario_dir / "quality",
        quarantine_dir=root / phase5["paths"]["quarantine_dir"],
    )
    quality = quality_gate.evaluate(current, batch_name=f"phase5_{scenario}", source=source)

    model_path = root / phase5["registry"]["artifact_path"]
    model = load_model(model_path)
    metrics, _ = evaluate_model(
        model,
        current,
        threshold=decision_threshold(root),
        scenario=f"phase5_{scenario}",
        vendor=source,
    )
    performance_path = save_metrics(metrics, scenario_dir / "performance.json")

    reference_probabilities = np.asarray(
        model.predict_proba(reference[MODEL_INPUT_FEATURES])[:, 1], dtype=float
    )
    current_probabilities = np.asarray(model.predict_proba(current[MODEL_INPUT_FEATURES])[:, 1], dtype=float)

    drift_config = deepcopy(phase3)
    drift_config["scenario"]["name"] = f"phase5_{scenario}_drift"
    drift_config["scenario"]["source"] = source
    drift_detector = DriftDetector(drift_config)
    drift = drift_detector.evaluate(
        reference,
        current,
        reference_predictions=pd.Series(reference_probabilities, name="risk_probability"),
        current_predictions=pd.Series(current_probabilities, name="risk_probability"),
        approval_threshold=decision_threshold(root),
    )
    drift_json, drift_csv = save_drift_report(
        drift,
        scenario_dir / "drift_report.json",
        scenario_dir / "drift_metrics.csv",
    )

    fairness_config = deepcopy(phase4)
    fairness_config["scenario"]["name"] = f"phase5_{scenario}_fairness"
    fairness = FairnessEvaluator(fairness_config).evaluate(
        reference,
        current,
        reference_probabilities=reference_probabilities,
        current_probabilities=current_probabilities,
        default_threshold=decision_threshold(root),
    )
    fairness_json, fairness_csv = save_fairness_report(
        fairness,
        scenario_dir / "fairness_report.json",
        scenario_dir / "fairness_by_group.csv",
    )

    quality_path = Path(quality.evidence_path)
    artifacts = [
        _artifact("model", model_path),
        _artifact("quality", quality_path),
        _artifact("performance", performance_path),
        _artifact("drift_json", drift_json),
        _artifact("drift_csv", drift_csv),
        _artifact("fairness_json", fairness_json),
        _artifact("fairness_csv", fairness_csv),
    ]

    phase4_shap = root / phase4["paths"]["shap_summary_json"]
    if scenario == "vendor_d" and phase4_shap.exists():
        artifacts.append(_artifact("phase4_shap_summary", phase4_shap))

    primary = fairness.current_primary
    bundle = EvidenceBundle(
        scenario=scenario,
        source=source,
        quality_decision=quality.decision,
        performance_metrics={
            "roc_auc": float(metrics["roc_auc"]),
            "pr_auc": float(metrics["pr_auc"]),
            "brier_score": float(metrics["brier_score"]),
        },
        drift_status=drift.overall_status,
        fairness_status=fairness.overall_status,
        artifacts=artifacts,
        metadata={
            "critical_drift_features": drift.critical_features,
            "warning_drift_features": drift.warning_features,
            "primary_sensitive_feature": fairness.primary_sensitive_feature,
            "demographic_parity_ratio": primary.demographic_parity_ratio,
            "selection_rate_difference": primary.demographic_parity_difference,
            "equalized_odds_difference": primary.equalized_odds_difference,
        },
    )
    save_evidence_bundle(bundle, scenario_dir / "evidence_bundle.json")
    return bundle
