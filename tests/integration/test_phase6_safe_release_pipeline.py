from __future__ import annotations

from pathlib import Path

from creditscore.governance.audit_log import AuditLog
from creditscore.governance.registry import ModelRegistry
from creditscore.release.controller import SafeReleaseController
from creditscore.release.gates import ReleasePolicy
from creditscore.release.models import ReleaseHealthSnapshot


def test_staging_shadow_canary_production_and_rollback_are_governed(tmp_path: Path) -> None:
    registry = ModelRegistry(tmp_path / "registry.json")
    audit = AuditLog(tmp_path / "audit.jsonl")
    policy = ReleasePolicy(0.03, 300.0, 0.06, 100)

    for version in ("healthy", "degraded"):
        record = registry.register(
            model_name="CreditScoreV4",
            version=version,
            artifact_path="model.joblib",
            artifact_sha256="abc",
        )
        record = registry.transition(model_name=record.model_name, version=version, target_stage="CANDIDATE")
        registry.transition(model_name=record.model_name, version=version, target_stage="STAGING")

    healthy = SafeReleaseController(
        registry=registry,
        audit_log=audit,
        state_path=tmp_path / "healthy.json",
        model_name="CreditScoreV4",
        model_version="healthy",
        canary_shares=[0.10, 0.25, 0.50, 1.00],
        shadow_policy=policy,
        canary_policy=policy,
    )
    healthy.start_shadow()
    state = healthy.complete_shadow(ReleaseHealthSnapshot(200, 0.0, 40.0, 0.0))
    while state.stage == "CANARY":
        state = healthy.advance_canary(ReleaseHealthSnapshot(500, 0.005, 60.0, 0.01))

    degraded = SafeReleaseController(
        registry=registry,
        audit_log=audit,
        state_path=tmp_path / "degraded.json",
        model_name="CreditScoreV4",
        model_version="degraded",
        canary_shares=[0.10, 0.25, 0.50, 1.00],
        shadow_policy=policy,
        canary_policy=policy,
    )
    degraded.start_shadow()
    degraded.complete_shadow(ReleaseHealthSnapshot(200, 0.0, 40.0, 0.0))
    rollback = degraded.advance_canary(ReleaseHealthSnapshot(500, 0.10, 500.0, 0.20))

    assert state.stage == "PRODUCTION"
    assert rollback.stage == "STAGING"
    assert len(audit.read_all()) >= 10
