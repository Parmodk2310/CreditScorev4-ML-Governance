from creditscore.governance.gates import (
    evaluate_calibration,
    evaluate_data_quality,
    evaluate_drift,
    evaluate_performance,
)
from creditscore.governance.models import EvidenceBundle
from creditscore.governance.policy import GovernancePolicy


def _policy() -> GovernancePolicy:
    return GovernancePolicy.from_config(
        {
            "policy": {
                "name": "test",
                "version": "1",
                "requested_stage": "STAGING",
                "gates": {
                    "data_quality": {"required_decision": "PASS", "blocking": True},
                    "performance": {
                        "minimum_roc_auc": 0.75,
                        "minimum_pr_auc": 0.60,
                        "blocking": True,
                    },
                    "calibration": {"maximum_brier_score": 0.20, "blocking": True},
                    "drift": {"blocked_statuses": ["CRITICAL"], "blocking": True},
                },
            }
        }
    )


def _bundle(**overrides) -> EvidenceBundle:
    payload = {
        "scenario": "test",
        "source": "vendor_a",
        "quality_decision": "PASS",
        "performance_metrics": {"roc_auc": 0.80, "pr_auc": 0.68, "brier_score": 0.16},
        "drift_status": "STABLE",
        "fairness_status": "PASS",
    }
    payload.update(overrides)
    return EvidenceBundle(**payload)


def test_quality_gate_blocks_failed_data_quality():
    result = evaluate_data_quality(_bundle(quality_decision="BLOCK"), _policy())
    assert not result.passed
    assert result.blocking


def test_performance_and_calibration_gates_enforce_thresholds():
    bundle = _bundle(performance_metrics={"roc_auc": 0.74, "pr_auc": 0.59, "brier_score": 0.21})
    assert not evaluate_performance(bundle, _policy()).passed
    assert not evaluate_calibration(bundle, _policy()).passed


def test_drift_gate_blocks_critical_status():
    result = evaluate_drift(_bundle(drift_status="CRITICAL"), _policy())
    assert not result.passed
