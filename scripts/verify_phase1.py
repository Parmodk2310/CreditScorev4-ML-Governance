#!/usr/bin/env python3
"""Run Phase 1 end-to-end and enforce measurable acceptance gates."""
from __future__ import annotations

import json
import subprocess
import sys

from creditscore.utils.config import load_config, project_root


def run(script: str) -> None:
    subprocess.run([sys.executable, str(project_root() / "scripts" / script)], check=True)


def main() -> None:
    cfg = load_config()
    root = project_root()

    print("CreditScoreV4 — Phase 1 Verification")
    print("=" * 40)
    run("generate_dataset.py")
    run("train_baseline.py")
    run("simulate_incident.py")

    baseline = json.loads((root / "data/evidence/phase1/baseline_metrics.json").read_text(encoding="utf-8"))
    incident = json.loads((root / "data/evidence/phase1/incident_metrics.json").read_text(encoding="utf-8"))
    acceptance = cfg["acceptance"]
    auc_drop = baseline["roc_auc"] - incident["roc_auc"]

    checks = {
        "baseline_auc": acceptance["baseline_auc_min"] <= baseline["roc_auc"] <= acceptance["baseline_auc_max"],
        "incident_auc": acceptance["incident_auc_min"] <= incident["roc_auc"] <= acceptance["incident_auc_max"],
        "auc_drop": auc_drop >= acceptance["minimum_auc_drop"],
        "baseline_null_rate": acceptance["baseline_null_rate_min"] <= baseline["device_risk_null_rate"] <= acceptance["baseline_null_rate_max"],
        "incident_null_rate": acceptance["incident_null_rate_min"] <= incident["device_risk_null_rate"] <= acceptance["incident_null_rate_max"],
    }

    print("\nMeasured evidence")
    print(f"  Healthy ROC-AUC................ {baseline['roc_auc']:.4f}")
    print(f"  Incident ROC-AUC............... {incident['roc_auc']:.4f}")
    print(f"  AUC degradation................ {auc_drop:.4f}")
    print(f"  Healthy device NULL rate....... {baseline['device_risk_null_rate']:.2%}")
    print(f"  Incident device NULL rate...... {incident['device_risk_null_rate']:.2%}")
    print("\nAcceptance gates")
    for name, passed in checks.items():
        print(f"  {name:<30} {'PASS' if passed else 'FAIL'}")

    if not all(checks.values()):
        raise SystemExit("\nPHASE 1: NOT VERIFIED")
    print("\nPHASE 1: VERIFIED")


if __name__ == "__main__":
    main()
