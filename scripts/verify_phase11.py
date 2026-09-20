#!/usr/bin/env python3
"""Verify the Phase 11 scheduled monitoring/orchestration contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return payload


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase11.yaml")
    acceptance = config["acceptance"]
    manifest_path = ROOT / str(config["evidence"]["manifest"])
    events_path = ROOT / str(config["evidence"]["events"])
    workflow_path = ROOT / str(config["scheduler"]["workflow"])

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Phase 11 manifest missing: {manifest_path.relative_to(ROOT)}. "
            "Run make phase11-run first."
        )

    manifest = _read_json(manifest_path)
    tasks = list(manifest["tasks"])
    expected_ids = [
        str(payload["id"]) for payload in config["orchestration"]["tasks"]
    ]
    actual_ids = [str(task["task_id"]) for task in tasks]

    all_hashes_valid = True
    for task in tasks:
        configured = next(
            payload
            for payload in config["orchestration"]["tasks"]
            if str(payload["id"]) == str(task["task_id"])
        )
        expected_paths = {str(path) for path in configured.get("evidence", [])}
        actual_hashes = {
            str(path): str(value)
            for path, value in task.get("evidence_sha256", {}).items()
        }
        if set(actual_hashes) != expected_paths:
            all_hashes_valid = False
            break
        if not all(SHA256_PATTERN.fullmatch(value) for value in actual_hashes.values()):
            all_hashes_valid = False
            break

    workflow_text = workflow_path.read_text(encoding="utf-8")
    cron = str(config["scheduler"]["cron_utc"])

    gates = {
        "final_status_pass": (
            str(manifest["final_status"])
            == str(acceptance["require_final_status"])
        ),
        "task_order_matches_config": actual_ids == expected_ids,
        "all_tasks_pass": (
            all(str(task["status"]) == "PASS" for task in tasks)
            is bool(acceptance["require_all_tasks_pass"])
        ),
        "no_skipped_tasks": (
            not any(str(task["status"]) == "SKIPPED" for task in tasks)
            is bool(acceptance["require_no_skipped_tasks"])
        ),
        "evidence_hashes_complete": (
            all_hashes_valid is bool(acceptance["require_evidence_hashes"])
        ),
        "fail_closed": (
            bool(manifest["fail_closed"])
            is bool(acceptance["require_fail_closed"])
        ),
        "automatic_retraining_disabled": (
            bool(manifest["automatic_retraining"]) is False
            and bool(acceptance["require_automatic_retraining_disabled"])
        ),
        "automatic_promotion_disabled": (
            bool(manifest["automatic_promotion"]) is False
            and bool(acceptance["require_automatic_promotion_disabled"])
        ),
        "events_written": events_path.exists() and events_path.stat().st_size > 0,
        "scheduled_workflow_present": (
            workflow_path.exists()
            and cron in workflow_text
            and "make phase11-run" in workflow_text
            and bool(acceptance["require_scheduled_workflow"])
        ),
        "scheduled_workflow_read_only": "contents: read" in workflow_text,
        "scheduled_workflow_uploads_evidence": (
            "phase11-monitoring-evidence" in workflow_text
            and "data/evidence/phase11" in workflow_text
        ),
    }

    print("CreditScoreV4 — Phase 11 Verification")
    print("=" * 41)
    print(f"  manifest run id.................. {manifest['run_id']}")
    print(f"  task count....................... {len(tasks)}")
    print(f"  final status..................... {manifest['final_status']}")
    print()
    print("Acceptance gates")
    for name, passed in gates.items():
        print(f"  {name:<42} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 11 CORE: VERIFIED")
        print(
            "Scheduled monitoring is fail-closed; automatic retraining and "
            "automatic promotion remain disabled."
        )
        return 0

    print("\nPHASE 11 CORE: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
