"""Typed evidence models for Phase 10 root-cause analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RootCauseScenarioMetrics:
    scenario: str
    sample_count: int
    roc_auc: float
    pr_auc: float
    brier_score: float
    approval_rate: float
    approved_default_rate: float
    mean_predicted_risk: float
    device_risk_null_rate: float
    decision_flip_count_vs_healthy: int
    decision_flip_rate_vs_healthy: float
    newly_approved_count_vs_healthy: int
    newly_rejected_count_vs_healthy: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
