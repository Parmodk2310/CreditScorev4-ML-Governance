"""Fairlearn-backed subgroup assessment for Phase 4."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fairlearn.metrics import (
    MetricFrame,
    demographic_parity_difference,
    demographic_parity_ratio,
    equalized_odds_difference,
    false_negative_rate,
    false_positive_rate,
    true_positive_rate,
)
from sklearn.metrics import accuracy_score

from .metrics import approval_rate
from .models import FairnessReport, GroupMetrics, SensitiveFeatureAssessment, maximum_status


class FairnessEvaluator:
    """Assess reference/current subgroup behavior without using groups as model inputs."""

    def __init__(self, config: dict[str, Any]):
        fairness = config["fairness"]
        self.primary_sensitive_feature = str(fairness["primary_sensitive_feature"])
        self.monitored_sensitive_features = [str(item) for item in fairness["monitored_sensitive_features"]]
        self.governance_sensitive_features = {str(item) for item in fairness["governance_sensitive_features"]}
        self.thresholds = fairness["thresholds"]
        self.scenario = str(config["scenario"]["name"])

    def _ratio_status(self, value: float) -> str:
        threshold = self.thresholds["demographic_parity_ratio"]
        if value < float(threshold["fail_below"]):
            return "FAIL"
        if value < float(threshold["warning_below"]):
            return "WARNING"
        return "PASS"

    def _difference_status(self, value: float, key: str) -> str:
        threshold = self.thresholds[key]
        if value >= float(threshold["fail_at_or_above"]):
            return "FAIL"
        if value >= float(threshold["warning_at_or_above"]):
            return "WARNING"
        return "PASS"

    def _evaluate_sensitive_feature(
        self,
        frame: pd.DataFrame,
        probabilities: np.ndarray,
        predicted_default: np.ndarray,
        sensitive_feature: str,
    ) -> SensitiveFeatureAssessment:
        if sensitive_feature not in frame.columns:
            raise ValueError(f"Missing sensitive feature: {sensitive_feature}")

        y_true = frame["default_30d"].astype(int).to_numpy()
        sensitive = frame[sensitive_feature].astype(str)
        approved = (predicted_default == 0).astype(int)

        metric_frame = MetricFrame(
            metrics={
                "approval_rate": approval_rate,
                "accuracy": accuracy_score,
                "true_positive_rate": true_positive_rate,
                "false_positive_rate": false_positive_rate,
                "false_negative_rate": false_negative_rate,
            },
            y_true=y_true,
            y_pred=predicted_default,
            sensitive_features=sensitive,
        )
        by_group = metric_frame.by_group
        if not isinstance(by_group, pd.DataFrame):
            raise TypeError("Expected MetricFrame.by_group to be a pandas DataFrame")

        group_metrics: list[GroupMetrics] = []
        for group_name, row in by_group.sort_index().iterrows():
            mask = sensitive.eq(str(group_name)).to_numpy()
            group_metrics.append(
                GroupMetrics(
                    sensitive_feature=sensitive_feature,
                    group=str(group_name),
                    sample_count=int(mask.sum()),
                    approval_rate=float(row["approval_rate"]),
                    predicted_default_rate=float(predicted_default[mask].mean()),
                    actual_default_rate=float(y_true[mask].mean()),
                    mean_predicted_risk=float(probabilities[mask].mean()),
                    accuracy=float(row["accuracy"]),
                    true_positive_rate=float(row["true_positive_rate"]),
                    false_positive_rate=float(row["false_positive_rate"]),
                    false_negative_rate=float(row["false_negative_rate"]),
                )
            )

        dp_ratio = float(demographic_parity_ratio(y_true, approved, sensitive_features=sensitive))
        dp_difference = float(demographic_parity_difference(y_true, approved, sensitive_features=sensitive))
        eo_difference = float(
            equalized_odds_difference(y_true, predicted_default, sensitive_features=sensitive)
        )
        status = maximum_status(
            self._ratio_status(dp_ratio),
            self._difference_status(dp_difference, "selection_rate_difference"),
            self._difference_status(eo_difference, "equalized_odds_difference"),
        )
        return SensitiveFeatureAssessment(
            sensitive_feature=sensitive_feature,
            status=status,
            demographic_parity_ratio=dp_ratio,
            demographic_parity_difference=dp_difference,
            equalized_odds_difference=eo_difference,
            group_metrics=group_metrics,
        )

    def _snapshot(
        self,
        frame: pd.DataFrame,
        probabilities: np.ndarray,
        threshold: float,
    ) -> list[SensitiveFeatureAssessment]:
        predicted_default = (probabilities >= threshold).astype(int)
        return [
            self._evaluate_sensitive_feature(
                frame,
                probabilities,
                predicted_default,
                sensitive_feature,
            )
            for sensitive_feature in self.monitored_sensitive_features
        ]

    def evaluate(
        self,
        reference: pd.DataFrame,
        current: pd.DataFrame,
        *,
        reference_probabilities: np.ndarray,
        current_probabilities: np.ndarray,
        default_threshold: float,
    ) -> FairnessReport:
        reference_results = self._snapshot(reference, reference_probabilities, default_threshold)
        current_results = self._snapshot(current, current_probabilities, default_threshold)

        governed = [
            item.status
            for item in current_results
            if item.sensitive_feature in self.governance_sensitive_features
        ]
        overall_status = maximum_status(*governed)
        reference_primary = next(
            item for item in reference_results if item.sensitive_feature == self.primary_sensitive_feature
        )
        current_primary = next(
            item for item in current_results if item.sensitive_feature == self.primary_sensitive_feature
        )
        primary_delta = {
            "demographic_parity_ratio": current_primary.demographic_parity_ratio
            - reference_primary.demographic_parity_ratio,
            "demographic_parity_difference": current_primary.demographic_parity_difference
            - reference_primary.demographic_parity_difference,
            "equalized_odds_difference": current_primary.equalized_odds_difference
            - reference_primary.equalized_odds_difference,
        }
        return FairnessReport(
            scenario=self.scenario,
            primary_sensitive_feature=self.primary_sensitive_feature,
            overall_status=overall_status,
            reference=reference_results,
            current=current_results,
            primary_metric_delta=primary_delta,
            metadata={
                "governance_sensitive_features": sorted(self.governance_sensitive_features),
                "monitored_sensitive_features": self.monitored_sensitive_features,
                "thresholds": self.thresholds,
                "decision_semantics": {
                    "model_positive_class": "default_30d=1",
                    "favorable_lending_decision": "approved when risk_probability < threshold",
                },
            },
        )
