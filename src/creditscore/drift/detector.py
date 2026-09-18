"""Feature and prediction drift orchestration."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .ks import calculate_ks
from .models import DriftMetricResult, DriftReport, maximum_severity
from .psi import calculate_psi


class DriftDetector:
    def __init__(self, config: dict[str, Any]):
        monitoring = config["monitoring"]
        self.features = list(monitoring["features"])
        self.psi_config = monitoring["psi"]
        self.ks_config = monitoring["ks"]
        self.scenario = str(config["scenario"]["name"])
        self.reference_source = str(config["scenario"]["reference_source"])
        self.current_source = str(config["scenario"]["source"])

    def _psi_status(self, value: float) -> str:
        if value >= float(self.psi_config["critical"]):
            return "CRITICAL"
        if value >= float(self.psi_config["warning"]):
            return "WARNING"
        return "STABLE"

    def _ks_status(self, statistic: float, pvalue: float) -> str:
        if pvalue >= float(self.ks_config["alpha"]):
            return "STABLE"
        if statistic >= float(self.ks_config["critical"]):
            return "CRITICAL"
        if statistic >= float(self.ks_config["warning"]):
            return "WARNING"
        return "STABLE"

    def _evaluate_series(self, name: str, reference: pd.Series, current: pd.Series) -> DriftMetricResult:
        psi = calculate_psi(
            reference,
            current,
            bins=int(self.psi_config["bins"]),
            epsilon=float(self.psi_config["epsilon"]),
        )
        ks = calculate_ks(reference, current)
        psi_status = self._psi_status(psi)
        ks_status = self._ks_status(ks.statistic, ks.pvalue)

        reference_numeric = pd.to_numeric(reference, errors="coerce")
        current_numeric = pd.to_numeric(current, errors="coerce")
        reference_mean = None if reference_numeric.dropna().empty else float(reference_numeric.mean())
        current_mean = None if current_numeric.dropna().empty else float(current_numeric.mean())

        return DriftMetricResult(
            feature=name,
            psi=psi,
            psi_status=psi_status,
            ks_statistic=ks.statistic,
            ks_pvalue=ks.pvalue,
            ks_status=ks_status,
            status=maximum_severity(psi_status, ks_status),
            reference_mean=reference_mean,
            current_mean=current_mean,
            reference_null_rate=float(reference_numeric.isna().mean()),
            current_null_rate=float(current_numeric.isna().mean()),
            reference_count=ks.reference_count,
            current_count=ks.current_count,
        )

    def evaluate(
        self,
        reference: pd.DataFrame,
        current: pd.DataFrame,
        *,
        reference_predictions: pd.Series,
        current_predictions: pd.Series,
        approval_threshold: float,
    ) -> DriftReport:
        missing_features = [
            feature for feature in self.features if feature not in reference or feature not in current
        ]
        if missing_features:
            raise ValueError(f"Missing monitored features: {missing_features}")

        feature_results = [
            self._evaluate_series(feature, reference[feature], current[feature]) for feature in self.features
        ]
        prediction_result = self._evaluate_series(
            "risk_probability",
            reference_predictions,
            current_predictions,
        )
        statuses = [result.status for result in feature_results] + [prediction_result.status]
        overall_status = maximum_severity(*statuses)

        reference_approval = float((reference_predictions < approval_threshold).mean())
        current_approval = float((current_predictions < approval_threshold).mean())
        prediction_summary = {
            "reference_mean_risk": float(reference_predictions.mean()),
            "current_mean_risk": float(current_predictions.mean()),
            "mean_risk_shift": float(current_predictions.mean() - reference_predictions.mean()),
            "reference_approval_rate": reference_approval,
            "current_approval_rate": current_approval,
            "approval_rate_shift": current_approval - reference_approval,
        }

        return DriftReport(
            scenario=self.scenario,
            reference_source=self.reference_source,
            current_source=self.current_source,
            overall_status=overall_status,
            feature_results=feature_results,
            prediction_result=prediction_result,
            prediction_summary=prediction_summary,
            metadata={
                "psi_thresholds": {
                    "warning": float(self.psi_config["warning"]),
                    "critical": float(self.psi_config["critical"]),
                },
                "ks_thresholds": {
                    "warning": float(self.ks_config["warning"]),
                    "critical": float(self.ks_config["critical"]),
                    "alpha": float(self.ks_config["alpha"]),
                },
            },
        )
