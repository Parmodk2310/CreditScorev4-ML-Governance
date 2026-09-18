#!/usr/bin/env python3
"""Evaluate one Phase 5 candidate without changing its final registry stage."""

from __future__ import annotations

import argparse
from pathlib import Path

from creditscore.governance.workflow import GovernanceWorkflow

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["healthy", "vendor_c", "vendor_d"], required=True)
    args = parser.parse_args()

    workflow = GovernanceWorkflow(ROOT)
    decision = workflow.evaluate_only(args.scenario)

    print("CreditScoreV4 — Phase 5 Governance Evaluation")
    print("=" * 47)
    print(f"Scenario...................... {decision.scenario}")
    print(f"Model version................. {decision.model_version}")
    print(f"Decision...................... {decision.decision}")
    print(f"Requested stage............... {decision.requested_stage}")
    print()
    print("Gates")
    for gate in decision.gates:
        print(f"  {gate.name:22} {gate.status:4}  {gate.reason}")
    if decision.blocking_reasons:
        print("\nBlocking reasons")
        for reason in decision.blocking_reasons:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
