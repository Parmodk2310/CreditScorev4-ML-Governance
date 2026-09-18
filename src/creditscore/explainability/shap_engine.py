"""SHAP explanation engine for the fitted CreditScoreV4 XGBoost pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap
from scipy import sparse

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES, PROTECTED_EVALUATION_COLUMNS


def _clean_feature_name(name: str) -> str:
    for prefix in ("numeric__", "categorical__"):
        if name.startswith(prefix):
            return name[len(prefix) :]
    return name


@dataclass
class ShapAnalysis:
    global_importance: pd.DataFrame
    group_importance: pd.DataFrame
    group_delta: pd.DataFrame
    summary: dict[str, Any]


class ShapEngine:
    """Explain the model after applying the exact fitted feature transforms."""

    def __init__(self, model: Any):
        self.model = model

    def _transform(self, frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
        feature_engineering = self.model.named_steps["feature_engineering"]
        preprocessor = self.model.named_steps["preprocessor"]
        engineered = feature_engineering.transform(frame[MODEL_INPUT_FEATURES].copy())
        transformed = preprocessor.transform(engineered)
        if sparse.issparse(transformed):
            transformed = transformed.toarray()
        matrix = np.asarray(transformed, dtype=float)
        names = [_clean_feature_name(str(item)) for item in preprocessor.get_feature_names_out()]
        return matrix, names

    @staticmethod
    def _values(explainer: Any, matrix: np.ndarray) -> np.ndarray:
        explanation = explainer(matrix)
        values = np.asarray(explanation.values)
        if values.ndim == 3:
            values = values[:, :, -1]
        if values.ndim != 2:
            raise ValueError(f"Unexpected SHAP value shape: {values.shape}")
        return values

    def explain(
        self,
        frame: pd.DataFrame,
        *,
        sensitive_feature: str,
        primary_group: str,
        sample_size: int,
        random_seed: int,
        top_k: int,
        local_examples: int,
    ) -> ShapAnalysis:
        if sensitive_feature not in frame.columns:
            raise ValueError(f"Missing sensitive feature: {sensitive_feature}")

        sample_n = min(int(sample_size), len(frame))
        sample = frame.sample(n=sample_n, random_state=random_seed).copy()
        matrix, feature_names = self._transform(sample)
        protected_leaks = [
            column
            for column in PROTECTED_EVALUATION_COLUMNS
            if any(column in feature_name for feature_name in feature_names)
        ]
        if protected_leaks:
            raise RuntimeError(f"Protected attributes reached SHAP feature space: {protected_leaks}")

        classifier = self.model.named_steps["classifier"]
        explainer = shap.TreeExplainer(classifier)
        values = self._values(explainer, matrix)

        global_frame = pd.DataFrame(
            {
                "feature": feature_names,
                "mean_abs_shap": np.abs(values).mean(axis=0),
                "mean_shap": values.mean(axis=0),
            }
        ).sort_values("mean_abs_shap", ascending=False, ignore_index=True)
        global_frame.insert(0, "rank", np.arange(1, len(global_frame) + 1))

        group_rows: list[dict[str, Any]] = []
        sensitive_values = sample[sensitive_feature].astype(str).to_numpy()
        for group in sorted(pd.unique(sensitive_values)):
            group_mask = sensitive_values == str(group)
            group_values = values[group_mask]
            for index, feature in enumerate(feature_names):
                group_rows.append(
                    {
                        "sensitive_feature": sensitive_feature,
                        "group": str(group),
                        "sample_count": int(group_mask.sum()),
                        "feature": feature,
                        "mean_abs_shap": float(np.abs(group_values[:, index]).mean()),
                        "mean_shap": float(group_values[:, index].mean()),
                    }
                )
        group_frame = pd.DataFrame(group_rows)
        group_frame["rank_within_group"] = group_frame.groupby("group")["mean_abs_shap"].rank(
            method="first", ascending=False
        )
        group_frame = group_frame.sort_values(["group", "rank_within_group"], ignore_index=True)

        primary = group_frame[group_frame["group"].eq(primary_group)].copy()
        if primary.empty:
            raise ValueError(f"Primary group not present in SHAP sample: {primary_group}")
        overall_signed = global_frame.set_index("feature")["mean_shap"]
        primary["overall_mean_shap"] = primary["feature"].map(overall_signed)
        primary["delta_mean_shap"] = primary["mean_shap"] - primary["overall_mean_shap"]
        group_delta = primary.sort_values("delta_mean_shap", ascending=False, ignore_index=True)

        probabilities = self.model.predict_proba(sample[MODEL_INPUT_FEATURES])[:, 1]
        primary_indices = np.flatnonzero(sensitive_values == primary_group)
        local_payload: list[dict[str, Any]] = []
        if primary_indices.size:
            ordered = primary_indices[np.argsort(-probabilities[primary_indices])]
            for sample_position in ordered[: max(0, int(local_examples))]:
                row_values = values[sample_position]
                top_indices = np.argsort(-np.abs(row_values))[:top_k]
                local_payload.append(
                    {
                        "application_id": str(sample.iloc[sample_position]["application_id"]),
                        "group": primary_group,
                        "risk_probability": float(probabilities[sample_position]),
                        "top_contributions": [
                            {
                                "feature": feature_names[index],
                                "shap_value": float(row_values[index]),
                            }
                            for index in top_indices
                        ],
                    }
                )

        positive_group_features = (
            primary.sort_values("mean_shap", ascending=False)["feature"].head(top_k).tolist()
        )
        summary = {
            "sample_size": sample_n,
            "sensitive_feature": sensitive_feature,
            "primary_group": primary_group,
            "top_k": top_k,
            "protected_evaluation_columns": PROTECTED_EVALUATION_COLUMNS,
            "protected_attributes_present_in_model_feature_space": False,
            "top_global_features": global_frame.head(top_k)["feature"].tolist(),
            "top_positive_primary_group_features": positive_group_features,
            "local_examples": local_payload,
        }
        return ShapAnalysis(
            global_importance=global_frame,
            group_importance=group_frame,
            group_delta=group_delta,
            summary=summary,
        )

    @staticmethod
    def save(
        analysis: ShapAnalysis,
        *,
        summary_path: str | Path,
        global_path: str | Path,
        group_path: str | Path,
        delta_path: str | Path,
    ) -> tuple[Path, Path, Path, Path]:
        summary_path = Path(summary_path)
        global_path = Path(global_path)
        group_path = Path(group_path)
        delta_path = Path(delta_path)
        for path in (summary_path, global_path, group_path, delta_path):
            path.parent.mkdir(parents=True, exist_ok=True)

        summary_path.write_text(json.dumps(analysis.summary, indent=2, sort_keys=True), encoding="utf-8")
        analysis.global_importance.to_csv(global_path, index=False)
        analysis.group_importance.to_csv(group_path, index=False)
        analysis.group_delta.to_csv(delta_path, index=False)
        return summary_path, global_path, group_path, delta_path
