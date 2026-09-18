#!/usr/bin/env python3
"""Register one Phase 5 candidate in the local model registry."""

from __future__ import annotations

import argparse
from pathlib import Path

from creditscore.governance.workflow import GovernanceWorkflow

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["healthy", "vendor_c", "vendor_d"], default="healthy")
    args = parser.parse_args()

    workflow = GovernanceWorkflow(ROOT)
    record = workflow.prepare_candidate(args.scenario)
    print("CreditScoreV4 — Phase 5 Candidate Registration")
    print("=" * 49)
    print(f"Model......................... {record.model_name}")
    print(f"Version....................... {record.version}")
    print(f"Stage......................... {record.stage}")
    print(f"Artifact SHA-256.............. {record.artifact_sha256}")


if __name__ == "__main__":
    main()
