"""CreditScoreV4 baseline model construction and training."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from xgboost import XGBClassifier

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES, build_preprocessor
from creditscore.features.engineering import add_engineered_features


def build_model_pipeline(model_params: dict[str, Any]) -> Pipeline:
    classifier = XGBClassifier(**model_params)
    return Pipeline(
        [
            ("feature_engineering", FunctionTransformer(add_engineered_features, validate=False)),
            ("preprocessor", build_preprocessor()),
            ("classifier", classifier),
        ]
    )


def train_model(
    train_df: pd.DataFrame,
    *,
    target_column: str,
    model_params: dict[str, Any],
) -> Pipeline:
    X_train = train_df[MODEL_INPUT_FEATURES].copy()
    y_train = train_df[target_column].astype(int)
    pipeline = build_model_pipeline(model_params)
    pipeline.fit(X_train, y_train)
    return pipeline


def save_model(model: Pipeline, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(path: str | Path) -> Pipeline:
    return joblib.load(Path(path))
