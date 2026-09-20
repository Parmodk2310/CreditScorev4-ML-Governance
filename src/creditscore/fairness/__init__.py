"""Fairness assessment package."""

from .evaluator import FairnessEvaluator
from .expanded import (
    ExpandedFairnessEvaluator,
    ExpandedFairnessReport,
    ExpandedSensitiveAssessment,
    add_intersection_column,
    save_expanded_fairness_report,
)
from .models import FairnessReport, SensitiveFeatureAssessment
from .proxy_risk import ProxyRiskAnalyzer, ProxyRiskReport, save_proxy_risk_report
from .report import save_fairness_report

__all__ = [
    "ExpandedFairnessEvaluator",
    "ExpandedFairnessReport",
    "ExpandedSensitiveAssessment",
    "FairnessEvaluator",
    "FairnessReport",
    "ProxyRiskAnalyzer",
    "ProxyRiskReport",
    "SensitiveFeatureAssessment",
    "add_intersection_column",
    "save_expanded_fairness_report",
    "save_fairness_report",
    "save_proxy_risk_report",
]
