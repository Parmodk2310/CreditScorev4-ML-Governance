"""Domain models for deterministic Phase 5 governance decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceArtifact:
    """Immutable pointer to one evidence artifact and its content hash."""

    name: str
    path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceBundle:
    """Normalized evidence consumed by the Phase 5 policy engine."""

    scenario: str
    source: str
    quality_decision: str
    performance_metrics: dict[str, float]
    drift_status: str
    fairness_status: str
    artifacts: list[EvidenceArtifact] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "source": self.source,
            "quality_decision": self.quality_decision,
            "performance_metrics": self.performance_metrics,
            "drift_status": self.drift_status,
            "fairness_status": self.fairness_status,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class GovernanceGateResult:
    """Outcome of one configurable promotion policy gate."""

    name: str
    status: str
    passed: bool
    blocking: bool
    reason: str
    observed: Any
    expected: Any

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GovernanceDecision:
    """Auditable APPROVE/REJECT output for one candidate evaluation."""

    decision_id: str
    model_name: str
    model_version: str
    scenario: str
    decision: str
    current_stage: str
    requested_stage: str
    policy_name: str
    policy_version: str
    gates: list[GovernanceGateResult]
    blocking_reasons: list[str]
    evidence_hashes: dict[str, str]

    @property
    def approved(self) -> bool:
        return self.decision == "APPROVE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "scenario": self.scenario,
            "decision": self.decision,
            "current_stage": self.current_stage,
            "requested_stage": self.requested_stage,
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "gates": [gate.to_dict() for gate in self.gates],
            "blocking_reasons": self.blocking_reasons,
            "evidence_hashes": self.evidence_hashes,
        }
