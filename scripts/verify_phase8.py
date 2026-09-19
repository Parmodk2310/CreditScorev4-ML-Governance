#!/usr/bin/env python3
"""Phase 8 gate: reviewer documentation, evidence traceability, and policy consistency."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from check_deployment_gate import evaluate_gate

from creditscore.governance.registry import ALLOWED_TRANSITIONS
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return payload


def _same_float(left: Any, right: Any) -> bool:
    return abs(float(left) - float(right)) < 1e-12


def _all_paths_exist(paths: list[str]) -> bool:
    return all((ROOT / path).exists() for path in paths)


def _decision(path: str) -> str:
    return str(_read_json(ROOT / path).get("decision", ""))


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> int:
    phase8 = load_yaml(ROOT / "configs" / "phase8.yaml")
    phase5 = load_yaml(ROOT / "configs" / "phase5.yaml")
    phase6 = load_yaml(ROOT / "configs" / "phase6.yaml")
    phase7 = load_yaml(ROOT / "configs" / "phase7.yaml")

    required_docs = [str(v) for v in phase8["documents"]["required"]]
    required_visuals = [str(v) for v in phase8["visuals"]["required"]]
    required_evidence = [str(v) for v in phase8["evidence"]["required"]]

    policy_expected = phase8["policy_contract"]
    policy_actual = phase5["policy"]["gates"]
    release_expected = phase8["release_contract"]
    release_actual = phase6["release"]

    original = os.environ.pop("AWS_DEPLOY_ENABLED", None)
    try:
        deployment_enabled, _ = evaluate_gate()
    finally:
        if original is not None:
            os.environ["AWS_DEPLOY_ENABLED"] = original

    evidence_present = _all_paths_exist(required_evidence)

    decisions: dict[str, str] = {}
    release_report: dict[str, Any] = {}
    phase7_manifest: dict[str, Any] = {}

    if evidence_present:
        decisions = {
            "healthy": _decision("data/evidence/phase5/healthy/governance_decision.json"),
            "vendor_c": _decision("data/evidence/phase5/vendor_c/governance_decision.json"),
            "vendor_d": _decision("data/evidence/phase5/vendor_d/governance_decision.json"),
        }
        release_report = _read_json(ROOT / "data/evidence/phase6/phase6_release_report.json")
        phase7_manifest = _read_json(ROOT / "data/evidence/phase7/release_manifest.json")

    expected_outcomes = {str(name): str(value) for name, value in phase8["governance_outcomes"].items()}

    registry_safe = (
        ALLOWED_TRANSITIONS["REGISTERED"] == {"CANDIDATE"}
        and ALLOWED_TRANSITIONS["CANDIDATE"] == {"STAGING", "REJECTED"}
        and "PRODUCTION" not in ALLOWED_TRANSITIONS["CANDIDATE"]
        and ALLOWED_TRANSITIONS["STAGING"] == {"SHADOW"}
        and ALLOWED_TRANSITIONS["SHADOW"] == {"CANARY", "STAGING"}
        and ALLOWED_TRANSITIONS["CANARY"] == {"PRODUCTION", "STAGING"}
    )

    gates = {
        "required_documents_exist": _all_paths_exist(required_docs),
        "required_visuals_exist": _all_paths_exist(required_visuals),
        "required_phase1_7_evidence_exists": evidence_present,
        "policy_roc_auc_matches": _same_float(
            policy_actual["performance"]["minimum_roc_auc"],
            policy_expected["minimum_roc_auc"],
        ),
        "policy_pr_auc_matches": _same_float(
            policy_actual["performance"]["minimum_pr_auc"],
            policy_expected["minimum_pr_auc"],
        ),
        "policy_brier_matches": _same_float(
            policy_actual["calibration"]["maximum_brier_score"],
            policy_expected["maximum_brier_score"],
        ),
        "policy_drift_block_matches": str(policy_expected["blocked_drift_status"])
        in {str(v) for v in policy_actual["drift"]["blocked_statuses"]},
        "policy_fairness_block_matches": str(policy_expected["blocked_fairness_status"])
        in {str(v) for v in policy_actual["fairness"]["blocked_statuses"]},
        "policy_evidence_minimum_matches": int(policy_actual["evidence_integrity"]["minimum_artifacts"])
        == int(policy_expected["minimum_artifacts"]),
        "registry_transition_contract": registry_safe,
        "canary_shares_match": [float(v) for v in release_actual["canary_shares"]]
        == [float(v) for v in release_expected["canary_shares"]],
        "shadow_error_rate_matches": _same_float(
            release_actual["gates"]["shadow"]["maximum_error_rate"],
            release_expected["shadow"]["maximum_error_rate"],
        ),
        "shadow_p95_matches": _same_float(
            release_actual["gates"]["shadow"]["maximum_p95_latency_ms"],
            release_expected["shadow"]["maximum_p95_latency_ms"],
        ),
        "canary_error_rate_matches": _same_float(
            release_actual["gates"]["canary"]["maximum_error_rate"],
            release_expected["canary"]["maximum_error_rate"],
        ),
        "canary_p95_matches": _same_float(
            release_actual["gates"]["canary"]["maximum_p95_latency_ms"],
            release_expected["canary"]["maximum_p95_latency_ms"],
        ),
        "deployment_env_contract": str(phase7["aws"]["deploy_enabled_env"])
        == str(phase8["deployment_contract"]["enable_env"]),
        "deployment_fail_closed": deployment_enabled is False,
        "expected_governance_outcomes": evidence_present and decisions == expected_outcomes,
        "healthy_release_reaches_production": evidence_present
        and str(release_report.get("healthy_final_stage")) == str(release_expected["healthy_final_stage"]),
        "degraded_release_rolls_back": evidence_present
        and str(release_report.get("rollback_final_stage")) == str(release_expected["rollback_final_stage"]),
        "rollback_reason_present": evidence_present and bool(release_report.get("rollback_reason")),
        "phase7_manifest_fail_closed": evidence_present
        and phase7_manifest.get("deployment_enabled") is False,
    }

    reviewer_manifest = {
        "schema_version": 1,
        "project": "CreditScoreV4 ML Governance",
        "phase": 8,
        "generated_from_commit": _git_commit(),
        "evidence": {
            "required_paths": required_evidence,
            "phase1_7_evidence_present": evidence_present,
            "governance_decisions": decisions,
            "release": {
                "healthy_final_stage": release_report.get("healthy_final_stage"),
                "rollback_final_stage": release_report.get("rollback_final_stage"),
                "rollback_reason": release_report.get("rollback_reason"),
                "visited_canary_shares": release_report.get("visited_canary_shares"),
            },
            "delivery": {
                "deployment_enabled": phase7_manifest.get("deployment_enabled") if phase7_manifest else None,
            },
        },
        "documentation": {
            "required": required_docs,
            "all_present": gates["required_documents_exist"],
        },
        "visuals": {
            "required": required_visuals,
            "all_present": gates["required_visuals_exist"],
        },
        "acceptance": gates,
    }

    output = ROOT / str(phase8["evidence"]["reviewer_manifest"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(reviewer_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    gates["reviewer_manifest_written"] = output.exists()

    print("CreditScoreV4 — Phase 8 Verification")
    print("=" * 41)
    for name, passed in gates.items():
        print(f"  {name:<42} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print(f"\nReviewer manifest............... {output.relative_to(ROOT)}")
        print("PHASE 8: VERIFIED")
        return 0

    print("\nPHASE 8: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
