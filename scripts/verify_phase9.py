#!/usr/bin/env python3
"""Verify Phase 9 business-impact evidence and its acceptance contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return payload


def _in_range(value: float, contract: dict[str, Any]) -> bool:
    return float(contract["minimum"]) <= value <= float(contract["maximum"])


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase9.yaml")
    acceptance = config["acceptance"]
    report_path = ROOT / str(config["evidence"]["report"])

    if not report_path.exists():
        print(f"Missing Phase 9 report: " f"{report_path.relative_to(ROOT)}")
        return 1

    report = _read_json(report_path)
    healthy = report["healthy"]
    incident = report["incident"]
    comparison = report["comparison"]
    traceability = report["traceability"]

    healthy_approval = float(healthy["approval_rate"])
    incident_approval = float(incident["approval_rate"])
    healthy_approved_default = float(healthy["approved_default_rate"])
    incident_approved_default = float(incident["approved_default_rate"])

    gates = {
        "same_population": bool(comparison["same_population"]) is bool(acceptance["require_same_population"]),
        "same_labels": bool(comparison["same_labels"]) is bool(acceptance["require_same_labels"]),
        "healthy_approval_rate": _in_range(
            healthy_approval,
            acceptance["healthy_approval_rate"],
        ),
        "incident_approval_rate": _in_range(
            incident_approval,
            acceptance["incident_approval_rate"],
        ),
        "approval_rate_increase": float(comparison["approval_rate_change"])
        >= float(acceptance["minimum_approval_rate_increase"]),
        "healthy_approved_default_rate": _in_range(
            healthy_approved_default,
            acceptance["healthy_approved_default_rate"],
        ),
        "incident_approved_default_rate": _in_range(
            incident_approved_default,
            acceptance["incident_approved_default_rate"],
        ),
        "approved_default_rate_increase": float(comparison["approved_default_rate_change"])
        >= float(acceptance["minimum_approved_default_rate_increase"]),
        "predicted_risk_underestimation": float(comparison["mean_predicted_risk_change"])
        <= float(acceptance["maximum_mean_predicted_risk_change"]),
        "device_missingness_increase": float(comparison["device_null_rate_change"])
        >= float(acceptance["minimum_device_null_rate_increase"]),
        "overall_default_rate_preserved": abs(float(comparison["overall_default_rate_change"]))
        <= float(acceptance["maximum_overall_default_rate_delta"]),
        "traceability_hashes_present": all(
            isinstance(value, str) and len(value) == 64 for value in traceability.values()
        ),
    }

    print("CreditScoreV4 — Phase 9 Verification")
    print("=" * 40)
    print(f"  healthy approval rate.............. " f"{healthy_approval:.2%}")
    print(f"  incident approval rate............. " f"{incident_approval:.2%}")
    print("  approval-rate change............... " f"{float(comparison['approval_rate_change']):+.2%}")
    print("  healthy approved default rate...... " f"{healthy_approved_default:.2%}")
    print("  incident approved default rate..... " f"{incident_approved_default:.2%}")
    print(
        "  approved-default change............ " f"{float(comparison['approved_default_rate_change']):+.2%}"
    )
    print("  mean predicted-risk change......... " f"{float(comparison['mean_predicted_risk_change']):+.4f}")
    print("  device NULL-rate change............ " f"{float(comparison['device_null_rate_change']):+.2%}")
    print(f"  newly approved applicants.......... " f"{comparison['newly_approved_count']}")
    print(f"  newly rejected applicants.......... " f"{comparison['newly_rejected_count']}")
    print(f"  decision flips..................... " f"{comparison['decision_flip_count']}")

    print("\nAcceptance gates")
    for name, passed in gates.items():
        print(f"  {name:<38} " f"{'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 9: VERIFIED")
        return 0

    print("\nPHASE 9: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
