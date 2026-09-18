from pathlib import Path

from creditscore.governance.audit_log import AuditLog
from creditscore.governance.decision import GovernanceDecisionService
from creditscore.governance.evaluator import GovernanceEvaluator
from creditscore.governance.models import EvidenceArtifact, EvidenceBundle
from creditscore.governance.policy import GovernancePolicy
from creditscore.governance.registry import ModelRegistry
from creditscore.utils.hashing import file_sha256


def test_same_policy_approves_healthy_and_rejects_drift_and_fairness(tmp_path: Path):
    artifact = tmp_path / "model.joblib"
    artifact.write_bytes(b"model")
    evidence_file = tmp_path / "evidence.json"
    evidence_file.write_text("{}", encoding="utf-8")
    evidence_artifact = EvidenceArtifact(
        "evidence",
        str(evidence_file),
        file_sha256(evidence_file),
        evidence_file.stat().st_size,
    )

    gates = {
        "data_quality": {"required_decision": "PASS", "blocking": True},
        "performance": {"minimum_roc_auc": 0.75, "minimum_pr_auc": 0.60, "blocking": True},
        "calibration": {"maximum_brier_score": 0.20, "blocking": True},
        "drift": {"blocked_statuses": ["CRITICAL"], "blocking": True},
        "fairness": {"blocked_statuses": ["FAIL"], "blocking": True},
        "evidence_integrity": {"minimum_artifacts": 1, "blocking": True},
    }
    policy = GovernancePolicy.from_config(
        {
            "policy": {
                "name": "integration",
                "version": "1",
                "requested_stage": "STAGING",
                "gates": gates,
            }
        }
    )
    registry = ModelRegistry(tmp_path / "registry.json")
    audit = AuditLog(tmp_path / "audit.jsonl")
    service = GovernanceDecisionService(
        evaluator=GovernanceEvaluator(policy),
        registry=registry,
        audit_log=audit,
        approved_stage="STAGING",
        rejected_stage="REJECTED",
    )

    outcomes = {}
    for version, drift, fairness in (
        ("healthy", "STABLE", "PASS"),
        ("drift", "CRITICAL", "PASS"),
        ("fairness", "STABLE", "FAIL"),
    ):
        registry.register(
            model_name="CreditScoreV4",
            version=version,
            artifact_path=str(artifact),
            artifact_sha256=file_sha256(artifact),
        )
        registry.transition(model_name="CreditScoreV4", version=version, target_stage="CANDIDATE")
        bundle = EvidenceBundle(
            scenario=version,
            source="synthetic",
            quality_decision="PASS",
            performance_metrics={"roc_auc": 0.80, "pr_auc": 0.68, "brier_score": 0.16},
            drift_status=drift,
            fairness_status=fairness,
            artifacts=[evidence_artifact],
        )
        decision, stage = service.evaluate_and_apply(
            model_name="CreditScoreV4",
            model_version=version,
            evidence=bundle,
        )
        outcomes[version] = (decision.decision, stage)

    assert outcomes["healthy"] == ("APPROVE", "STAGING")
    assert outcomes["drift"] == ("REJECT", "REJECTED")
    assert outcomes["fairness"] == ("REJECT", "REJECTED")
