#!/usr/bin/env python3
"""Evaluate a Phase 5 candidate and apply the allowed registry transition."""

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
    decision, stage, _ = workflow.evaluate_and_apply(args.scenario)

    print("CreditScoreV4 — Phase 5 Promotion Decision")
    print("=" * 43)
    print(f"Scenario...................... {args.scenario}")
    print(f"Decision...................... {decision.decision}")
    print(f"Registry stage................ {stage}")
    print(f"Decision ID................... {decision.decision_id}")
    if decision.blocking_reasons:
        print("Blocking reasons:")
        for reason in decision.blocking_reasons:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
