"""Serializable validation result models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuleResult:
    """Outcome of one data-quality rule."""

    rule_id: str
    passed: bool
    severity: str
    observed: Any
    expected: Any
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DataQualityReport:
    """Structured report produced by one validation engine."""

    engine: str
    batch_name: str
    source: str
    passed: bool
    row_count: int
    rules: list[RuleResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def failed_rule_ids(self) -> list[str]:
        return [rule.rule_id for rule in self.rules if not rule.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "batch_name": self.batch_name,
            "source": self.source,
            "passed": self.passed,
            "row_count": self.row_count,
            "failed_rule_ids": self.failed_rule_ids,
            "rules": [rule.to_dict() for rule in self.rules],
            "metadata": self.metadata,
        }
