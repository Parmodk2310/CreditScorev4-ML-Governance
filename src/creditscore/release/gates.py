"""Shadow/canary health gates used by the safe-release controller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import ReleaseGateResult, ReleaseHealthSnapshot


@dataclass(frozen=True)
class ReleasePolicy:
    maximum_error_rate: float
    maximum_p95_latency_ms: float
    maximum_mean_risk_delta: float
    minimum_request_count: int

    @classmethod
    def from_config(cls, payload: dict[str, Any]) -> ReleasePolicy:
        return cls(
            maximum_error_rate=float(payload["maximum_error_rate"]),
            maximum_p95_latency_ms=float(payload["maximum_p95_latency_ms"]),
            maximum_mean_risk_delta=float(payload["maximum_mean_risk_delta"]),
            minimum_request_count=int(payload["minimum_request_count"]),
        )


class ReleaseGateEvaluator:
    def __init__(self, policy: ReleasePolicy) -> None:
        self.policy = policy

    def evaluate(self, snapshot: ReleaseHealthSnapshot) -> list[ReleaseGateResult]:
        return [
            ReleaseGateResult(
                name="minimum_request_count",
                passed=snapshot.request_count >= self.policy.minimum_request_count,
                observed=snapshot.request_count,
                expected=self.policy.minimum_request_count,
                reason="Enough traffic has been observed for this rollout checkpoint.",
            ),
            ReleaseGateResult(
                name="error_rate",
                passed=snapshot.error_rate <= self.policy.maximum_error_rate,
                observed=snapshot.error_rate,
                expected=self.policy.maximum_error_rate,
                reason="Serving error rate must remain below the configured release ceiling.",
            ),
            ReleaseGateResult(
                name="p95_latency_ms",
                passed=snapshot.p95_latency_ms <= self.policy.maximum_p95_latency_ms,
                observed=snapshot.p95_latency_ms,
                expected=self.policy.maximum_p95_latency_ms,
                reason="P95 serving latency must remain below the configured release ceiling.",
            ),
            ReleaseGateResult(
                name="mean_risk_delta",
                passed=abs(snapshot.mean_risk_delta) <= self.policy.maximum_mean_risk_delta,
                observed=abs(snapshot.mean_risk_delta),
                expected=self.policy.maximum_mean_risk_delta,
                reason="Candidate risk output must remain close to the comparison baseline.",
            ),
        ]

    def passes(self, snapshot: ReleaseHealthSnapshot) -> bool:
        return all(result.passed for result in self.evaluate(snapshot))
