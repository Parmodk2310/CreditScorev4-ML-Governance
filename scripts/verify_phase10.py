#!/usr/bin/env python3
"""Verify Phase 10 root-cause evidence and remediation-governance contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return payload


def _f(mapping: dict[str, Any], key: str) -> float:
    return float(mapping[key])


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase10.yaml")
    acceptance = config["acceptance"]
    report_path = ROOT / str(config["evidence"]["report"])
    phase2_path = ROOT / "data/evidence/phase2/phase2_verification_summary.json"

    missing = [path for path in (report_path, phase2_path) if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing Phase 10 prerequisite: {path.relative_to(ROOT)}")
        return 1

    report = _read_json(report_path)
    phase2 = _read_json(phase2_path)

    invariants = report["invariants"]
    scenarios = report["scenarios"]
    effects = report["factorial_effects"]
    diagnostic = report["imputation_diagnostic"]
    counterfactuals = report["counterfactuals"]
    scope = report["scope"]
    traceability = report["traceability"]

    healthy = scenarios["healthy"]
    semantic = scenarios["semantic_only"]
    missingness = scenarios["missingness_only"]
    combined = scenarios["combined"]
    oracle = counterfactuals["oracle_semantic_restore"]
    oracle_metrics = oracle["metrics"]

    candidate_name = str(config["remediation"]["validation_candidate"])
    candidates = counterfactuals["training_quantile_candidates"]
    candidate_present = candidate_name in candidates
    candidate_metrics = candidates[candidate_name]["metrics"] if candidate_present else {}

    semantic_auc_drop = _f(healthy, "roc_auc") - _f(semantic, "roc_auc")
    missingness_approval_increase = _f(missingness, "approval_rate") - _f(healthy, "approval_rate")
    semantic_default_increase = _f(semantic, "approved_default_rate") - _f(healthy, "approved_default_rate")
    missingness_default_increase = _f(missingness, "approved_default_rate") - _f(
        healthy, "approved_default_rate"
    )

    oracle_auc_improvement = _f(oracle_metrics, "roc_auc") - _f(combined, "roc_auc")
    oracle_approval_reduction = _f(combined, "approval_rate") - _f(oracle_metrics, "approval_rate")
    oracle_default_reduction = _f(combined, "approved_default_rate") - _f(
        oracle_metrics, "approved_default_rate"
    )

    candidate_auc_improvement = (
        _f(candidate_metrics, "roc_auc") - _f(combined, "roc_auc") if candidate_present else float("-inf")
    )
    candidate_approval_gap = (
        abs(_f(candidate_metrics, "approval_rate") - _f(healthy, "approval_rate"))
        if candidate_present
        else float("inf")
    )
    candidate_default_reduction = (
        _f(combined, "approved_default_rate") - _f(candidate_metrics, "approved_default_rate")
        if candidate_present
        else float("-inf")
    )
    candidate_residual_auc_gap = (
        _f(healthy, "roc_auc") - _f(candidate_metrics, "roc_auc") if candidate_present else float("-inf")
    )
    candidate_residual_default_gap = (
        _f(candidate_metrics, "approved_default_rate") - _f(healthy, "approved_default_rate")
        if candidate_present
        else float("-inf")
    )

    vendor_b_blocked = str(phase2["incident"]["decision"]) == "BLOCK"

    gates = {
        "same_population": bool(invariants["same_population"]) is bool(acceptance["require_same_population"]),
        "same_labels": bool(invariants["same_labels"]) is bool(acceptance["require_same_labels"]),
        "generated_combined_matches_vendor_b": (
            bool(invariants["generated_combined_matches_vendor_b"])
            is bool(acceptance["require_generated_combined_matches_vendor_b"])
        ),
        "phase9_consistency": (
            bool(invariants["phase9_consistency"]) is bool(acceptance["require_phase9_consistency"])
        ),
        "newly_missing_rows": (
            int(diagnostic["newly_missing_count"]) >= int(acceptance["minimum_newly_missing_rows"])
        ),
        "median_control_reproduces_pipeline": (
            float(diagnostic["median_control_max_probability_delta"])
            <= float(acceptance["median_control_max_probability_delta"])
        ),
        "four_factorial_scenarios_present": (
            set(scenarios) == {"healthy", "semantic_only", "missingness_only", "combined"}
        ),
        "factorial_effects_present": (
            set(effects)
            >= {
                "roc_auc",
                "pr_auc",
                "brier_score",
                "approval_rate",
                "approved_default_rate",
                "mean_predicted_risk",
            }
        ),
        "semantic_auc_drop_material": semantic_auc_drop >= float(acceptance["minimum_semantic_auc_drop"]),
        "missingness_approval_increase_material": (
            missingness_approval_increase >= float(acceptance["minimum_missingness_approval_increase"])
        ),
        "semantic_approved_default_increase_material": (
            semantic_default_increase >= float(acceptance["minimum_semantic_approved_default_increase"])
        ),
        "missingness_approved_default_increase_material": (
            missingness_default_increase >= float(acceptance["minimum_missingness_approved_default_increase"])
        ),
        "semantic_reference_above_median": (
            float(diagnostic["semantic_reference_minus_median"])
            >= float(acceptance["minimum_semantic_reference_minus_median"])
        ),
        "oracle_is_not_deployable": oracle["deployable"] is False,
        "oracle_auc_improves": oracle_auc_improvement >= float(acceptance["minimum_oracle_auc_improvement"]),
        "oracle_reduces_approval_inflation": (
            oracle_approval_reduction >= float(acceptance["minimum_oracle_approval_reduction"])
        ),
        "oracle_reduces_approved_default": (
            oracle_default_reduction >= float(acceptance["minimum_oracle_approved_default_reduction"])
        ),
        "validation_candidate_present": candidate_present,
        "validation_candidate_is_diagnostic_only": (
            scope.get("validation_candidate") == candidate_name
            and scope.get("validation_candidate_status")
            == str(config["remediation"]["validation_candidate_status"])
            and scope.get("candidate_selected") is False
        ),
        "candidate_auc_improves": (
            candidate_auc_improvement >= float(acceptance["minimum_candidate_auc_improvement"])
        ),
        "candidate_approval_near_healthy": (
            candidate_approval_gap <= float(acceptance["maximum_candidate_approval_gap_from_healthy"])
        ),
        "candidate_reduces_approved_default": (
            candidate_default_reduction >= float(acceptance["minimum_candidate_approved_default_reduction"])
        ),
        "candidate_not_full_auc_remediation": (
            candidate_residual_auc_gap >= float(acceptance["minimum_candidate_residual_auc_gap"])
        ),
        "candidate_not_full_default_remediation": (
            candidate_residual_default_gap
            >= float(acceptance["minimum_candidate_residual_approved_default_gap"])
        ),
        "production_policy_unchanged": (
            scope["production_policy_changed"] is False
            and bool(acceptance["require_production_policy_unchanged"])
        ),
        "vendor_b_still_blocked": vendor_b_blocked is bool(acceptance["require_vendor_b_still_blocked"]),
        "traceability_hashes_present": all(
            isinstance(value, str) and len(value) == 64 for value in traceability.values()
        ),
    }

    print("CreditScoreV4 — Phase 10 Verification")
    print("=" * 40)
    print(f"  healthy AUC........................ {_f(healthy, 'roc_auc'):.4f}")
    print(f"  semantic-only AUC.................. {_f(semantic, 'roc_auc'):.4f}")
    print(f"  missingness-only approval.......... {_f(missingness, 'approval_rate'):.2%}")
    print(f"  combined approval.................. {_f(combined, 'approval_rate'):.2%}")
    print(
        "  semantic reference - median........ "
        f"{float(diagnostic['semantic_reference_minus_median']):+.4f}"
    )
    if candidate_present:
        print(f"  {candidate_name} AUC...................... {_f(candidate_metrics, 'roc_auc'):.4f}")
        print(
            f"  {candidate_name} approval................. " f"{_f(candidate_metrics, 'approval_rate'):.2%}"
        )
        print(
            f"  {candidate_name} approved default......... "
            f"{_f(candidate_metrics, 'approved_default_rate'):.2%}"
        )
    print(f"  Vendor B Phase 2 decision........... {phase2['incident']['decision']}")

    print("\nAcceptance gates")
    for name, passed in gates.items():
        print(f"  {name:<45} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 10: VERIFIED")
        print(
            f"{candidate_name} remains diagnostic-only; Vendor B remains BLOCKED "
            "and production preprocessing is unchanged."
        )
        return 0

    print("\nPHASE 10: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
