from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from creditscore.business_impact import (
    compare_business_impact,
    evaluate_scenario,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "application_id": ["A", "B", "C", "D"],
            "default_30d": [0, 1, 1, 1],
            "device_risk_score": [0.1, 0.2, np.nan, 0.8],
        }
    )


def test_evaluate_scenario_calculates_approved_outcomes() -> None:
    metrics = evaluate_scenario(
        _frame(),
        np.array([0.20, 0.40, 0.60, 0.80]),
        scenario="healthy",
        threshold=0.50,
    )

    assert metrics.sample_count == 4
    assert metrics.approval_count == 2
    assert metrics.approval_rate == pytest.approx(0.50)
    assert metrics.approved_default_rate == pytest.approx(0.50)
    assert metrics.device_risk_null_rate == pytest.approx(0.25)


def test_compare_business_impact_tracks_decision_transitions() -> None:
    healthy = _frame()
    incident = healthy.copy()
    incident.loc[1, "device_risk_score"] = np.nan

    comparison = compare_business_impact(
        healthy,
        incident,
        np.array([0.20, 0.40, 0.60, 0.80]),
        np.array([0.10, 0.30, 0.40, 0.70]),
        threshold=0.50,
    )

    assert comparison.same_population is True
    assert comparison.same_labels is True
    assert comparison.newly_approved_count == 1
    assert comparison.newly_rejected_count == 0
    assert comparison.decision_flip_count == 1
    assert comparison.approval_rate_change == pytest.approx(0.25)
    assert comparison.approved_default_rate_change == pytest.approx(1 / 6)
    assert comparison.newly_approved_default_rate == pytest.approx(1.0)


def test_compare_business_impact_rejects_different_population() -> None:
    healthy = _frame()
    incident = healthy.copy()
    incident.loc[0, "application_id"] = "OTHER"

    with pytest.raises(ValueError, match="same ordered population"):
        compare_business_impact(
            healthy,
            incident,
            np.array([0.20, 0.40, 0.60, 0.80]),
            np.array([0.20, 0.40, 0.60, 0.80]),
        )


def test_compare_business_impact_rejects_changed_labels() -> None:
    healthy = _frame()
    incident = healthy.copy()
    incident.loc[0, "default_30d"] = 1

    with pytest.raises(ValueError, match="same outcome labels"):
        compare_business_impact(
            healthy,
            incident,
            np.array([0.20, 0.40, 0.60, 0.80]),
            np.array([0.20, 0.40, 0.60, 0.80]),
        )
