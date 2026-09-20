"""Domain models for Phase 11 monitoring orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class MonitoringTaskSpec:
    task_id: str
    command: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    evidence_paths: tuple[str, ...] = ()
    max_attempts: int = 1


@dataclass
class MonitoringTaskResult:
    task_id: str
    status: str
    command: list[str]
    attempts: int
    return_code: int | None
    reason: str
    evidence_sha256: dict[str, str] = field(default_factory=dict)
    stdout_last_line: str = ""
    stderr_last_line: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MonitoringRun:
    run_id: str
    source_commit: str
    final_status: str
    fail_closed: bool
    automatic_retraining: bool
    automatic_promotion: bool
    tasks: list[MonitoringTaskResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "run_id": self.run_id,
            "source_commit": self.source_commit,
            "final_status": self.final_status,
            "fail_closed": self.fail_closed,
            "automatic_retraining": self.automatic_retraining,
            "automatic_promotion": self.automatic_promotion,
            "tasks": [task.to_dict() for task in self.tasks],
        }
