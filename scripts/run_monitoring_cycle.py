#!/usr/bin/env python3
"""Execute one Phase 11 scheduled governance-monitoring cycle."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from creditscore.orchestration import MonitoringOrchestrator
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _default_run_id() -> str:
    return "local-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    config = load_yaml(ROOT / "configs" / "phase11.yaml")
    orchestrator = MonitoringOrchestrator(root=ROOT, config=config)
    run = orchestrator.run(
        run_id=str(args.run_id or _default_run_id()),
        source_commit=_git_commit(),
    )

    manifest_path = ROOT / str(config["evidence"]["manifest"])
    events_path = ROOT / str(config["evidence"]["events"])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_path.write_text(
        json.dumps(run.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with events_path.open("w", encoding="utf-8") as handle:
        for result in run.tasks:
            handle.write(json.dumps(result.to_dict(), sort_keys=True) + "\n")

    print("CreditScoreV4 — Phase 11 Monitoring Cycle")
    print("=" * 43)
    print(f"Run id.............................. {run.run_id}")
    print(f"Source commit....................... {run.source_commit}")
    print(f"Fail closed......................... {str(run.fail_closed).lower()}")
    print(f"Automatic retraining................. {str(run.automatic_retraining).lower()}")
    print(f"Automatic promotion.................. {str(run.automatic_promotion).lower()}")
    print()
    for result in run.tasks:
        print(f"  {result.task_id:<28} {result.status:<7} " f"attempts={result.attempts}")
        if result.status != "PASS":
            print(f"    reason: {result.reason}")

    print(f"\nManifest............................ {manifest_path.relative_to(ROOT)}")
    print(f"Events.............................. {events_path.relative_to(ROOT)}")
    print(f"Final status........................ {run.final_status}")

    return 0 if run.final_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
