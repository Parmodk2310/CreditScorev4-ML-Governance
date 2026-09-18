from __future__ import annotations

from pathlib import Path

import pytest

from creditscore.governance.audit_log import AuditLog
from creditscore.governance.registry import ModelRegistry, RegistryTransitionError
from creditscore.release.controller import SafeReleaseController
from creditscore.release.gates import ReleasePolicy
from creditscore.release.models import ReleaseHealthSnapshot

POLICY = ReleasePolicy(0.03, 300.0, 0.06, 100)


def _staged_registry(tmp_path: Path, version: str = "candidate") -> ModelRegistry:
    registry = ModelRegistry(tmp_path / "registry.json")
    record = registry.register(
        model_name="CreditScoreV4",
        version=version,
        artifact_path="model.joblib",
        artifact_sha256="abc",
    )
    record = registry.transition(
        model_name=record.model_name,
        version=record.version,
        target_stage="CANDIDATE",
    )
    registry.transition(model_name=record.model_name, version=record.version, target_stage="STAGING")
    return registry


def _controller(tmp_path: Path, registry: ModelRegistry, version: str = "candidate") -> SafeReleaseController:
    return SafeReleaseController(
        registry=registry,
        audit_log=AuditLog(tmp_path / "audit.jsonl"),
        state_path=tmp_path / "release.json",
        model_name="CreditScoreV4",
        model_version=version,
        canary_shares=[0.10, 0.25, 0.50, 1.00],
        shadow_policy=POLICY,
        canary_policy=POLICY,
    )


def test_healthy_release_reaches_production(tmp_path: Path) -> None:
    registry = _staged_registry(tmp_path)
    controller = _controller(tmp_path, registry)
    controller.start_shadow()
    state = controller.complete_shadow(ReleaseHealthSnapshot(200, 0.0, 40.0, 0.0))
    while state.stage == "CANARY":
        state = controller.advance_canary(ReleaseHealthSnapshot(500, 0.005, 60.0, 0.01))
    assert state.stage == "PRODUCTION"
    assert state.completed_shares == [0.10, 0.25, 0.50, 1.00]


def test_degraded_canary_rolls_back_to_staging(tmp_path: Path) -> None:
    registry = _staged_registry(tmp_path)
    controller = _controller(tmp_path, registry)
    controller.start_shadow()
    controller.complete_shadow(ReleaseHealthSnapshot(200, 0.0, 40.0, 0.0))
    state = controller.advance_canary(ReleaseHealthSnapshot(500, 0.08, 450.0, 0.12))
    assert state.stage == "STAGING"
    assert state.rollback_reason is not None


def test_direct_candidate_to_production_remains_blocked(tmp_path: Path) -> None:
    registry = ModelRegistry(tmp_path / "registry.json")
    record = registry.register(
        model_name="CreditScoreV4",
        version="illegal",
        artifact_path="model.joblib",
        artifact_sha256="abc",
    )
    record = registry.transition(
        model_name=record.model_name,
        version=record.version,
        target_stage="CANDIDATE",
    )
    with pytest.raises(RegistryTransitionError):
        registry.transition(model_name=record.model_name, version=record.version, target_stage="PRODUCTION")
