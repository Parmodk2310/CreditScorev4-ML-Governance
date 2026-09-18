#!/usr/bin/env python3
"""Generate the deterministic, contract-valid Vendor C Phase 3 batch."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from creditscore.incidents.vendor_c_drift import VendorCDriftConfig, VendorCDriftScenario
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def build_scenario(config: dict) -> VendorCDriftScenario:
    vendor = config["vendor_c"]
    return VendorCDriftScenario(
        VendorCDriftConfig(
            random_seed=int(config["project"]["random_seed"]),
            device_center=float(vendor["device_risk"]["center"]),
            device_scale=float(vendor["device_risk"]["scale"]),
            device_shift=float(vendor["device_risk"]["shift"]),
            device_noise_std=float(vendor["device_risk"]["noise_std"]),
            utilization_shift=float(vendor["credit_utilization"]["shift"]),
            utilization_noise_std=float(vendor["credit_utilization"]["noise_std"]),
            dti_shift=float(vendor["debt_to_income"]["shift"]),
            dti_noise_std=float(vendor["debt_to_income"]["noise_std"]),
            bank_risk_shift=float(vendor["bank_transaction_risk"]["shift"]),
            bank_risk_noise_std=float(vendor["bank_transaction_risk"]["noise_std"]),
        )
    )


def generate_vendor_c(config: dict) -> tuple[pd.DataFrame, pd.DataFrame, Path]:
    reference_path = ROOT / config["scenario"]["input"]
    output_path = ROOT / config["scenario"]["output"]
    if not reference_path.exists():
        raise FileNotFoundError(f"Phase 1 reference batch is missing: {reference_path}")
    reference = pd.read_csv(reference_path)
    current = build_scenario(config).apply(reference)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    current.to_csv(output_path, index=False)
    return reference, current, output_path


def main() -> None:
    config = load_yaml(ROOT / "configs" / "phase3.yaml")
    reference, current, output_path = generate_vendor_c(config)
    print(f"Saved Vendor C: {output_path}")
    print(f"Rows: {len(current):,}")
    print(f"Schema preserved: {list(reference.columns) == list(current.columns)}")
    print(f"Reference device NULL rate: {reference['device_risk_score'].isna().mean():.3%}")
    print(f"Vendor C device NULL rate: {current['device_risk_score'].isna().mean():.3%}")


if __name__ == "__main__":
    main()
