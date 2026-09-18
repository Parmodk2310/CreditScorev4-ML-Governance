"""Model evaluation, evidence persistence, and ROC visualization."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import RocCurveDisplay

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.model.metrics import calculate_classification_metrics


def evaluate_model(
    model,
    frame: pd.DataFrame,
    *,
    target_column: str = "default_30d",
    threshold: float = 0.50,
    scenario: str,
    vendor: str,
) -> tuple[dict[str, Any], pd.DataFrame]:
    X = frame[MODEL_INPUT_FEATURES].copy()
    y = frame[target_column].astype(int)
    probabilities = model.predict_proba(X)[:, 1]
    metrics = calculate_classification_metrics(y, probabilities, threshold=threshold)
    metrics.update(
        {
            "scenario": scenario,
            "vendor": vendor,
            "n_samples": int(len(frame)),
            "target_rate": float(y.mean()),
            "device_risk_null_rate": float(frame["device_risk_score"].isna().mean()),
        }
    )
    predictions = pd.DataFrame(
        {
            "application_id": frame["application_id"].values,
            "y_true": y.values,
            "probability": probabilities,
        }
    )
    return metrics, predictions


def save_metrics(metrics: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    return path


def save_roc_plot(model, frame: pd.DataFrame, path: str | Path, *, title: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    X = frame[MODEL_INPUT_FEATURES].copy()
    y = frame["default_30d"].astype(int)
    RocCurveDisplay.from_estimator(model, X, y)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()
    return path
