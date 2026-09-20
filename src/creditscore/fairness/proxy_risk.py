"""Statistical proxy-risk screening for Phase 12."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


def eta_squared(values: pd.Series, groups: pd.Series) -> float:
    """Return categorical-group to numeric-feature association in [0, 1]."""
    numeric = pd.to_numeric(values, errors="coerce")
    labels = groups.astype(str)
    valid = numeric.notna() & labels.notna()
    numeric = numeric[valid]
    labels = labels[valid]
    if numeric.empty or labels.nunique() < 2:
        return 0.0

    overall = float(numeric.mean())
    total = float(((numeric - overall) ** 2).sum())
    if total <= 0:
        return 0.0

    between = 0.0
    for group in labels.unique():
        group_values = numeric[labels.eq(group)]
        between += len(group_values) * (float(group_values.mean()) - overall) ** 2
    return float(max(0.0, min(1.0, between / total)))


def cramers_v(values: pd.Series, groups: pd.Series) -> float:
    """Return bias-uncorrected Cramer's V for categorical association."""
    table = pd.crosstab(groups.astype(str), values.astype(str))
    if table.empty or min(table.shape) < 2:
        return 0.0
    result = chi2_contingency(table.to_numpy(), correction=False)
    chi2 = float(np.asarray(result.statistic, dtype=np.float64).item())
    n = float(np.asarray(table.to_numpy().sum(), dtype=np.float64).item())
    denominator = min(table.shape[0] - 1, table.shape[1] - 1)
    if n <= 0 or denominator <= 0:
        return 0.0
    return float(math.sqrt((chi2 / n) / denominator))


@dataclass
class ProxyRiskSignal:
    feature: str
    feature_type: str
    reference_association: float
    current_association: float
    association_delta: float
    model_mean_abs_shap: float
    association_rank: int
    model_influence_rank: int
    review_priority: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProxyRiskReport:
    sensitive_feature: str
    primary_group: str
    review_priority_features: list[str]
    top_association_features: list[str]
    signals: list[ProxyRiskSignal] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sensitive_feature": self.sensitive_feature,
            "primary_group": self.primary_group,
            "review_priority_features": self.review_priority_features,
            "top_association_features": self.top_association_features,
            "signals": [signal.to_dict() for signal in self.signals],
            "metadata": self.metadata,
        }


class ProxyRiskAnalyzer:
    """Pair group association with model influence without claiming causality."""

    def __init__(self, config: dict[str, Any]):
        proxy = config["proxy_risk"]
        self.sensitive_feature = str(proxy["sensitive_feature"])
        self.minimum_group_size = int(proxy["minimum_group_size"])
        self.numeric_features = [str(value) for value in proxy["numeric_features"]]
        self.categorical_features = [str(value) for value in proxy["categorical_features"]]
        self.minimum_association_delta = float(proxy["minimum_association_delta"])
        self.top_association_k = int(proxy["top_association_k"])
        self.top_model_influence_k = int(proxy["top_model_influence_k"])

    def _supported_mask(self, frame: pd.DataFrame) -> pd.Series:
        sensitive = frame[self.sensitive_feature].astype(str)
        counts = sensitive.value_counts()
        supported = set(counts[counts >= self.minimum_group_size].index.astype(str))
        return sensitive.isin(supported)

    def _association(
        self,
        frame: pd.DataFrame,
        feature: str,
        feature_type: str,
    ) -> float:
        supported = self._supported_mask(frame)
        values = frame.loc[supported, feature]
        groups = frame.loc[supported, self.sensitive_feature]
        if feature_type == "numeric":
            return eta_squared(values, groups)
        return cramers_v(values, groups)

    def _raw_feature_influence(
        self,
        shap_global: pd.DataFrame,
        feature: str,
        feature_type: str,
    ) -> float:
        names = shap_global["feature"].astype(str)
        if feature_type == "categorical":
            mask = names.str.startswith(f"{feature}_")
        else:
            mask = names.eq(feature)
        return float(shap_global.loc[mask, "mean_abs_shap"].sum())

    def analyze(
        self,
        reference: pd.DataFrame,
        current: pd.DataFrame,
        *,
        shap_global: pd.DataFrame,
        primary_group: str,
    ) -> ProxyRiskReport:
        if self.sensitive_feature not in reference or self.sensitive_feature not in current:
            raise ValueError(f"Missing proxy sensitive feature: {self.sensitive_feature}")

        rows: list[dict[str, Any]] = []
        for feature_type, features in (
            ("numeric", self.numeric_features),
            ("categorical", self.categorical_features),
        ):
            for feature in features:
                if feature not in reference or feature not in current:
                    raise ValueError(f"Missing proxy-analysis feature: {feature}")
                reference_association = self._association(
                    reference,
                    feature,
                    feature_type,
                )
                current_association = self._association(
                    current,
                    feature,
                    feature_type,
                )
                rows.append(
                    {
                        "feature": feature,
                        "feature_type": feature_type,
                        "reference_association": reference_association,
                        "current_association": current_association,
                        "association_delta": current_association - reference_association,
                        "model_mean_abs_shap": self._raw_feature_influence(
                            shap_global,
                            feature,
                            feature_type,
                        ),
                    }
                )

        table = pd.DataFrame(rows)
        table["association_rank"] = (
            table["association_delta"].rank(method="first", ascending=False).astype(int)
        )
        table["model_influence_rank"] = (
            table["model_mean_abs_shap"].rank(method="first", ascending=False).astype(int)
        )
        table["review_priority"] = table["association_delta"].ge(self.minimum_association_delta) & table[
            "model_influence_rank"
        ].le(self.top_model_influence_k)
        table = table.sort_values(
            ["association_rank", "model_influence_rank"],
            ignore_index=True,
        )

        records = table.to_dict(orient="records")
        signals = [
            ProxyRiskSignal(
                feature=str(record["feature"]),
                feature_type=str(record["feature_type"]),
                reference_association=float(record["reference_association"]),
                current_association=float(record["current_association"]),
                association_delta=float(record["association_delta"]),
                model_mean_abs_shap=float(record["model_mean_abs_shap"]),
                association_rank=int(record["association_rank"]),
                model_influence_rank=int(record["model_influence_rank"]),
                review_priority=bool(record["review_priority"]),
            )
            for record in records
        ]
        return ProxyRiskReport(
            sensitive_feature=self.sensitive_feature,
            primary_group=primary_group,
            review_priority_features=[signal.feature for signal in signals if signal.review_priority],
            top_association_features=[
                signal.feature for signal in signals if signal.association_rank <= self.top_association_k
            ],
            signals=signals,
            metadata={
                "minimum_group_size": self.minimum_group_size,
                "minimum_association_delta": self.minimum_association_delta,
                "top_association_k": self.top_association_k,
                "top_model_influence_k": self.top_model_influence_k,
                "interpretation": (
                    "association plus model influence is a review signal, not proof "
                    "that a feature is a legal or causal proxy"
                ),
            },
        )


def save_proxy_risk_report(
    report: ProxyRiskReport,
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
    pd.DataFrame([signal.to_dict() for signal in report.signals]).to_csv(
        csv_path,
        index=False,
    )
    return json_path, csv_path
