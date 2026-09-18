#!/usr/bin/env python3
"""Phase 4 release gate: aggregate-stable Vendor D must fail fairness governance and be explainable."""

from __future__ import annotations

from pathlib import Path

from assess_fairness import run_fairness_assessment
from explain_model import run_explainability
from simulate_fairness_stress import generate_vendor_d

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES, PROTECTED_EVALUATION_COLUMNS
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase4.yaml")
    reference, current, output_path = generate_vendor_d(config)
    quality, drift, fairness = run_fairness_assessment()
    shap_analysis = run_explainability()

    acceptance = config["acceptance"]
    primary = fairness.current_primary
    required_proxy_features = set(config["explainability"]["required_positive_proxy_features"])
    top_positive = set(shap_analysis.summary["top_positive_primary_group_features"])
    model_feature_names = set(MODEL_INPUT_FEATURES)
    shap_feature_names = set(shap_analysis.global_importance["feature"].astype(str))

    evidence_paths = [
        ROOT / config["paths"]["fairness_json"],
        ROOT / config["paths"]["fairness_csv"],
        ROOT / config["paths"]["shap_summary_json"],
        ROOT / config["paths"]["shap_global_csv"],
        ROOT / config["paths"]["shap_group_csv"],
        ROOT / config["paths"]["shap_delta_csv"],
    ]

    gates = {
        "vendor_d_generated": output_path.exists(),
        "schema_preserved": list(reference.columns) == list(current.columns),
        "row_count_preserved": len(reference) == len(current),
        "protected_values_preserved": all(
            reference[column].equals(current[column]) for column in PROTECTED_EVALUATION_COLUMNS
        ),
        "target_preserved": reference["default_30d"].equals(current["default_30d"]),
        "vendor_d_phase2_passes": quality.passed,
        "vendor_d_not_quarantined": quality.quarantine_path is None,
        "aggregate_phase3_is_stable": drift.overall_status == str(acceptance["require_phase3_status"]),
        "fairness_governance_fails": fairness.overall_status == str(acceptance["require_fairness_status"]),
        "demographic_parity_ratio_flagged": primary.demographic_parity_ratio
        < float(acceptance["maximum_primary_demographic_parity_ratio"]),
        "selection_rate_difference_flagged": primary.demographic_parity_difference
        >= float(acceptance["minimum_primary_selection_rate_difference"]),
        "equalized_odds_difference_flagged": primary.equalized_odds_difference
        >= float(acceptance["minimum_primary_equalized_odds_difference"]),
        "protected_attributes_absent_from_model": all(
            column not in model_feature_names for column in PROTECTED_EVALUATION_COLUMNS
        ),
        "protected_attributes_absent_from_shap": all(
            not any(column in feature for feature in shap_feature_names)
            for column in PROTECTED_EVALUATION_COLUMNS
        ),
        "stressed_proxies_explained": required_proxy_features.issubset(top_positive),
        "evidence_written": all(path.exists() for path in evidence_paths),
    }

    print("CreditScoreV4 — Phase 4 Verification")
    print("=" * 41)
    print(f"Vendor D Phase 2 decision.......... {quality.decision}")
    print(f"Vendor D Phase 3 aggregate drift.. {drift.overall_status}")
    print(f"Fairness governance............... {fairness.overall_status}")
    print(f"Primary DP ratio.................. {primary.demographic_parity_ratio:.4f}")
    print(f"Primary selection difference...... {primary.demographic_parity_difference:.4f}")
    print(f"Primary equalized-odds difference. {primary.equalized_odds_difference:.4f}")
    print(
        "Explained proxy features.......... "
        f"{', '.join(sorted(required_proxy_features & top_positive)) or 'none'}"
    )
    print()
    print("Acceptance gates")
    for name, passed in gates.items():
        print(f"  {name:40} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 4: VERIFIED")
        return 0
    print("\nPHASE 4: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
