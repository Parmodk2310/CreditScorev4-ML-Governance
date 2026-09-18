#!/usr/bin/env python3
"""Phase 5 release gate: policy decisions, registry transitions, hashes, and auditability."""

from __future__ import annotations

import shutil
from pathlib import Path

from creditscore.governance.evidence import verify_artifact
from creditscore.governance.registry import RegistryTransitionError
from creditscore.governance.workflow import GovernanceWorkflow
from creditscore.utils.config import load_yaml
from creditscore.utils.hashing import file_sha256

ROOT = Path(__file__).resolve().parents[1]


def _reset_runtime(config: dict) -> None:
    for key in ("registry", "audit_log"):
        path = ROOT / config["paths"][key]
        if path.exists():
            path.unlink()
    for key in ("evidence_dir", "quarantine_dir"):
        path = ROOT / config["paths"][key]
        if path.exists():
            for child in path.iterdir():
                if child.name == ".gitkeep":
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()


def _blocking_gate_names(decision) -> set[str]:
    return {gate.name for gate in decision.gates if gate.blocking and not gate.passed}


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase5.yaml")
    _reset_runtime(config)
    workflow = GovernanceWorkflow(ROOT)

    healthy_decision, healthy_stage, healthy_evidence = workflow.evaluate_and_apply("healthy")
    drift_decision, drift_stage, drift_evidence = workflow.evaluate_and_apply("vendor_c")
    fairness_decision, fairness_stage, fairness_evidence = workflow.evaluate_and_apply("vendor_d")

    illegal_version = "0.5.0-illegal-transition-check"
    model_path = ROOT / config["registry"]["artifact_path"]
    illegal = workflow.registry.register(
        model_name=workflow.model_name,
        version=illegal_version,
        artifact_path=str(model_path),
        artifact_sha256=file_sha256(model_path),
        metadata={"scenario": "illegal_transition_check"},
    )
    illegal = workflow.registry.transition(
        model_name=illegal.model_name,
        version=illegal.version,
        target_stage="CANDIDATE",
    )
    illegal_transition_blocked = False
    try:
        workflow.registry.transition(
            model_name=illegal.model_name,
            version=illegal.version,
            target_stage="PRODUCTION",
        )
    except RegistryTransitionError:
        illegal_transition_blocked = True

    artifacts = healthy_evidence.artifacts + drift_evidence.artifacts + fairness_evidence.artifacts
    decision_paths = [
        ROOT / config["paths"]["evidence_dir"] / scenario / "governance_decision.json"
        for scenario in ("healthy", "vendor_c", "vendor_d")
    ]
    evidence_hashes_verified = all(verify_artifact(artifact) for artifact in artifacts)
    audit_records = workflow.audit.read_all()
    registry_records = workflow.registry.list_versions()
    acceptance = config["acceptance"]

    gates = {
        "healthy_candidate_approved": healthy_decision.decision == str(acceptance["healthy_decision"]),
        "healthy_promoted_to_staging": healthy_stage == str(acceptance["healthy_stage"]),
        "vendor_c_rejected": drift_decision.decision == str(acceptance["vendor_c_decision"]),
        "vendor_c_drift_blocks": str(acceptance["vendor_c_blocking_gate"])
        in _blocking_gate_names(drift_decision),
        "vendor_c_promotion_blocked": drift_stage == str(acceptance["vendor_c_stage"]),
        "vendor_d_rejected": fairness_decision.decision == str(acceptance["vendor_d_decision"]),
        "vendor_d_fairness_blocks": str(acceptance["vendor_d_blocking_gate"])
        in _blocking_gate_names(fairness_decision),
        "vendor_d_promotion_blocked": fairness_stage == str(acceptance["vendor_d_stage"]),
        "evidence_hashes_verified": evidence_hashes_verified,
        "audit_records_written": len(audit_records) >= int(acceptance["minimum_audit_records"]),
        "registry_persisted": len(registry_records) >= 4,
        "decision_artifacts_written": all(path.exists() for path in decision_paths),
        "illegal_transition_blocked": illegal_transition_blocked,
    }

    print("CreditScoreV4 — Phase 5 Verification")
    print("=" * 41)
    print("Healthy candidate")
    print(f"  Governance decision........ {healthy_decision.decision}")
    print(f"  Promotion.................. CANDIDATE -> {healthy_stage}")
    print()
    print("Vendor C candidate")
    print(f"  Governance decision........ {drift_decision.decision}")
    print(f"  Blocking gates............. {', '.join(sorted(_blocking_gate_names(drift_decision)))}")
    print(f"  Registry stage............. {drift_stage}")
    print()
    print("Vendor D candidate")
    print(f"  Governance decision........ {fairness_decision.decision}")
    print(f"  Blocking gates............. {', '.join(sorted(_blocking_gate_names(fairness_decision)))}")
    print(f"  Registry stage............. {fairness_stage}")
    print()
    print(f"Audit records................. {len(audit_records)}")
    print(f"Evidence artifacts checked.... {len(artifacts)}")
    print()
    print("Acceptance gates")
    for name, passed in gates.items():
        print(f"  {name:36} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 5: VERIFIED")
        return 0
    print("\nPHASE 5: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
