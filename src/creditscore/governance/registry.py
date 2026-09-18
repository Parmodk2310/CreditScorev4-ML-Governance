"""Small auditable JSON model registry with explicit lifecycle transitions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class RegistryTransitionError(ValueError):
    """Raised when a model lifecycle transition violates the state machine."""


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "REGISTERED": {"CANDIDATE"},
    "CANDIDATE": {"STAGING", "REJECTED"},
    "STAGING": set(),
    "REJECTED": set(),
    # Reserved for Phase 6. They are known stages but cannot be reached by Phase 5.
    "SHADOW": set(),
    "CANARY": set(),
    "PRODUCTION": set(),
}


@dataclass
class ModelVersionRecord:
    model_name: str
    version: str
    artifact_path: str
    artifact_sha256: str
    stage: str
    metadata: dict[str, Any] = field(default_factory=dict)
    last_decision_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ModelRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "models": {}}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or "models" not in payload:
            raise ValueError(f"Invalid registry file: {self.path}")
        return payload

    def _save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def _key(model_name: str, version: str) -> str:
        return f"{model_name}:{version}"

    def register(
        self,
        *,
        model_name: str,
        version: str,
        artifact_path: str,
        artifact_sha256: str,
        metadata: dict[str, Any] | None = None,
    ) -> ModelVersionRecord:
        payload = self._load()
        key = self._key(model_name, version)
        existing = payload["models"].get(key)
        if existing is not None:
            return ModelVersionRecord(**existing)

        record = ModelVersionRecord(
            model_name=model_name,
            version=version,
            artifact_path=artifact_path,
            artifact_sha256=artifact_sha256,
            stage="REGISTERED",
            metadata=dict(metadata or {}),
        )
        payload["models"][key] = record.to_dict()
        self._save(payload)
        return record

    def get(self, model_name: str, version: str) -> ModelVersionRecord:
        payload = self._load()
        key = self._key(model_name, version)
        if key not in payload["models"]:
            raise KeyError(f"Model version is not registered: {key}")
        return ModelVersionRecord(**payload["models"][key])

    def transition(
        self,
        *,
        model_name: str,
        version: str,
        target_stage: str,
        decision_id: str | None = None,
    ) -> ModelVersionRecord:
        target_stage = str(target_stage).upper()
        if target_stage not in ALLOWED_TRANSITIONS:
            raise RegistryTransitionError(f"Unknown registry stage: {target_stage}")

        payload = self._load()
        key = self._key(model_name, version)
        if key not in payload["models"]:
            raise KeyError(f"Model version is not registered: {key}")

        record = ModelVersionRecord(**payload["models"][key])
        allowed = ALLOWED_TRANSITIONS.get(record.stage, set())
        if target_stage not in allowed:
            raise RegistryTransitionError(
                f"Illegal model transition: {record.stage} -> {target_stage} for {key}"
            )

        record.stage = target_stage
        record.last_decision_id = decision_id
        payload["models"][key] = record.to_dict()
        self._save(payload)
        return record

    def list_versions(self) -> list[ModelVersionRecord]:
        payload = self._load()
        return [ModelVersionRecord(**item) for _, item in sorted(payload["models"].items())]
