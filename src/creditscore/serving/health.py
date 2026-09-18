"""Simple liveness/readiness helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceHealth:
    alive: bool
    model_ready: bool

    @property
    def ready(self) -> bool:
        return self.alive and self.model_ready
