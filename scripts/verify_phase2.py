"""Verify the Phase 2 gate against the exact deterministic Phase 1 incident."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from creditscore.utils.config import load_yaml
from creditscore.utils.hashing import file_sha256
from creditscore.validation import DataQualityGate, load_data_contract

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase2.yaml")
    phase1 = load_yaml(ROOT / "configs" / "phase1.yaml")
    contract = load_data_contract(ROOT / config["contract"]["path"])
    gate = DataQualityGate(
        contract,
        evidence_dir=ROOT / config["gate"]["evidence_dir"],
        quarantine_dir=ROOT / config["gate"]["quarantine_dir"],
    )

    healthy_path = ROOT / "data" / "raw" / "vendor_a" / "holdout.csv"
    incident_path = ROOT / "data" / "raw" / "vendor_b" / "holdout.csv"
    if not healthy_path.exists() or not incident_path.exists():
        raise FileNotFoundError(
            "Phase 1 fixtures are missing. Run `make phase1-verify` first so Vendor A and Vendor B are regenerated."
        )

    healthy = pd.read_csv(healthy_path)
    incident = pd.read_csv(incident_path)
    healthy_decision = gate.evaluate(healthy, batch_name="vendor_a_healthy", source="vendor_a")
    incident_decision = gate.evaluate(incident, batch_name="vendor_b_incident", source="vendor_b")

    healthy_null = float(healthy["device_risk_score"].isna().mean())
    incident_null = float(incident["device_risk_score"].isna().mean())
    required_rule = str(config["acceptance"]["required_failed_rule"])
    phase1_comparison = json.loads(
        (ROOT / "data" / "evidence" / "phase1" / "performance_comparison.json").read_text(encoding="utf-8")
    )

    gates = {
        "healthy_vendor_passes": healthy_decision.passed,
        "incident_vendor_blocked": not incident_decision.passed,
        "incident_contract_failed": not incident_decision.contract_passed,
        "incident_gx_failed": not incident_decision.gx_passed,
        "required_null_rule_failed": required_rule in incident_decision.failed_rule_ids,
        "phase1_incident_null_rate_preserved": (
            float(config["acceptance"]["incident_device_null_rate_min"])
            <= incident_null
            <= float(config["acceptance"]["incident_device_null_rate_max"])
        ),
        "incident_is_materially_worse": incident_null > healthy_null + 0.10,
        "quarantine_written": bool(incident_decision.quarantine_path)
        and Path(incident_decision.quarantine_path).exists(),
        "exact_phase1_vendor_b_fixture": (
            file_sha256(incident_path) == phase1_comparison["vendor_b_file_sha256"]
        ),
    }

    summary = {
        "healthy": {
            "decision": healthy_decision.decision,
            "device_risk_null_rate": healthy_null,
            "fingerprint": healthy_decision.batch_fingerprint,
        },
        "incident": {
            "decision": incident_decision.decision,
            "device_risk_null_rate": incident_null,
            "fingerprint": incident_decision.batch_fingerprint,
            "failed_rule_ids": incident_decision.failed_rule_ids,
        },
        "phase1_expected_incident_null_rate": float(phase1["incident"]["target_device_null_rate"]),
        "acceptance_gates": gates,
    }
    summary_path = ROOT / config["gate"]["evidence_dir"] / "phase2_verification_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("CreditScoreV4 — Phase 2 Verification")
    print("=" * 41)
    print(f"Healthy Vendor A decision.......... {healthy_decision.decision}")
    print(f"Healthy device NULL rate.......... {healthy_null:.2%}")
    print(f"Incident Vendor B decision........ {incident_decision.decision}")
    print(f"Incident device NULL rate......... {incident_null:.2%}")
    print()
    print("Acceptance gates")
    for name, passed in gates.items():
        print(f"  {name:<35} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 2: VERIFIED")
        return 0
    print("\nPHASE 2: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
