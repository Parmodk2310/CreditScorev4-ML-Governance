from __future__ import annotations

import numpy as np
import pandas as pd

from creditscore.fairness.expanded import (
    ExpandedFairnessEvaluator,
    add_intersection_column,
)
from creditscore.incidents.vendor_e_intersectional_proxy_stress import (
    VendorEIntersectionalProxyStressScenario,
    VendorEStressConfig,
)


def test_vendor_e_preserves_protected_values_and_creates_intersectional_stress() -> None:
    rows = 24
    frame = pd.DataFrame(
        {
            "sex": ["female"] * 12 + ["male"] * 12,
            "synthetic_demographic_group": (["group_c"] * 6 + ["group_a"] * 6) * 2,
            "device_risk_score": np.linspace(0.2, 0.5, rows),
            "credit_utilization": np.linspace(0.2, 0.5, rows),
            "bank_transaction_risk": np.linspace(0.1, 0.4, rows),
            "default_30d": [0, 1] * 12,
        }
    )
    scenario = VendorEIntersectionalProxyStressScenario(
        VendorEStressConfig(
            sex_value="female",
            demographic_group_value="group_c",
            device_risk_score_shift=0.2,
            credit_utilization_shift=0.1,
            bank_transaction_risk_shift=0.1,
        )
    )
    current = scenario.apply(frame)

    assert frame["sex"].equals(current["sex"])
    assert frame["synthetic_demographic_group"].equals(
        current["synthetic_demographic_group"]
    )
    assert frame["default_30d"].equals(current["default_30d"])

    reference_augmented = add_intersection_column(
        frame,
        components=["sex", "synthetic_demographic_group"],
        output_column="intersection",
        separator="|",
    )
    current_augmented = add_intersection_column(
        current,
        components=["sex", "synthetic_demographic_group"],
        output_column="intersection",
        separator="|",
    )
    assert reference_augmented["intersection"].equals(
        current_augmented["intersection"]
    )


def test_expanded_fairness_uses_favorable_approval_semantics() -> None:
    frame = pd.DataFrame(
        {
            "sex": ["female"] * 4 + ["male"] * 4,
            "synthetic_demographic_group": ["group_c"] * 2 + ["group_a"] * 2
            + ["group_c"] * 2 + ["group_a"] * 2,
            "intersection": [
                "female|group_c",
                "female|group_c",
                "female|group_a",
                "female|group_a",
                "male|group_c",
                "male|group_c",
                "male|group_a",
                "male|group_a",
            ],
            "default_30d": [0, 1, 0, 1, 0, 1, 0, 1],
        }
    )
    probabilities = np.array([0.8, 0.9, 0.1, 0.8, 0.1, 0.8, 0.1, 0.8])
    config = {
        "scenario": {"name": "integration"},
        "intersection": {
            "derived_feature": "intersection",
            "minimum_group_size": 2,
        },
        "fairness": {
            "monitored_sensitive_features": ["intersection"],
            "governance_sensitive_features": ["intersection"],
            "thresholds": {
                "demographic_parity_ratio": {
                    "warning_below": 0.90,
                    "fail_below": 0.80,
                },
                "selection_rate_difference": {
                    "warning_at_or_above": 0.10,
                    "fail_at_or_above": 0.15,
                },
                "equal_opportunity_difference": {
                    "warning_at_or_above": 0.10,
                    "fail_at_or_above": 0.15,
                },
                "equalized_odds_difference": {
                    "warning_at_or_above": 0.10,
                    "fail_at_or_above": 0.20,
                },
                "false_approval_rate_difference": {
                    "warning_at_or_above": 0.10,
                    "fail_at_or_above": 0.15,
                },
            },
        },
    }

    report = ExpandedFairnessEvaluator(config).evaluate(
        frame,
        frame,
        reference_probabilities=probabilities,
        current_probabilities=probabilities,
        default_threshold=0.5,
    )

    target = next(
        group
        for group in report.current_primary.group_metrics
        if group.group == "female|group_c"
    )
    assert target.approval_rate == 0.0
    assert target.favorable_true_positive_rate == 0.0
