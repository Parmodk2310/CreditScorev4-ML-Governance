"""Apply governance decisions to the model registry and audit trail."""

from __future__ import annotations

from .audit_log import AuditLog
from .evaluator import GovernanceEvaluator
from .models import EvidenceBundle, GovernanceDecision
from .registry import ModelRegistry


class GovernanceDecisionService:
    def __init__(
        self,
        *,
        evaluator: GovernanceEvaluator,
        registry: ModelRegistry,
        audit_log: AuditLog,
        approved_stage: str,
        rejected_stage: str,
    ):
        self.evaluator = evaluator
        self.registry = registry
        self.audit_log = audit_log
        self.approved_stage = approved_stage
        self.rejected_stage = rejected_stage

    def evaluate_and_apply(
        self,
        *,
        model_name: str,
        model_version: str,
        evidence: EvidenceBundle,
    ) -> tuple[GovernanceDecision, str]:
        record = self.registry.get(model_name, model_version)
        decision = self.evaluator.evaluate(
            model_name=model_name,
            model_version=model_version,
            current_stage=record.stage,
            evidence=evidence,
        )
        self.audit_log.append("GOVERNANCE_EVALUATED", decision.to_dict())

        target = self.approved_stage if decision.approved else self.rejected_stage
        updated = self.registry.transition(
            model_name=model_name,
            version=model_version,
            target_stage=target,
            decision_id=decision.decision_id,
        )
        self.audit_log.append(
            "REGISTRY_TRANSITION",
            {
                "model_name": model_name,
                "model_version": model_version,
                "decision_id": decision.decision_id,
                "target_stage": updated.stage,
            },
        )
        return decision, updated.stage
