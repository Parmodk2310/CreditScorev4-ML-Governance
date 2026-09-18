"""Pure governance gate functions used by the Phase 5 evaluator."""

from __future__ import annotations

from typing import Any

from .models import EvidenceBundle, GovernanceGateResult
from .policy import GovernancePolicy


def _result(
    name: str,
    *,
    passed: bool,
    blocking: bool,
    reason: str,
    observed: Any,
    expected: Any,
) -> GovernanceGateResult:
    return GovernanceGateResult(
        name=name,
        status="PASS" if passed else "FAIL",
        passed=passed,
        blocking=blocking,
        reason=reason,
        observed=observed,
        expected=expected,
    )


def evaluate_data_quality(bundle: EvidenceBundle, policy: GovernancePolicy) -> GovernanceGateResult:
    spec = policy.gate("data_quality")
    expected = str(spec["required_decision"])
    passed = bundle.quality_decision == expected
    return _result(
        "data_quality",
        passed=passed,
        blocking=bool(spec["blocking"]),
        reason=(
            "Data-quality evidence satisfies the required decision."
            if passed
            else f"Data-quality decision is {bundle.quality_decision}; required {expected}."
        ),
        observed=bundle.quality_decision,
        expected=expected,
    )


def evaluate_performance(bundle: EvidenceBundle, policy: GovernancePolicy) -> GovernanceGateResult:
    spec = policy.gate("performance")
    roc_auc = float(bundle.performance_metrics["roc_auc"])
    pr_auc = float(bundle.performance_metrics["pr_auc"])
    min_roc = float(spec["minimum_roc_auc"])
    min_pr = float(spec["minimum_pr_auc"])
    passed = roc_auc >= min_roc and pr_auc >= min_pr
    return _result(
        "performance",
        passed=passed,
        blocking=bool(spec["blocking"]),
        reason=(
            "Discrimination metrics satisfy the promotion policy."
            if passed
            else "Performance evidence is below a configured promotion threshold."
        ),
        observed={"roc_auc": roc_auc, "pr_auc": pr_auc},
        expected={"minimum_roc_auc": min_roc, "minimum_pr_auc": min_pr},
    )


def evaluate_calibration(bundle: EvidenceBundle, policy: GovernancePolicy) -> GovernanceGateResult:
    spec = policy.gate("calibration")
    brier = float(bundle.performance_metrics["brier_score"])
    maximum = float(spec["maximum_brier_score"])
    passed = brier <= maximum
    return _result(
        "calibration",
        passed=passed,
        blocking=bool(spec["blocking"]),
        reason=(
            "Brier score satisfies the configured calibration guardrail."
            if passed
            else "Brier score exceeds the configured calibration guardrail."
        ),
        observed=brier,
        expected={"maximum_brier_score": maximum},
    )


def evaluate_drift(bundle: EvidenceBundle, policy: GovernancePolicy) -> GovernanceGateResult:
    spec = policy.gate("drift")
    blocked = {str(value) for value in spec["blocked_statuses"]}
    passed = bundle.drift_status not in blocked
    return _result(
        "drift",
        passed=passed,
        blocking=bool(spec["blocking"]),
        reason=(
            "Drift evidence is within the configured promotion policy."
            if passed
            else f"Drift status {bundle.drift_status} is blocking."
        ),
        observed=bundle.drift_status,
        expected={"blocked_statuses": sorted(blocked)},
    )


def evaluate_fairness(bundle: EvidenceBundle, policy: GovernancePolicy) -> GovernanceGateResult:
    spec = policy.gate("fairness")
    blocked = {str(value) for value in spec["blocked_statuses"]}
    passed = bundle.fairness_status not in blocked
    return _result(
        "fairness",
        passed=passed,
        blocking=bool(spec["blocking"]),
        reason=(
            "Fairness evidence is within the configured promotion policy."
            if passed
            else f"Fairness status {bundle.fairness_status} is blocking."
        ),
        observed=bundle.fairness_status,
        expected={"blocked_statuses": sorted(blocked)},
    )


def evaluate_evidence_integrity(bundle: EvidenceBundle, policy: GovernancePolicy) -> GovernanceGateResult:
    spec = policy.gate("evidence_integrity")
    minimum = int(spec["minimum_artifacts"])
    valid = [artifact for artifact in bundle.artifacts if artifact.sha256 and artifact.size_bytes > 0]
    passed = len(valid) >= minimum and len(valid) == len(bundle.artifacts)
    return _result(
        "evidence_integrity",
        passed=passed,
        blocking=bool(spec["blocking"]),
        reason=(
            "All referenced evidence artifacts have content hashes."
            if passed
            else "Evidence bundle is incomplete or contains an unhashed artifact."
        ),
        observed={"valid_artifacts": len(valid), "total_artifacts": len(bundle.artifacts)},
        expected={"minimum_artifacts": minimum, "all_artifacts_hashed": True},
    )


def evaluate_all_gates(bundle: EvidenceBundle, policy: GovernancePolicy) -> list[GovernanceGateResult]:
    return [
        evaluate_data_quality(bundle, policy),
        evaluate_performance(bundle, policy),
        evaluate_calibration(bundle, policy),
        evaluate_drift(bundle, policy),
        evaluate_fairness(bundle, policy),
        evaluate_evidence_integrity(bundle, policy),
    ]
