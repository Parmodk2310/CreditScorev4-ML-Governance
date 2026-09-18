"""Serializable drift result models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SEVERITY_ORDER = {"STABLE": 0, "WARNING": 1, "CRITICAL": 2}


def maximum_severity(*statuses: str) -> str:
    return max(statuses, key=lambda value: SEVERITY_ORDER[value])


@dataclass(frozen=True)
class DriftMetricResult:
    feature: str
    psi: float
    psi_status: str
    ks_statistic: float
    ks_pvalue: float
    ks_status: str
    status: str
    reference_mean: float | None
    current_mean: float | None
    reference_null_rate: float
    current_null_rate: float
    reference_count: int
    current_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DriftReport:
    scenario: str
    reference_source: str
    current_source: str
    overall_status: str
    feature_results: list[DriftMetricResult] = field(default_factory=list)
    prediction_result: DriftMetricResult | None = None
    prediction_summary: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def critical_features(self) -> list[str]:
        return [result.feature for result in self.feature_results if result.status == "CRITICAL"]

    @property
    def warning_features(self) -> list[str]:
        return [result.feature for result in self.feature_results if result.status == "WARNING"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "reference_source": self.reference_source,
            "current_source": self.current_source,
            "overall_status": self.overall_status,
            "critical_features": self.critical_features,
            "warning_features": self.warning_features,
            "feature_results": [result.to_dict() for result in self.feature_results],
            "prediction_result": None if self.prediction_result is None else self.prediction_result.to_dict(),
            "prediction_summary": self.prediction_summary,
            "metadata": self.metadata,
        }
