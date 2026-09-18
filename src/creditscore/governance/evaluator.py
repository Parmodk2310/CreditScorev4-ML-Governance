"""Deterministic Phase 5 policy evaluator."""

from __future__ import annotations

import hashlib
import json

from .gates import evaluate_all_gates
from .models import EvidenceBundle, GovernanceDecision
from .policy import GovernancePolicy


class GovernanceEvaluator:
    def __init__(self, policy: GovernancePolicy):
        self.policy = policy

    def evaluate(
        self,
        *,
        model_name: str,
        model_version: str,
        current_stage: str,
        evidence: EvidenceBundle,
    ) -> GovernanceDecision:
        gates = evaluate_all_gates(evidence, self.policy)
        blocking_failures = [gate for gate in gates if gate.blocking and not gate.passed]
        decision = "APPROVE" if not blocking_failures else "REJECT"
        blocking_reasons = [f"{gate.name}: {gate.reason}" for gate in blocking_failures]
        evidence_hashes = {artifact.name: artifact.sha256 for artifact in evidence.artifacts}

        identity_payload = {
            "model_name": model_name,
            "model_version": model_version,
            "scenario": evidence.scenario,
            "decision": decision,
            "current_stage": current_stage,
            "requested_stage": self.policy.requested_stage,
            "policy_name": self.policy.name,
            "policy_version": self.policy.version,
            "gates": [gate.to_dict() for gate in gates],
            "evidence_hashes": evidence_hashes,
        }
        canonical = json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        decision_id = hashlib.sha256(canonical).hexdigest()[:20]

        return GovernanceDecision(
            decision_id=decision_id,
            model_name=model_name,
            model_version=model_version,
            scenario=evidence.scenario,
            decision=decision,
            current_stage=current_stage,
            requested_stage=self.policy.requested_stage,
            policy_name=self.policy.name,
            policy_version=self.policy.version,
            gates=gates,
            blocking_reasons=blocking_reasons,
            evidence_hashes=evidence_hashes,
        )
