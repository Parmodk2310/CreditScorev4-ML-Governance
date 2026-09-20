#!/usr/bin/env python3
"""Generate deterministic Vendor E intersectional proxy stress for Phase 12."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from creditscore.fairness import add_intersection_column
from creditscore.incidents.vendor_e_intersectional_proxy_stress import (
    VendorEIntersectionalProxyStressScenario,
    VendorEStressConfig,
)
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def build_scenario(config: dict) -> VendorEIntersectionalProxyStressScenario:
    stressed = config["intersection"]["stressed_values"]
    vendor = config["vendor_e"]
    return VendorEIntersectionalProxyStressScenario(
        VendorEStressConfig(
            sex_value=str(stressed["sex"]),
            demographic_group_value=str(stressed["synthetic_demographic_group"]),
            device_risk_score_shift=float(vendor["device_risk_score_shift"]),
            credit_utilization_shift=float(vendor["credit_utilization_shift"]),
            bank_transaction_risk_shift=float(vendor["bank_transaction_risk_shift"]),
        )
    )


def target_group_name(config: dict) -> str:
    components = [str(value) for value in config["intersection"]["components"]]
    separator = str(config["intersection"]["separator"])
    stressed = config["intersection"]["stressed_values"]
    return separator.join(str(stressed[column]) for column in components)


def generate_vendor_e(
    config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Path]:
    input_path = ROOT / str(config["scenario"]["input"])
    output_path = ROOT / str(config["scenario"]["output"])
    if not input_path.exists():
        raise FileNotFoundError(f"Phase 1 reference batch is missing: {input_path}")

    reference = pd.read_csv(input_path)
    scenario = build_scenario(config)
    current = scenario.apply(reference)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    current.to_csv(output_path, index=False)

    intersection = config["intersection"]
    components = [str(value) for value in intersection["components"]]
    derived = str(intersection["derived_feature"])
    separator = str(intersection["separator"])
    reference_augmented = add_intersection_column(
        reference,
        components=components,
        output_column=derived,
        separator=separator,
    )
    current_augmented = add_intersection_column(
        current,
        components=components,
        output_column=derived,
        separator=separator,
    )
    return reference, current, reference_augmented, current_augmented, output_path


def main() -> None:
    config = load_yaml(ROOT / "configs" / "phase12.yaml")
    _, _, reference, current, output_path = generate_vendor_e(config)
    derived = str(config["intersection"]["derived_feature"])
    target = target_group_name(config)
    count = int(current[derived].astype(str).eq(target).sum())

    print(f"Saved Vendor E: {output_path}")
    print(f"Rows: {len(current):,}")
    print(f"Target intersection: {target} ({count:,} rows)")
    print(
        "Protected intersection preserved: "
        f"{reference[derived].equals(current[derived])}"
    )


if __name__ == "__main__":
    main()
