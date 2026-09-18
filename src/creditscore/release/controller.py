"""Safe-release controller coordinating registry transitions and rollout gates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from creditscore.governance.audit_log import AuditLog
from creditscore.governance.registry import ModelRegistry

from .gates import ReleaseGateEvaluator, ReleasePolicy
from .models import ReleaseGateResult, ReleaseHealthSnapshot, ReleaseState
from .rollback import rollback_reason


class SafeReleaseController:
    def __init__(
        self,
        *,
        registry: ModelRegistry,
        audit_log: AuditLog,
        state_path: str | Path,
        model_name: str,
        model_version: str,
        canary_shares: list[float],
        shadow_policy: ReleasePolicy,
        canary_policy: ReleasePolicy,
    ) -> None:
        if not canary_shares:
            raise ValueError("At least one canary share is required")
        shares = [float(value) for value in canary_shares]
        if any(value <= 0.0 or value > 1.0 for value in shares):
            raise ValueError("Canary shares must be in (0, 1]")
        if shares != sorted(shares) or shares[-1] != 1.0:
            raise ValueError("Canary shares must be ascending and end at 1.0")

        self.registry = registry
        self.audit = audit_log
        self.state_path = Path(state_path)
        self.model_name = str(model_name)
        self.model_version = str(model_version)
        self.canary_shares = shares
        self.shadow_evaluator = ReleaseGateEvaluator(shadow_policy)
        self.canary_evaluator = ReleaseGateEvaluator(canary_policy)

    @classmethod
    def from_config(
        cls,
        *,
        root: str | Path,
        config: dict[str, Any],
        model_version: str | None = None,
    ) -> SafeReleaseController:
        root = Path(root)
        release = config["release"]
        gates = release["gates"]
        return cls(
            registry=ModelRegistry(root / str(release["registry_path"])),
            audit_log=AuditLog(root / str(release["audit_log"])),
            state_path=root / str(release["state_path"]),
            model_name=str(release["model_name"]),
            model_version=str(model_version or release["model_version"]),
            canary_shares=[float(value) for value in release["canary_shares"]],
            shadow_policy=ReleasePolicy.from_config(gates["shadow"]),
            canary_policy=ReleasePolicy.from_config(gates["canary"]),
        )

    def _save_state(self, state: ReleaseState) -> ReleaseState:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.state_path)
        return state

    def _read_state(self) -> ReleaseState:
        if not self.state_path.exists():
            record = self.registry.get(self.model_name, self.model_version)
            return ReleaseState(
                model_name=self.model_name,
                model_version=self.model_version,
                stage=record.stage,
            )
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        if payload.get("model_name") != self.model_name or payload.get("model_version") != self.model_version:
            record = self.registry.get(self.model_name, self.model_version)
            return ReleaseState(
                model_name=self.model_name,
                model_version=self.model_version,
                stage=record.stage,
            )
        payload["last_gate_results"] = []
        return ReleaseState(**payload)

    def start_shadow(self) -> ReleaseState:
        record = self.registry.get(self.model_name, self.model_version)
        if record.stage != "STAGING":
            raise ValueError(f"Shadow rollout requires STAGING; current stage is {record.stage}")
        record = self.registry.transition(
            model_name=self.model_name,
            version=self.model_version,
            target_stage="SHADOW",
        )
        state = ReleaseState(self.model_name, self.model_version, record.stage)
        self.audit.append("SHADOW_STARTED", state.to_dict())
        return self._save_state(state)

    def complete_shadow(self, snapshot: ReleaseHealthSnapshot) -> ReleaseState:
        state = self._read_state()
        if state.stage != "SHADOW":
            raise ValueError(f"Shadow evaluation requires SHADOW; current stage is {state.stage}")
        results = self.shadow_evaluator.evaluate(snapshot)
        state.last_gate_results = results
        self.audit.append(
            "SHADOW_EVALUATED",
            {"snapshot": snapshot.to_dict(), "gates": [result.to_dict() for result in results]},
        )
        if not all(result.passed for result in results):
            return self.rollback(results)

        record = self.registry.transition(
            model_name=self.model_name,
            version=self.model_version,
            target_stage="CANARY",
        )
        state.stage = record.stage
        state.canary_share = self.canary_shares[0]
        self.audit.append("CANARY_STARTED", state.to_dict())
        return self._save_state(state)

    def advance_canary(self, snapshot: ReleaseHealthSnapshot) -> ReleaseState:
        state = self._read_state()
        if state.stage != "CANARY":
            raise ValueError(f"Canary evaluation requires CANARY; current stage is {state.stage}")
        results = self.canary_evaluator.evaluate(snapshot)
        state.last_gate_results = results
        self.audit.append(
            "CANARY_EVALUATED",
            {
                "share": state.canary_share,
                "snapshot": snapshot.to_dict(),
                "gates": [result.to_dict() for result in results],
            },
        )
        if not all(result.passed for result in results):
            return self.rollback(results)

        state.completed_shares.append(state.canary_share)
        current_index = self.canary_shares.index(state.canary_share)
        if current_index == len(self.canary_shares) - 1:
            record = self.registry.transition(
                model_name=self.model_name,
                version=self.model_version,
                target_stage="PRODUCTION",
            )
            state.stage = record.stage
            state.canary_share = 1.0
            self.audit.append("PRODUCTION_PROMOTED", state.to_dict())
            return self._save_state(state)

        state.canary_share = self.canary_shares[current_index + 1]
        self.audit.append("CANARY_ADVANCED", state.to_dict())
        return self._save_state(state)

    def rollback(self, results: list[ReleaseGateResult] | None = None) -> ReleaseState:
        state = self._read_state()
        if state.stage not in {"SHADOW", "CANARY"}:
            raise ValueError(f"Rollback requires SHADOW or CANARY; current stage is {state.stage}")
        results = list(results or [])
        reason = rollback_reason(results)
        record = self.registry.transition(
            model_name=self.model_name,
            version=self.model_version,
            target_stage="STAGING",
        )
        state.stage = record.stage
        state.canary_share = 0.0
        state.rollback_reason = reason
        state.last_gate_results = results
        self.audit.append("RELEASE_ROLLED_BACK", state.to_dict())
        return self._save_state(state)
