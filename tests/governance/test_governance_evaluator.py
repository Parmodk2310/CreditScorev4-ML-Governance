from pathlib import Path

from creditscore.governance.evaluator import GovernanceEvaluator
from creditscore.governance.models import EvidenceArtifact, EvidenceBundle
from creditscore.governance.policy import GovernancePolicy
from creditscore.utils.hashing import file_sha256


def _policy() -> GovernancePolicy:
    gates = {
        "data_quality": {"required_decision": "PASS", "blocking": True},
        "performance": {"minimum_roc_auc": 0.75, "minimum_pr_auc": 0.60, "blocking": True},
        "calibration": {"maximum_brier_score": 0.20, "blocking": True},
        "drift": {"blocked_statuses": ["CRITICAL"], "blocking": True},
        "fairness": {"blocked_statuses": ["FAIL"], "blocking": True},
        "evidence_integrity": {"minimum_artifacts": 1, "blocking": True},
    }
    return GovernancePolicy.from_config(
        {
            "policy": {
                "name": "test_policy",
                "version": "1",
                "requested_stage": "STAGING",
                "gates": gates,
            }
        }
    )


def _artifact(tmp_path: Path) -> EvidenceArtifact:
    path = tmp_path / "evidence.json"
    path.write_text("{}", encoding="utf-8")
    return EvidenceArtifact("evidence", str(path), file_sha256(path), path.stat().st_size)


def _bundle(tmp_path: Path, *, drift="STABLE", fairness="PASS") -> EvidenceBundle:
    return EvidenceBundle(
        scenario="test",
        source="vendor_a",
        quality_decision="PASS",
        performance_metrics={"roc_auc": 0.80, "pr_auc": 0.68, "brier_score": 0.16},
        drift_status=drift,
        fairness_status=fairness,
        artifacts=[_artifact(tmp_path)],
    )


def test_evaluator_approves_healthy_evidence(tmp_path):
    decision = GovernanceEvaluator(_policy()).evaluate(
        model_name="CreditScoreV4",
        model_version="test",
        current_stage="CANDIDATE",
        evidence=_bundle(tmp_path),
    )
    assert decision.decision == "APPROVE"
    assert not decision.blocking_reasons


def test_evaluator_rejects_drift_or_fairness_failures(tmp_path):
    evaluator = GovernanceEvaluator(_policy())
    drift = evaluator.evaluate(
        model_name="CreditScoreV4",
        model_version="drift",
        current_stage="CANDIDATE",
        evidence=_bundle(tmp_path, drift="CRITICAL"),
    )
    fairness = evaluator.evaluate(
        model_name="CreditScoreV4",
        model_version="fairness",
        current_stage="CANDIDATE",
        evidence=_bundle(tmp_path, fairness="FAIL"),
    )
    assert drift.decision == "REJECT"
    assert fairness.decision == "REJECT"
    assert any(reason.startswith("drift:") for reason in drift.blocking_reasons)
    assert any(reason.startswith("fairness:") for reason in fairness.blocking_reasons)
