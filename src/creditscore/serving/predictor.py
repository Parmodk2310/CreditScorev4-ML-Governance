"""Thread-safe prediction wrapper around the persisted CreditScoreV4 pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.model.train import load_model
from creditscore.utils.hashing import file_sha256


@dataclass(frozen=True)
class PredictionResult:
    application_id: str | None
    risk_probability: float
    predicted_default: int
    approved: bool
    model_name: str
    model_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "application_id": self.application_id,
            "risk_probability": self.risk_probability,
            "predicted_default": self.predicted_default,
            "approved": self.approved,
            "model_name": self.model_name,
            "model_version": self.model_version,
        }


class ModelPredictor:
    """Load once and expose deterministic single/batch risk predictions."""

    def __init__(
        self,
        *,
        model_path: str | Path,
        model_name: str,
        model_version: str,
        expected_artifact_sha256: str,
        decision_threshold: float = 0.50,
    ) -> None:
        self.model_path = Path(model_path)
        self.model_name = str(model_name)
        self.model_version = str(model_version)
        self.expected_artifact_sha256 = str(expected_artifact_sha256).strip().lower()
        if not self.expected_artifact_sha256:
            raise ValueError("Expected model artifact SHA-256 is required")
        self.decision_threshold = float(decision_threshold)
        self._lock = RLock()
        self._model: Pipeline | None = None
        self._artifact_sha256: str | None = None

    @property
    def ready(self) -> bool:
        return self._model is not None

    @property
    def artifact_sha256(self) -> str:
        if self._artifact_sha256 is None:
            raise RuntimeError("Model artifact has not been loaded yet")
        return self._artifact_sha256

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model artifact not found: {self.model_path}")
        with self._lock:
            if self._model is None:
                actual_sha256 = file_sha256(self.model_path).lower()
                if actual_sha256 != self.expected_artifact_sha256:
                    raise RuntimeError(
                        "Model artifact SHA-256 mismatch; refusing to deserialize " f"{self.model_path}"
                    )
                self._model = load_model(self.model_path)
                self._artifact_sha256 = actual_sha256

    def _require_model(self) -> Pipeline:
        if self._model is None:
            raise RuntimeError("Model is not loaded")
        return self._model

    @staticmethod
    def _frame(records: list[dict[str, Any]]) -> pd.DataFrame:
        frame = pd.DataFrame(records)
        missing = [column for column in MODEL_INPUT_FEATURES if column not in frame.columns]
        if missing:
            raise ValueError(f"Missing model input features: {', '.join(sorted(missing))}")
        return frame[MODEL_INPUT_FEATURES].copy()

    def predict_batch(self, records: list[dict[str, Any]]) -> list[PredictionResult]:
        if not records:
            return []
        model = self._require_model()
        frame = self._frame(records)
        with self._lock:
            probabilities = np.asarray(model.predict_proba(frame)[:, 1], dtype=float)

        results: list[PredictionResult] = []
        for record, probability in zip(records, probabilities, strict=True):
            risk = float(probability)
            predicted_default = int(risk >= self.decision_threshold)
            results.append(
                PredictionResult(
                    application_id=record.get("application_id"),
                    risk_probability=risk,
                    predicted_default=predicted_default,
                    approved=risk < self.decision_threshold,
                    model_name=self.model_name,
                    model_version=self.model_version,
                )
            )
        return results

    def predict_one(self, record: dict[str, Any]) -> PredictionResult:
        return self.predict_batch([record])[0]
