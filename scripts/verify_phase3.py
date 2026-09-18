#!/usr/bin/env python3
"""Phase 3 acceptance gate: contract-valid Vendor C must still trigger drift governance."""

from __future__ import annotations

from pathlib import Path

from check_drift import run_drift_check
from simulate_drift import generate_vendor_c

from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase3.yaml")
    reference, current, output_path = generate_vendor_c(config)
    quality, report = run_drift_check()

    device_reference_null = float(reference["device_risk_score"].isna().mean())
    device_current_null = float(current["device_risk_score"].isna().mean())
    monitored = {result.feature: result for result in report.feature_results}
    required_critical = list(config["monitoring"]["required_critical_features"])
    control_features = list(config["monitoring"]["control_features"])
    prediction = report.prediction_result

    evidence_json = ROOT / config["paths"]["evidence_json"]
    evidence_csv = ROOT / config["paths"]["evidence_csv"]
    reference_profile = ROOT / config["paths"]["reference_profile"]

    acceptance = config["acceptance"]
    gates = {
        "vendor_c_generated": output_path.exists(),
        "schema_preserved": list(reference.columns) == list(current.columns),
        "row_count_preserved": len(reference) == len(current),
        "vendor_c_phase2_passes": quality.passed,
        "vendor_c_not_quarantined": quality.quarantine_path is None,
        "device_null_within_contract": device_current_null
        <= float(acceptance["maximum_vendor_c_device_null_rate"]),
        "device_null_rate_preserved": abs(device_current_null - device_reference_null)
        <= float(acceptance["maximum_null_rate_delta_vs_reference"]),
        "overall_drift_is_critical": report.overall_status == str(acceptance["require_overall_status"]),
        "required_critical_features": all(
            feature in monitored and monitored[feature].status == "CRITICAL" for feature in required_critical
        ),
        "minimum_critical_features": len(report.critical_features)
        >= int(acceptance["minimum_critical_features"]),
        "control_features_remain_stable": all(
            feature in monitored and monitored[feature].status == "STABLE" for feature in control_features
        ),
        "prediction_drift_detected": prediction is not None and prediction.status in {"WARNING", "CRITICAL"},
        "evidence_written": evidence_json.exists() and evidence_csv.exists() and reference_profile.exists(),
    }

    print("CreditScoreV4 — Phase 3 Verification")
    print("=" * 41)
    print(f"Vendor C Phase 2 decision.......... {quality.decision}")
    print(f"Reference device NULL rate......... {device_reference_null:.2%}")
    print(f"Vendor C device NULL rate.......... {device_current_null:.2%}")
    print(f"Overall drift status............... {report.overall_status}")
    print(f"Critical features.................. {', '.join(report.critical_features)}")
    if prediction is not None:
        print(
            "Prediction drift................... "
            f"{prediction.status} (PSI={prediction.psi:.4f}, KS={prediction.ks_statistic:.4f})"
        )
    print()
    print("Acceptance gates")
    for name, passed in gates.items():
        print(f"  {name:35} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 3: VERIFIED")
        return 0
    print("\nPHASE 3: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
