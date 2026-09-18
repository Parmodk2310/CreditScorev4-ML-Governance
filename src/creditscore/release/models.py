"""Domain models for Phase 6 safe-release orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReleaseHealthSnapshot:
    request_count: int
    error_rate: float
    p95_latency_ms: float
    mean_risk_delta: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReleaseGateResult:
    name: str
    passed: bool
    observed: float | int
    expected: float | int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReleaseState:
    model_name: str
    model_version: str
    stage: str
    canary_share: float = 0.0
    completed_shares: list[float] = field(default_factory=list)
    rollback_reason: str | None = None
    last_gate_results: list[ReleaseGateResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "stage": self.stage,
            "canary_share": self.canary_share,
            "completed_shares": list(self.completed_shares),
            "rollback_reason": self.rollback_reason,
            "last_gate_results": [item.to_dict() for item in self.last_gate_results],
        }
