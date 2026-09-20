"""Expanded subgroup fairness evidence for Phase 12."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SEVERITY_ORDER = {"PASS": 0, "WARNING": 1, "FAIL": 2}


def maximum_status(*statuses: str) -> str:
    if not statuses:
        return "PASS"
    return max(statuses, key=lambda status: SEVERITY_ORDER[status])


def add_intersection_column(
    frame: pd.DataFrame,
    *,
    components: list[str],
    output_column: str,
    separator: str,
) -> pd.DataFrame:
    missing = [column for column in components if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing intersection components: {missing}")

    result = frame.copy()
    combined = result[components[0]].astype(str)
    for column in components[1:]:
        combined = combined.str.cat(result[column].astype(str), sep=separator)
    result[output_column] = combined
    return result


@dataclass(frozen=True)
class ExpandedGroupMetrics:
    sensitive_feature: str
    group: str
    sample_count: int
    eligible_for_governance: bool
    approval_rate: float
    actual_default_rate: float
    mean_predicted_risk: float
    favorable_true_positive_rate: float
    false_approval_rate: float
    missed_opportunity_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExpandedSensitiveAssessment:
    sensitive_feature: str
    status: str
    demographic_parity_ratio: float
    selection_rate_difference: float
    equal_opportunity_difference: float
    equalized_odds_difference: float
    false_approval_rate_difference: float
    group_metrics: list[ExpandedGroupMetrics] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sensitive_feature": self.sensitive_feature,
            "status": self.status,
            "demographic_parity_ratio": self.demographic_parity_ratio,
            "selection_rate_difference": self.selection_rate_difference,
            "equal_opportunity_difference": self.equal_opportunity_difference,
            "equalized_odds_difference": self.equalized_odds_difference,
            "false_approval_rate_difference": self.false_approval_rate_difference,
            "group_metrics": [metric.to_dict() for metric in self.group_metrics],
        }


@dataclass
class ExpandedFairnessReport:
    scenario: str
    primary_sensitive_feature: str
    overall_status: str
    reference: list[ExpandedSensitiveAssessment]
    current: list[ExpandedSensitiveAssessment]
    metadata: dict[str, Any] = field(default_factory=dict)

    def assessment(self, dataset: str, sensitive_feature: str) -> ExpandedSensitiveAssessment:
        values = self.reference if dataset == "reference" else self.current
        return next(item for item in values if item.sensitive_feature == sensitive_feature)

    @property
    def current_primary(self) -> ExpandedSensitiveAssessment:
        return self.assessment("current", self.primary_sensitive_feature)

    @property
    def reference_primary(self) -> ExpandedSensitiveAssessment:
        return self.assessment("reference", self.primary_sensitive_feature)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "primary_sensitive_feature": self.primary_sensitive_feature,
            "overall_status": self.overall_status,
            "reference": [item.to_dict() for item in self.reference],
            "current": [item.to_dict() for item in self.current],
            "metadata": self.metadata,
        }


class ExpandedFairnessEvaluator:
    """Evaluate favorable-decision fairness, including intersectional groups."""

    def __init__(self, config: dict[str, Any]):
        fairness = config["fairness"]
        intersection = config["intersection"]
        self.scenario = str(config["scenario"]["name"])
        self.primary_sensitive_feature = str(intersection["derived_feature"])
        self.monitored_sensitive_features = [str(value) for value in fairness["monitored_sensitive_features"]]
        self.governance_sensitive_features = {
            str(value) for value in fairness["governance_sensitive_features"]
        }
        self.minimum_group_size = int(intersection["minimum_group_size"])
        self.thresholds = fairness["thresholds"]

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

    @staticmethod
    def _rate(values: np.ndarray, mask: np.ndarray) -> float:
        selected = values[mask]
        if selected.size == 0:
            return float("nan")
        return float(selected.mean())

    def _evaluate_feature(
        self,
        frame: pd.DataFrame,
        probabilities: np.ndarray,
        sensitive_feature: str,
        threshold: float,
    ) -> ExpandedSensitiveAssessment:
        if sensitive_feature not in frame.columns:
            raise ValueError(f"Missing sensitive feature: {sensitive_feature}")

        y_default = frame["default_30d"].astype(int).to_numpy()
        approved = (probabilities < threshold).astype(int)
        favorable_truth = (y_default == 0).astype(int)
        sensitive = frame[sensitive_feature].astype(str)

        rows: list[ExpandedGroupMetrics] = []
        for group in sorted(sensitive.unique()):
            mask = sensitive.eq(group).to_numpy()
            group_default = y_default[mask]
            group_approved = approved[mask]
            group_favorable = favorable_truth[mask]
            group_probabilities = probabilities[mask]

            rows.append(
                ExpandedGroupMetrics(
                    sensitive_feature=sensitive_feature,
                    group=str(group),
                    sample_count=int(mask.sum()),
                    eligible_for_governance=int(mask.sum()) >= self.minimum_group_size,
                    approval_rate=float(group_approved.mean()),
                    actual_default_rate=float(group_default.mean()),
                    mean_predicted_risk=float(group_probabilities.mean()),
                    favorable_true_positive_rate=self._rate(
                        group_approved,
                        group_favorable == 1,
                    ),
                    false_approval_rate=self._rate(
                        group_approved,
                        group_favorable == 0,
                    ),
                    missed_opportunity_rate=self._rate(
                        1 - group_approved,
                        group_favorable == 1,
                    ),
                )
            )

        eligible = [row for row in rows if row.eligible_for_governance]
        if len(eligible) < 2:
            raise ValueError(
                f"Fairness governance requires at least two supported groups for {sensitive_feature}"
            )

        approval_rates = np.asarray([row.approval_rate for row in eligible], dtype=float)
        opportunity_rates = np.asarray([row.favorable_true_positive_rate for row in eligible], dtype=float)
        false_approval_rates = np.asarray([row.false_approval_rate for row in eligible], dtype=float)

        demographic_parity_ratio = float(approval_rates.min() / approval_rates.max())
        selection_rate_difference = float(approval_rates.max() - approval_rates.min())
        equal_opportunity_difference = float(np.nanmax(opportunity_rates) - np.nanmin(opportunity_rates))
        false_approval_rate_difference = float(
            np.nanmax(false_approval_rates) - np.nanmin(false_approval_rates)
        )
        equalized_odds_difference = max(
            equal_opportunity_difference,
            false_approval_rate_difference,
        )

        status = maximum_status(
            self._ratio_status(demographic_parity_ratio),
            self._difference_status(
                selection_rate_difference,
                "selection_rate_difference",
            ),
            self._difference_status(
                equal_opportunity_difference,
                "equal_opportunity_difference",
            ),
            self._difference_status(
                equalized_odds_difference,
                "equalized_odds_difference",
            ),
            self._difference_status(
                false_approval_rate_difference,
                "false_approval_rate_difference",
            ),
        )

        return ExpandedSensitiveAssessment(
            sensitive_feature=sensitive_feature,
            status=status,
            demographic_parity_ratio=demographic_parity_ratio,
            selection_rate_difference=selection_rate_difference,
            equal_opportunity_difference=equal_opportunity_difference,
            equalized_odds_difference=equalized_odds_difference,
            false_approval_rate_difference=false_approval_rate_difference,
            group_metrics=rows,
        )

    def _snapshot(
        self,
        frame: pd.DataFrame,
        probabilities: np.ndarray,
        threshold: float,
    ) -> list[ExpandedSensitiveAssessment]:
        return [
            self._evaluate_feature(
                frame,
                probabilities,
                sensitive_feature,
                threshold,
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
    ) -> ExpandedFairnessReport:
        reference_results = self._snapshot(
            reference,
            reference_probabilities,
            default_threshold,
        )
        current_results = self._snapshot(
            current,
            current_probabilities,
            default_threshold,
        )
        governed = [
            item.status
            for item in current_results
            if item.sensitive_feature in self.governance_sensitive_features
        ]
        return ExpandedFairnessReport(
            scenario=self.scenario,
            primary_sensitive_feature=self.primary_sensitive_feature,
            overall_status=maximum_status(*governed),
            reference=reference_results,
            current=current_results,
            metadata={
                "minimum_group_size": self.minimum_group_size,
                "governance_sensitive_features": sorted(self.governance_sensitive_features),
                "monitored_sensitive_features": self.monitored_sensitive_features,
                "thresholds": self.thresholds,
                "decision_semantics": {
                    "model_positive_class": "default_30d=1",
                    "favorable_decision": "approved when risk_probability < threshold",
                    "equal_opportunity": ("difference in approval rate among applicants with default_30d=0"),
                    "false_approval": ("approval rate among applicants with default_30d=1"),
                },
            },
        )


def save_expanded_fairness_report(
    report: ExpandedFairnessReport,
    *,
    json_path: str | Path,
    csv_path: str | Path,
) -> tuple[Path, Path]:
    json_path = Path(json_path)
    csv_path = Path(csv_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows: list[dict[str, Any]] = []
    for dataset, assessments in (
        ("reference", report.reference),
        ("current", report.current),
    ):
        for assessment in assessments:
            for group in assessment.group_metrics:
                row = group.to_dict()
                row.update(
                    {
                        "dataset": dataset,
                        "assessment_status": assessment.status,
                        "demographic_parity_ratio": assessment.demographic_parity_ratio,
                        "selection_rate_difference": assessment.selection_rate_difference,
                        "equal_opportunity_difference": assessment.equal_opportunity_difference,
                        "equalized_odds_difference": assessment.equalized_odds_difference,
                        "false_approval_rate_difference": assessment.false_approval_rate_difference,
                    }
                )
                rows.append(row)
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return json_path, csv_path
