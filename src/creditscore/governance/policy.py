"""Configuration-backed model promotion policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GovernancePolicy:
    name: str
    version: str
    requested_stage: str
    gates: dict[str, dict[str, Any]]

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> GovernancePolicy:
        payload = config["policy"]
        return cls(
            name=str(payload["name"]),
            version=str(payload["version"]),
            requested_stage=str(payload["requested_stage"]),
            gates={str(name): dict(spec) for name, spec in payload["gates"].items()},
        )

    def gate(self, name: str) -> dict[str, Any]:
        if name not in self.gates:
            raise KeyError(f"Unknown governance gate: {name}")
        return self.gates[name]
