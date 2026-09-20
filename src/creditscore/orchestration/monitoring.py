"""Fail-closed task orchestration for scheduled governance monitoring."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from creditscore.utils.hashing import file_sha256

from .models import MonitoringRun, MonitoringTaskResult, MonitoringTaskSpec


def load_task_specs(config: dict[str, Any]) -> list[MonitoringTaskSpec]:
    execution = config["execution"]
    default_attempts = int(execution["max_attempts"])
    specs: list[MonitoringTaskSpec] = []

    for payload in config["orchestration"]["tasks"]:
        specs.append(
            MonitoringTaskSpec(
                task_id=str(payload["id"]),
                command=tuple(str(token) for token in payload["command"]),
                depends_on=tuple(str(value) for value in payload.get("depends_on", [])),
                evidence_paths=tuple(str(value) for value in payload.get("evidence", [])),
                max_attempts=int(payload.get("max_attempts", default_attempts)),
            )
        )

    validate_task_graph(specs)
    return specs


def validate_task_graph(specs: list[MonitoringTaskSpec]) -> None:
    if not specs:
        raise ValueError("Phase 11 requires at least one monitoring task")

    ids = [spec.task_id for spec in specs]
    if len(ids) != len(set(ids)):
        raise ValueError("Monitoring task ids must be unique")

    known = set(ids)
    for spec in specs:
        if spec.max_attempts < 1:
            raise ValueError(f"Task {spec.task_id} must allow at least one attempt")
        if spec.task_id in spec.depends_on:
            raise ValueError(f"Task {spec.task_id} cannot depend on itself")
        unknown = set(spec.depends_on) - known
        if unknown:
            raise ValueError(f"Task {spec.task_id} has unknown dependencies: {sorted(unknown)}")

    visiting: set[str] = set()
    visited: set[str] = set()
    deps = {spec.task_id: set(spec.depends_on) for spec in specs}

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            raise ValueError("Monitoring task graph contains a cycle")
        visiting.add(task_id)
        for dependency in deps[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in ids:
        visit(task_id)


def topological_order(specs: list[MonitoringTaskSpec]) -> list[MonitoringTaskSpec]:
    by_id = {spec.task_id: spec for spec in specs}
    remaining = set(by_id)
    ordered: list[MonitoringTaskSpec] = []

    while remaining:
        progressed = False
        for spec in specs:
            if spec.task_id not in remaining:
                continue
            if all(dependency not in remaining for dependency in spec.depends_on):
                ordered.append(spec)
                remaining.remove(spec.task_id)
                progressed = True
        if not progressed:
            raise ValueError("Monitoring task graph could not be ordered")

    return ordered


def _resolved_command(command: tuple[str, ...]) -> list[str]:
    if not command:
        raise ValueError("Monitoring task command cannot be empty")
    resolved = list(command)
    if resolved[0] == "python":
        resolved[0] = sys.executable
    return resolved


def _last_nonempty_line(text: str) -> str:
    for line in reversed(text.splitlines()):
        if line.strip():
            return line.strip()
    return ""


class MonitoringOrchestrator:
    def __init__(self, *, root: Path, config: dict[str, Any]):
        self.root = root
        self.config = config
        self.specs = topological_order(load_task_specs(config))
        self.retry_delay_seconds = float(config["execution"]["retry_delay_seconds"])

    def run(self, *, run_id: str, source_commit: str) -> MonitoringRun:
        results: list[MonitoringTaskResult] = []
        by_id: dict[str, MonitoringTaskResult] = {}

        for spec in self.specs:
            failed_dependencies = [
                dependency for dependency in spec.depends_on if by_id[dependency].status != "PASS"
            ]
            if failed_dependencies:
                result = MonitoringTaskResult(
                    task_id=spec.task_id,
                    status="SKIPPED",
                    command=_resolved_command(spec.command),
                    attempts=0,
                    return_code=None,
                    reason=("fail-closed dependency block: " + ", ".join(failed_dependencies)),
                )
                results.append(result)
                by_id[spec.task_id] = result
                continue

            result = self._execute(spec)
            results.append(result)
            by_id[spec.task_id] = result

        final_status = "PASS" if results and all(result.status == "PASS" for result in results) else "FAIL"
        return MonitoringRun(
            run_id=run_id,
            source_commit=source_commit,
            final_status=final_status,
            fail_closed=bool(self.config["orchestration"]["fail_closed"]),
            automatic_retraining=bool(self.config["orchestration"]["automatic_retraining"]),
            automatic_promotion=bool(self.config["orchestration"]["automatic_promotion"]),
            tasks=results,
        )

    def _execute(self, spec: MonitoringTaskSpec) -> MonitoringTaskResult:
        command = _resolved_command(spec.command)
        environment = os.environ.copy()
        src_path = str(self.root / "src")
        existing_pythonpath = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = (
            src_path if not existing_pythonpath else f"{src_path}:{existing_pythonpath}"
        )

        completed: subprocess.CompletedProcess[str] | None = None
        attempts = 0
        for attempts in range(1, spec.max_attempts + 1):
            completed = subprocess.run(
                command,
                cwd=self.root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode == 0:
                break
            if attempts < spec.max_attempts and self.retry_delay_seconds > 0:
                time.sleep(self.retry_delay_seconds)

        if completed is None:
            raise RuntimeError(f"Task {spec.task_id} was not executed")

        evidence_hashes: dict[str, str] = {}
        missing_evidence: list[str] = []
        if completed.returncode == 0:
            for relative in spec.evidence_paths:
                path = self.root / relative
                if not path.exists():
                    missing_evidence.append(relative)
                elif path.is_file():
                    evidence_hashes[relative] = file_sha256(path)

        if completed.returncode != 0:
            status = "FAIL"
            reason = f"command exited with code {completed.returncode}"
        elif missing_evidence:
            status = "FAIL"
            reason = "expected evidence missing: " + ", ".join(missing_evidence)
        else:
            status = "PASS"
            reason = "command and evidence contract passed"

        return MonitoringTaskResult(
            task_id=spec.task_id,
            status=status,
            command=command,
            attempts=attempts,
            return_code=completed.returncode,
            reason=reason,
            evidence_sha256=evidence_hashes,
            stdout_last_line=_last_nonempty_line(completed.stdout),
            stderr_last_line=_last_nonempty_line(completed.stderr),
        )
