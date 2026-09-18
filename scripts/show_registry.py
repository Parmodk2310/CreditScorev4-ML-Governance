#!/usr/bin/env python3
"""Display the local Phase 5 model registry."""

from __future__ import annotations

from pathlib import Path

from creditscore.governance.workflow import GovernanceWorkflow

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    workflow = GovernanceWorkflow(ROOT)
    records = workflow.registry.list_versions()
    print("CreditScoreV4 — Phase 5 Registry")
    print("=" * 34)
    if not records:
        print("Registry is empty.")
        return
    print(f"{'Version':24} {'Stage':12} {'Decision':20}")
    print("-" * 60)
    for record in records:
        print(f"{record.version:24} {record.stage:12} {record.last_decision_id or '-':20}")


if __name__ == "__main__":
    main()
