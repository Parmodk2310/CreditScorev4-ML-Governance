"""Serializable fairness assessment models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SEVERITY_ORDER = {"PASS": 0, "WARNING": 1, "FAIL": 2}


def maximum_status(*statuses: str) -> str:
    if not statuses:
        return "PASS"
    return max(statuses, key=lambda status: SEVERITY_ORDER[status])


@dataclass(frozen=True)
class GroupMetrics:
    sensitive_feature: str
    group: str
    sample_count: int
    approval_rate: float
    predicted_default_rate: float
    actual_default_rate: float
    mean_predicted_risk: float
    accuracy: float
    true_positive_rate: float
    false_positive_rate: float
    false_negative_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SensitiveFeatureAssessment:
    sensitive_feature: str
    status: str
    demographic_parity_ratio: float
    demographic_parity_difference: float
    equalized_odds_difference: float
    group_metrics: list[GroupMetrics] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sensitive_feature": self.sensitive_feature,
            "status": self.status,
            "demographic_parity_ratio": self.demographic_parity_ratio,
            "demographic_parity_difference": self.demographic_parity_difference,
            "equalized_odds_difference": self.equalized_odds_difference,
            "group_metrics": [metric.to_dict() for metric in self.group_metrics],
        }


@dataclass
class FairnessReport:
    scenario: str
    primary_sensitive_feature: str
    overall_status: str
    reference: list[SensitiveFeatureAssessment]
    current: list[SensitiveFeatureAssessment]
    primary_metric_delta: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def current_primary(self) -> SensitiveFeatureAssessment:
        return next(item for item in self.current if item.sensitive_feature == self.primary_sensitive_feature)

    @property
    def reference_primary(self) -> SensitiveFeatureAssessment:
        return next(
            item for item in self.reference if item.sensitive_feature == self.primary_sensitive_feature
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "primary_sensitive_feature": self.primary_sensitive_feature,
            "overall_status": self.overall_status,
            "reference": [item.to_dict() for item in self.reference],
            "current": [item.to_dict() for item in self.current],
            "primary_metric_delta": self.primary_metric_delta,
            "metadata": self.metadata,
        }
