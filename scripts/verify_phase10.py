#!/usr/bin/env python3
"""Verify the integrity of the first-pass Phase 10 experiment."""

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


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase10.yaml")
    acceptance = config["acceptance"]
    report_path = ROOT / str(config["evidence"]["report"])

    if not report_path.exists():
        print(f"Missing Phase 10 report: " f"{report_path.relative_to(ROOT)}")
        return 1

    report = _read_json(report_path)
    invariants = report["invariants"]
    diagnostic = report["imputation_diagnostic"]
    traceability = report["traceability"]

    gates = {
        "same_population": (
            bool(invariants["same_population"]) is bool(acceptance["require_same_population"])
        ),
        "same_labels": (bool(invariants["same_labels"]) is bool(acceptance["require_same_labels"])),
        "generated_combined_matches_vendor_b": (
            bool(invariants["generated_combined_matches_vendor_b"])
            is bool(acceptance["require_generated_combined_matches_vendor_b"])
        ),
        "phase9_consistency": (
            bool(invariants["phase9_consistency"]) is bool(acceptance["require_phase9_consistency"])
        ),
        "newly_missing_rows_present": (
            int(diagnostic["newly_missing_count"]) >= int(acceptance["minimum_newly_missing_rows"])
        ),
        "median_control_reproduces_pipeline": (
            float(diagnostic["median_control_max_probability_delta"])
            <= float(acceptance["median_control_max_probability_delta"])
        ),
        "four_factorial_scenarios_present": (
            set(report["scenarios"])
            == {
                "healthy",
                "semantic_only",
                "missingness_only",
                "combined",
            }
        ),
        "factorial_effects_present": (
            set(report["factorial_effects"])
            >= {
                "roc_auc",
                "pr_auc",
                "brier_score",
                "approval_rate",
                "approved_default_rate",
                "mean_predicted_risk",
            }
        ),
        "oracle_is_not_deployable": (
            report["counterfactuals"]["oracle_semantic_restore"]["deployable"] is False
        ),
        "candidate_not_preselected": (report["scope"]["candidate_selected"] is False),
        "production_policy_unchanged": (report["scope"]["production_policy_changed"] is False),
        "traceability_hashes_present": all(
            isinstance(value, str) and len(value) == 64 for value in traceability.values()
        ),
    }

    print("CreditScoreV4 — Phase 10 Structural Verification")
    print("=" * 51)

    for name, passed in gates.items():
        print(f"  {name:<43} " f"{'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 10 CORE EXPERIMENT: VERIFIED")
        print(
            "Outcome-specific remediation gates are intentionally " "pending deterministic evidence review."
        )
        return 0

    print("\nPHASE 10 CORE EXPERIMENT: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
