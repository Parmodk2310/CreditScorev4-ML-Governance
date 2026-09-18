#!/usr/bin/env python3
"""Demonstrate automatic rollback when canary health violates release gates."""

from __future__ import annotations

from pathlib import Path

from creditscore.governance.registry import ModelRegistry
from creditscore.release.controller import SafeReleaseController
from creditscore.release.models import ReleaseHealthSnapshot
from creditscore.utils.config import load_yaml
from creditscore.utils.hashing import file_sha256

ROOT = Path(__file__).resolve().parents[1]
ROLLBACK_VERSION = "0.6.0-rollback-demo"


def _stage_candidate(config: dict) -> None:
    release = config["release"]
    registry = ModelRegistry(ROOT / release["registry_path"])
    model_path = ROOT / config["serving"]["model_path"]
    record = registry.register(
        model_name=str(release["model_name"]),
        version=ROLLBACK_VERSION,
        artifact_path=str(model_path),
        artifact_sha256=file_sha256(model_path),
        metadata={"scenario": "phase6_rollback_demo"},
    )
    if record.stage == "REGISTERED":
        record = registry.transition(
            model_name=record.model_name,
            version=record.version,
            target_stage="CANDIDATE",
        )
    if record.stage == "CANDIDATE":
        registry.transition(model_name=record.model_name, version=record.version, target_stage="STAGING")


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase6.yaml")
    _stage_candidate(config)
    controller = SafeReleaseController.from_config(
        root=ROOT,
        config=config,
        model_version=ROLLBACK_VERSION,
    )
    controller.start_shadow()
    controller.complete_shadow(ReleaseHealthSnapshot(200, 0.001, 40.0, 0.0))
    state = controller.advance_canary(ReleaseHealthSnapshot(500, 0.09, 480.0, 0.15))
    print(f"Rollback stage: {state.stage}")
    print(f"Rollback reason: {state.rollback_reason}")
    return 0 if state.stage == "STAGING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
