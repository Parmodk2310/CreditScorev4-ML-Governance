#!/usr/bin/env python3
"""Validate structural integrity of every GitHub Actions workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"


def _fail(path: Path, message: str) -> None:
    raise ValueError(f"{path.relative_to(ROOT)}: {message}")


def _validate_step(path: Path, index: int, step: Any) -> None:
    if not isinstance(step, dict):
        _fail(path, f"steps[{index}] must be a mapping")

    if "uses" not in step and "run" not in step:
        _fail(path, f"steps[{index}] must define either 'uses' or 'run'")


def _validate_job(path: Path, name: str, job: Any) -> None:
    if not isinstance(job, dict):
        _fail(path, f"job {name!r} must be a mapping")

    if "uses" in job:
        return

    steps = job.get("steps")
    if not isinstance(steps, list) or not steps:
        _fail(path, f"job {name!r} must contain a non-empty steps list")

    for index, step in enumerate(steps):
        _validate_step(path, index, step)


def validate_workflow(path: Path) -> None:
    try:
        # BaseLoader intentionally keeps YAML scalars as strings, including
        # GitHub's top-level `on` key.
        payload = yaml.load(
            path.read_text(encoding="utf-8"),
            Loader=yaml.BaseLoader,
        )
    except yaml.YAMLError as exc:
        _fail(path, f"invalid YAML: {exc}")

    if not isinstance(payload, dict):
        _fail(path, "workflow root must be a mapping")

    for required in ("name", "on", "jobs"):
        if required not in payload:
            _fail(path, f"missing top-level key {required!r}")

    jobs = payload["jobs"]
    if not isinstance(jobs, dict) or not jobs:
        _fail(path, "'jobs' must be a non-empty mapping")

    for name, job in jobs.items():
        _validate_job(path, str(name), job)


def main() -> int:
    paths = sorted(set(WORKFLOW_DIR.glob("*.yml")) | set(WORKFLOW_DIR.glob("*.yaml")))

    if not paths:
        raise RuntimeError("No GitHub Actions workflows found")

    for path in paths:
        validate_workflow(path)
        print(f"WORKFLOW VALID: {path.relative_to(ROOT)}")

    print(f"Validated {len(paths)} GitHub Actions workflows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
