"""Generate Phase 12 intersectional fairness and proxy-risk evidence."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
from simulate_intersectional_stress import generate_vendor_e, target_group_name

from creditscore.data.preprocessing import (
    MODEL_INPUT_FEATURES,
    PROTECTED_EVALUATION_COLUMNS,
)
from creditscore.drift import DriftDetector
from creditscore.explainability import ShapEngine
from creditscore.fairness import (
    ExpandedFairnessEvaluator,
    ProxyRiskAnalyzer,
    save_expanded_fairness_report,
    save_proxy_risk_report,
)
from creditscore.model.train import load_model
from creditscore.utils.config import decision_settings, load_yaml
from creditscore.utils.hashing import file_sha256
from creditscore.validation import DataQualityGate, load_data_contract

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    phase2 = load_yaml(ROOT / "configs" / "phase2.yaml")
    phase3 = load_yaml(ROOT / "configs" / "phase3.yaml")
    config = load_yaml(ROOT / "configs" / "phase12.yaml")
    _, decision_threshold = decision_settings(ROOT)

    (
        reference_raw,
        current_raw,
        reference,
        current,
        output_path,
    ) = generate_vendor_e(config)

    contract = load_data_contract(ROOT / str(phase2["contract"]["path"]))
    quality_gate = DataQualityGate(
        contract,
        evidence_dir=ROOT / str(phase2["gate"]["evidence_dir"]),
        quarantine_dir=ROOT / str(phase2["gate"]["quarantine_dir"]),
    )
    quality = quality_gate.evaluate(
        current_raw,
        batch_name="vendor_e_phase12",
        source="vendor_e",
    )

    model_path = ROOT / str(config["paths"]["model"])
    model = load_model(model_path)
    reference_probabilities = np.asarray(
        model.predict_proba(reference_raw[MODEL_INPUT_FEATURES])[:, 1],
        dtype=float,
    )
    current_probabilities = np.asarray(
        model.predict_proba(current_raw[MODEL_INPUT_FEATURES])[:, 1],
        dtype=float,
    )

    drift_config = deepcopy(phase3)
    drift_config["scenario"]["name"] = "vendor_e_aggregate_drift_check"
    drift_config["scenario"]["source"] = "vendor_e"
    drift = DriftDetector(drift_config).evaluate(
        reference_raw,
        current_raw,
        reference_predictions=pd.Series(
            reference_probabilities,
            name="risk_probability",
        ),
        current_predictions=pd.Series(
            current_probabilities,
            name="risk_probability",
        ),
        approval_threshold=decision_threshold,
    )

    fairness = ExpandedFairnessEvaluator(config).evaluate(
        reference,
        current,
        reference_probabilities=reference_probabilities,
        current_probabilities=current_probabilities,
        default_threshold=decision_threshold,
    )
    fairness_json, fairness_csv = save_expanded_fairness_report(
        fairness,
        json_path=ROOT / str(config["paths"]["fairness_json"]),
        csv_path=ROOT / str(config["paths"]["fairness_csv"]),
    )

    shap_config = config["proxy_risk"]["shap"]
    target = target_group_name(config)
    shap_analysis = ShapEngine(model).explain(
        current,
        sensitive_feature=str(config["intersection"]["derived_feature"]),
        primary_group=target,
        sample_size=int(shap_config["sample_size"]),
        random_seed=int(shap_config["random_seed"]),
        top_k=int(shap_config["top_k"]),
        local_examples=int(shap_config["local_examples"]),
    )
    ShapEngine.save(
        shap_analysis,
        summary_path=ROOT / str(config["paths"]["shap_summary_json"]),
        global_path=ROOT / str(config["paths"]["shap_global_csv"]),
        group_path=ROOT / str(config["paths"]["shap_group_csv"]),
        delta_path=ROOT / str(config["paths"]["shap_delta_csv"]),
    )

    proxy = ProxyRiskAnalyzer(config).analyze(
        reference,
        current,
        shap_global=shap_analysis.global_importance,
        primary_group=target,
    )
    proxy_json, proxy_csv = save_proxy_risk_report(
        proxy,
        json_path=ROOT / str(config["paths"]["proxy_json"]),
        csv_path=ROOT / str(config["paths"]["proxy_csv"]),
    )

    primary = fairness.current_primary
    reference_primary = fairness.reference_primary
    single_axis_statuses = {
        item.sensitive_feature: item.status
        for item in fairness.current
        if item.sensitive_feature != fairness.primary_sensitive_feature
    }
    target_count = next(item.sample_count for item in primary.group_metrics if item.group == target)
    stressed_features = [str(value) for value in config["proxy_risk"]["stressed_proxy_features"]]
    signal_by_feature = {signal.feature: signal for signal in proxy.signals}
    stressed_deltas = {feature: signal_by_feature[feature].association_delta for feature in stressed_features}

    shap_features = set(shap_analysis.global_importance["feature"].astype(str))
    derived = str(config["intersection"]["derived_feature"])
    intersection_absent_from_shap = not any(derived in feature for feature in shap_features)

    summary = {
        "schema_version": 1,
        "scenario": str(config["scenario"]["name"]),
        "source": str(config["scenario"]["source"]),
        "target_intersection": target,
        "target_intersection_count": int(target_count),
        "data_quality_decision": quality.decision,
        "aggregate_drift_status": drift.overall_status,
        "protected_values_preserved": all(
            reference_raw[column].equals(current_raw[column]) for column in PROTECTED_EVALUATION_COLUMNS
        ),
        "target_preserved": reference_raw["default_30d"].equals(current_raw["default_30d"]),
        "protected_attributes_absent_from_model": all(
            column not in MODEL_INPUT_FEATURES for column in PROTECTED_EVALUATION_COLUMNS
        ),
        "intersection_absent_from_shap_feature_space": intersection_absent_from_shap,
        "reference_intersection_status": reference_primary.status,
        "intersection_status": fairness.overall_status,
        "single_axis_statuses": single_axis_statuses,
        "intersection_metrics": {
            "demographic_parity_ratio": primary.demographic_parity_ratio,
            "selection_rate_difference": primary.selection_rate_difference,
            "equal_opportunity_difference": primary.equal_opportunity_difference,
            "equalized_odds_difference": primary.equalized_odds_difference,
            "false_approval_rate_difference": primary.false_approval_rate_difference,
        },
        "stressed_proxy_association_deltas": stressed_deltas,
        "top_association_features": proxy.top_association_features,
        "review_priority_features": proxy.review_priority_features,
        "evidence_sha256": {
            "model": file_sha256(model_path),
            "reference_batch": file_sha256(ROOT / str(config["scenario"]["input"])),
            "current_batch": file_sha256(output_path),
            "fairness_json": file_sha256(fairness_json),
            "fairness_csv": file_sha256(fairness_csv),
            "proxy_json": file_sha256(proxy_json),
            "proxy_csv": file_sha256(proxy_csv),
            "shap_summary": file_sha256(ROOT / str(config["paths"]["shap_summary_json"])),
        },
        "interpretation": {
            "intersectional_metrics": ("project governance signals for a deterministic synthetic fixture"),
            "proxy_risk": (
                "statistical association plus SHAP influence supports review; "
                "it does not prove causal proxy use or legal discrimination"
            ),
        },
    }
    summary_path = ROOT / str(config["paths"]["summary_json"])
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("CreditScoreV4 — Phase 12 Fairness + Proxy Risk")
    print("=" * 47)
    print(f"Vendor E Phase 2 decision.......... {quality.decision}")
    print(f"Aggregate Phase 3 drift............ {drift.overall_status}")
    print(f"Target intersection................ {target} ({target_count:,})")
    print(f"Reference intersection status...... {reference_primary.status}")
    print(f"Current intersection status........ {fairness.overall_status}")
    print()
    print("Demographic parity ratio.......... " f"{primary.demographic_parity_ratio:.4f}")
    print("Selection-rate difference......... " f"{primary.selection_rate_difference:.4f}")
    print("Equal-opportunity difference...... " f"{primary.equal_opportunity_difference:.4f}")
    print("Equalized-odds difference......... " f"{primary.equalized_odds_difference:.4f}")
    print("False-approval-rate difference.... " f"{primary.false_approval_rate_difference:.4f}")
    print()
    print("Single-axis statuses")
    for feature, status in single_axis_statuses.items():
        print(f"  {feature:<32} {status}")
    print()
    print("Proxy-review priority features")
    for feature in proxy.review_priority_features:
        print(f"  - {feature}")
    print(f"\nSummary............................ {summary_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
