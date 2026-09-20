"""Typed Phase 9 business-impact evidence models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BusinessImpactMetrics:
    scenario: str
    sample_count: int
    approval_count: int
    approval_rate: float
    overall_default_rate: float
    approved_default_rate: float
    mean_predicted_risk: float
    approved_mean_predicted_risk: float
    device_risk_null_rate: float
    device_risk_observed_mean: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BusinessImpactComparison:
    same_population: bool
    same_labels: bool
    approval_rate_change: float
    approved_default_rate_change: float
    overall_default_rate_change: float
    mean_predicted_risk_change: float
    device_null_rate_change: float
    device_observed_mean_change: float
    newly_approved_count: int
    newly_rejected_count: int
    decision_flip_count: int
    decision_flip_rate: float
    newly_approved_default_rate: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
