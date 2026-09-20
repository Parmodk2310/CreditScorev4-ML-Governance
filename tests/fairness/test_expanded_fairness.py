from __future__ import annotations

import numpy as np
import pandas as pd

from creditscore.fairness.expanded import (
    ExpandedFairnessEvaluator,
    add_intersection_column,
)


def _config() -> dict:
    return {
        "scenario": {"name": "test"},
        "intersection": {
            "derived_feature": "intersection",
            "minimum_group_size": 2,
        },
        "fairness": {
            "monitored_sensitive_features": ["sex", "group", "intersection"],
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


def test_add_intersection_column_preserves_source_values() -> None:
    frame = pd.DataFrame(
        {
            "sex": ["female", "male"],
            "group": ["a", "b"],
            "default_30d": [0, 1],
        }
    )

    result = add_intersection_column(
        frame,
        components=["sex", "group"],
        output_column="intersection",
        separator="|",
    )

    assert result["intersection"].tolist() == ["female|a", "male|b"]
    assert result["sex"].equals(frame["sex"])
    assert result["group"].equals(frame["group"])


def test_intersection_can_fail_when_single_axes_do_not() -> None:
    frame = pd.DataFrame(
        {
            "sex": ["female"] * 4 + ["male"] * 4,
            "group": ["a", "a", "b", "b"] * 2,
            "intersection": [
                "female|a",
                "female|a",
                "female|b",
                "female|b",
                "male|a",
                "male|a",
                "male|b",
                "male|b",
            ],
            "default_30d": [0, 1, 0, 1, 0, 1, 0, 1],
        }
    )
    reference = np.array([0.1, 0.8, 0.1, 0.8, 0.1, 0.8, 0.1, 0.8])
    current = np.array([0.1, 0.8, 0.9, 0.9, 0.1, 0.8, 0.1, 0.8])

    report = ExpandedFairnessEvaluator(_config()).evaluate(
        frame,
        frame,
        reference_probabilities=reference,
        current_probabilities=current,
        default_threshold=0.5,
    )

    assert report.overall_status == "FAIL"
    assert report.current_primary.status == "FAIL"
