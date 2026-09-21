from __future__ import annotations

from pathlib import Path

from creditscore.governance.registry import ModelRegistry
from creditscore.serving.app import _expected_model_sha256
from scripts.serve_model import apply_environment_overrides


def test_expected_model_sha256_uses_companion_digest(tmp_path: Path) -> None:
    digest_path = tmp_path / "model.joblib.sha256"
    digest_path.write_text("companion-sha\n", encoding="utf-8")
    config = {
        "serving": {
            "model_path": "model.joblib",
            "model_digest_path": "model.joblib.sha256",
            "model_name": "CreditScoreV4",
            "model_version": "test",
        }
    }

    assert _expected_model_sha256(tmp_path, config) == "companion-sha"


def test_expected_model_sha256_prefers_governance_registry(tmp_path: Path) -> None:
    digest_path = tmp_path / "model.joblib.sha256"
    digest_path.write_text("companion-sha\n", encoding="utf-8")
    registry = ModelRegistry(tmp_path / "registry.json")
    registry.register(
        model_name="CreditScoreV4",
        version="test",
        artifact_path="model.joblib",
        artifact_sha256="registry-sha",
    )
    config = {
        "serving": {
            "model_path": "model.joblib",
            "model_digest_path": "model.joblib.sha256",
            "model_name": "CreditScoreV4",
            "model_version": "test",
        },
        "release": {"registry_path": "registry.json"},
    }

    assert _expected_model_sha256(tmp_path, config) == "registry-sha"


def test_model_path_environment_override_uses_companion_digest(monkeypatch) -> None:
    config = {
        "serving": {
            "model_path": "models/original.joblib",
            "model_digest_path": "models/original.joblib.sha256",
        }
    }
    monkeypatch.setenv("CREDITSCORE_MODEL_PATH", "/tmp/override.joblib")
    monkeypatch.delenv("CREDITSCORE_MODEL_DIGEST_PATH", raising=False)

    updated = apply_environment_overrides(config)

    assert updated["serving"]["model_path"] == "/tmp/override.joblib"
    assert updated["serving"]["model_digest_path"] == "/tmp/override.joblib.sha256"
    assert config["serving"]["model_path"] == "models/original.joblib"
