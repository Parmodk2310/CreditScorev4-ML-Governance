#!/usr/bin/env python3
"""Generate deterministic Vendor D subgroup proxy stress for Phase 4."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from creditscore.incidents.vendor_d_group_stress import VendorDGroupStressScenario, VendorDStressConfig
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def build_scenario(config: dict) -> VendorDGroupStressScenario:
    vendor = config["vendor_d"]
    return VendorDGroupStressScenario(
        VendorDStressConfig(
            sensitive_feature=str(vendor["sensitive_feature"]),
            stressed_group=str(vendor["stressed_group"]),
            device_risk_score_shift=float(vendor["device_risk_score_shift"]),
            credit_utilization_shift=float(vendor["credit_utilization_shift"]),
            bank_transaction_risk_shift=float(vendor["bank_transaction_risk_shift"]),
        )
    )


def generate_vendor_d(config: dict) -> tuple[pd.DataFrame, pd.DataFrame, Path]:
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
    config = load_yaml(ROOT / "configs" / "phase4.yaml")
    reference, current, output_path = generate_vendor_d(config)
    sensitive = str(config["vendor_d"]["sensitive_feature"])
    stressed_group = str(config["vendor_d"]["stressed_group"])
    stressed_count = int(current[sensitive].astype(str).eq(stressed_group).sum())

    print(f"Saved Vendor D: {output_path}")
    print(f"Rows: {len(current):,}")
    print(f"Schema preserved: {list(reference.columns) == list(current.columns)}")
    print(f"Stressed group: {stressed_group} ({stressed_count:,} rows)")
    print(f"Reference device NULL rate: {reference['device_risk_score'].isna().mean():.3%}")
    print(f"Vendor D device NULL rate: {current['device_risk_score'].isna().mean():.3%}")


if __name__ == "__main__":
    main()
