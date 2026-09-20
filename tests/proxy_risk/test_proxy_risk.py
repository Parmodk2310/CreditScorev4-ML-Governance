from __future__ import annotations

import pandas as pd

from creditscore.fairness.proxy_risk import (
    ProxyRiskAnalyzer,
    cramers_v,
    eta_squared,
)


def test_eta_squared_detects_numeric_group_association() -> None:
    groups = pd.Series(["a", "a", "a", "b", "b", "b"])
    values = pd.Series([0.0, 0.1, 0.2, 0.8, 0.9, 1.0])

    assert eta_squared(values, groups) > 0.80


def test_cramers_v_detects_categorical_group_association() -> None:
    groups = pd.Series(["a", "a", "a", "b", "b", "b"])
    values = pd.Series(["x", "x", "x", "y", "y", "y"])

    assert cramers_v(values, groups) > 0.90


def test_proxy_analyzer_requires_association_plus_model_influence() -> None:
    reference = pd.DataFrame(
        {
            "intersection": ["a"] * 4 + ["b"] * 4,
            "risk_feature": [0.4, 0.5, 0.4, 0.5, 0.4, 0.5, 0.4, 0.5],
            "control_feature": [0.1, 0.2, 0.3, 0.4, 0.1, 0.2, 0.3, 0.4],
            "category": ["x", "y"] * 4,
        }
    )
    current = reference.copy()
    current.loc[current["intersection"].eq("b"), "risk_feature"] += 0.4

    config = {
        "proxy_risk": {
            "sensitive_feature": "intersection",
            "minimum_group_size": 2,
            "numeric_features": ["risk_feature", "control_feature"],
            "categorical_features": ["category"],
            "minimum_association_delta": 0.01,
            "top_association_k": 2,
            "top_model_influence_k": 1,
        }
    }
    shap = pd.DataFrame(
        {
            "feature": ["risk_feature", "control_feature", "category_x", "category_y"],
            "mean_abs_shap": [0.9, 0.2, 0.05, 0.05],
        }
    )

    report = ProxyRiskAnalyzer(config).analyze(
        reference,
        current,
        shap_global=shap,
        primary_group="b",
    )

    assert "risk_feature" in report.top_association_features
    assert "risk_feature" in report.review_priority_features
    assert "control_feature" not in report.review_priority_features
