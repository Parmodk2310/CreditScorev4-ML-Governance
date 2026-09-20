#!/usr/bin/env python3
"""Verify the Phase 12 intersectional fairness/proxy-risk contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return payload


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase12.yaml")
    acceptance = config["acceptance"]
    proxy = config["proxy_risk"]
    summary_path = ROOT / str(config["paths"]["summary_json"])
    if not summary_path.exists():
        raise FileNotFoundError(
            f"Phase 12 summary missing: {summary_path.relative_to(ROOT)}. " "Run make phase12-analyze first."
        )

    summary = _load_json(summary_path)
    metrics = summary["intersection_metrics"]
    stressed_features = {str(value) for value in proxy["stressed_proxy_features"]}
    stressed_deltas = {
        str(feature): float(value) for feature, value in summary["stressed_proxy_association_deltas"].items()
    }
    top_association = {str(value) for value in summary["top_association_features"]}
    review_priority = {str(value) for value in summary["review_priority_features"]}
    single_axis_statuses = {
        str(feature): str(status) for feature, status in summary["single_axis_statuses"].items()
    }
    evidence_hashes = {str(name): str(value) for name, value in summary["evidence_sha256"].items()}

    minimum_delta = float(proxy["minimum_association_delta"])
    minimum_top = int(proxy["minimum_stressed_features_in_top_association"])
    minimum_priority = int(proxy["minimum_stressed_features_in_review_priority"])

    gates = {
        "phase2_pass": (
            str(summary["data_quality_decision"]) == "PASS"
            if bool(acceptance["require_phase2_pass"])
            else True
        ),
        "aggregate_drift_status": str(summary["aggregate_drift_status"])
        == str(acceptance["require_phase3_status"]),
        "reference_intersection_not_fail": (
            str(summary["reference_intersection_status"]) != "FAIL"
            if bool(acceptance["require_reference_intersection_not_fail"])
            else True
        ),
        "intersection_status": str(summary["intersection_status"])
        == str(acceptance["require_intersection_status"]),
        "single_axis_not_fail": (
            all(status != "FAIL" for status in single_axis_statuses.values())
            if bool(acceptance["require_single_axis_not_fail"])
            else True
        ),
        "demographic_parity_ratio": float(metrics["demographic_parity_ratio"])
        < float(acceptance["maximum_intersection_demographic_parity_ratio"]),
        "selection_rate_difference": float(metrics["selection_rate_difference"])
        >= float(acceptance["minimum_intersection_selection_rate_difference"]),
        "equal_opportunity_difference": float(metrics["equal_opportunity_difference"])
        >= float(acceptance["minimum_intersection_equal_opportunity_difference"]),
        "equalized_odds_difference": float(metrics["equalized_odds_difference"])
        >= float(acceptance["minimum_intersection_equalized_odds_difference"]),
        "false_approval_rate_difference": float(metrics["false_approval_rate_difference"])
        >= float(acceptance["minimum_intersection_false_approval_rate_difference"]),
        "stressed_group_count": int(summary["target_intersection_count"])
        >= int(acceptance["minimum_stressed_group_count"]),
        "protected_values_preserved": (
            bool(summary["protected_values_preserved"])
            is bool(acceptance["require_protected_values_preserved"])
        ),
        "target_preserved": (
            bool(summary["target_preserved"]) is bool(acceptance["require_target_preserved"])
        ),
        "protected_absent_from_model": (
            bool(summary["protected_attributes_absent_from_model"])
            is bool(acceptance["require_protected_attributes_absent_from_model"])
        ),
        "intersection_absent_from_shap": (
            bool(summary["intersection_absent_from_shap_feature_space"])
            is bool(acceptance["require_intersection_absent_from_shap_feature_space"])
        ),
        "proxy_association_deltas": (
            all(
                feature in stressed_deltas and stressed_deltas[feature] >= minimum_delta
                for feature in stressed_features
            )
            if bool(acceptance["require_proxy_association_deltas"])
            else True
        ),
        "stressed_features_in_top_association": (
            len(stressed_features & top_association) >= minimum_top
            if bool(acceptance["require_stressed_features_in_top_association"])
            else True
        ),
        "stressed_features_in_review_priority": (
            len(stressed_features & review_priority) >= minimum_priority
            if bool(acceptance["require_stressed_features_in_review_priority"])
            else True
        ),
        "traceability_hashes_present": bool(evidence_hashes)
        and all(SHA256_PATTERN.fullmatch(value) for value in evidence_hashes.values()),
    }

    print("CreditScoreV4 — Phase 12 Verification")
    print("=" * 41)
    print(f"  target intersection............... {summary['target_intersection']}")
    print(f"  target count...................... {summary['target_intersection_count']}")
    print(f"  aggregate drift................... {summary['aggregate_drift_status']}")
    print(f"  fairness status................... {summary['intersection_status']}")
    print("  demographic parity ratio......... " f"{float(metrics['demographic_parity_ratio']):.4f}")
    print("  equal opportunity difference..... " f"{float(metrics['equal_opportunity_difference']):.4f}")
    print("  equalized odds difference......... " f"{float(metrics['equalized_odds_difference']):.4f}")
    print()
    print("Acceptance gates")
    for name, passed in gates.items():
        print(f"  {name:<44} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 12 CORE: VERIFIED")
        print(
            "Intersectional fairness fails while the configured single-axis "
            "dimensions avoid FAIL; proxy signals remain review evidence, not "
            "causal or legal conclusions."
        )
        return 0

    print("\nPHASE 12 CORE: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
