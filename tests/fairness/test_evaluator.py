from __future__ import annotations

import numpy as np
import pandas as pd

from creditscore.fairness import FairnessEvaluator


def _config() -> dict:
    return {
        "scenario": {"name": "test"},
        "fairness": {
            "primary_sensitive_feature": "synthetic_demographic_group",
            "monitored_sensitive_features": ["synthetic_demographic_group"],
            "governance_sensitive_features": ["synthetic_demographic_group"],
            "thresholds": {
                "demographic_parity_ratio": {"warning_below": 0.90, "fail_below": 0.80},
                "selection_rate_difference": {
                    "warning_at_or_above": 0.10,
                    "fail_at_or_above": 0.15,
                },
                "equalized_odds_difference": {
                    "warning_at_or_above": 0.10,
                    "fail_at_or_above": 0.20,
                },
            },
        },
    }


def test_evaluator_flags_large_selection_disparity() -> None:
    frame = pd.DataFrame(
        {
            "synthetic_demographic_group": ["group_a"] * 6 + ["group_c"] * 6,
            "default_30d": [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1],
        }
    )
    reference_probabilities = np.array([0.1, 0.2, 0.8, 0.3, 0.7, 0.2] * 2)
    current_probabilities = np.array([0.1, 0.2, 0.8, 0.3, 0.7, 0.2, 0.7, 0.8, 0.6, 0.9, 0.7, 0.8])

    report = FairnessEvaluator(_config()).evaluate(
        frame,
        frame,
        reference_probabilities=reference_probabilities,
        current_probabilities=current_probabilities,
        default_threshold=0.5,
    )

    assert report.overall_status == "FAIL"
    assert report.current_primary.demographic_parity_ratio < 0.80
