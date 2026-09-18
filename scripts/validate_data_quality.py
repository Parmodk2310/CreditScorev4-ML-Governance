"""Run the Phase 2 data-quality gate against a CSV batch."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from creditscore.utils.config import load_yaml
from creditscore.validation import DataQualityGate, load_data_contract

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="CSV batch to validate")
    parser.add_argument("--source", required=True, help="Logical upstream source name")
    parser.add_argument("--batch-name", required=True, help="Evidence/quarantine batch name")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml(ROOT / "configs" / "phase2.yaml")
    contract = load_data_contract(ROOT / config["contract"]["path"])
    gate = DataQualityGate(
        contract,
        evidence_dir=ROOT / config["gate"]["evidence_dir"],
        quarantine_dir=ROOT / config["gate"]["quarantine_dir"],
    )
    frame = pd.read_csv(ROOT / args.input)
    decision = gate.evaluate(frame, batch_name=args.batch_name, source=args.source)

    print(f"Batch: {decision.batch_name}")
    print(f"Source: {decision.source}")
    print(f"Decision: {decision.decision}")
    print(f"Contract: {'PASS' if decision.contract_passed else 'FAIL'}")
    print(f"Great Expectations: {'PASS' if decision.gx_passed else 'FAIL'}")
    if decision.failed_rule_ids:
        print("Failed rules:")
        for rule_id in decision.failed_rule_ids:
            print(f"  - {rule_id}")
    print(f"Evidence: {decision.evidence_path}")
    if decision.quarantine_path:
        print(f"Quarantine: {decision.quarantine_path}")
    return 0 if decision.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
