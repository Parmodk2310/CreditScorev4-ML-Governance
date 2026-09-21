from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from creditscore.serving.predictor import ModelPredictor


class FakeModel:
    def predict_proba(self, frame):  # type: ignore[no-untyped-def]
        positive = np.linspace(0.25, 0.75, len(frame))
        return np.column_stack([1.0 - positive, positive])


def _record() -> dict:
    return {
        "application_id": "APP-TEST",
        "age": 40,
        "annual_income": 70000.0,
        "employment_length_years": 8.0,
        "debt_to_income": 0.30,
        "credit_utilization": 0.35,
        "credit_history_years": 12.0,
        "delinquencies_2y": 0,
        "inquiries_6m": 1,
        "open_credit_accounts": 6,
        "device_risk_score": 0.20,
        "bank_transaction_risk": 0.25,
        "employment_verification_score": 0.80,
        "region": "north",
        "employment_type": "salaried",
    }


def test_predictor_returns_risk_and_decision(monkeypatch, tmp_path: Path) -> None:
    artifact = tmp_path / "model.joblib"
    artifact.write_bytes(b"fake-model")
    events: list[str] = []

    def fake_hash(_: Path) -> str:
        events.append("hash")
        return "abc123"

    def fake_load(_: Path) -> FakeModel:
        events.append("load")
        return FakeModel()

    monkeypatch.setattr("creditscore.serving.predictor.file_sha256", fake_hash)
    monkeypatch.setattr("creditscore.serving.predictor.load_model", fake_load)

    predictor = ModelPredictor(
        model_path=artifact,
        model_name="CreditScoreV4",
        model_version="test",
        decision_threshold=0.50,
        expected_artifact_sha256="abc123",
    )
    predictor.load()
    low, high = predictor.predict_batch([_record(), _record()])

    assert events[:2] == ["hash", "load"]
    assert low.risk_probability == 0.25
    assert low.approved is True
    assert high.risk_probability == 0.75
    assert high.predicted_default == 1
    assert predictor.artifact_sha256 == "abc123"

    events.clear()
    rejected = ModelPredictor(
        model_path=artifact,
        model_name="CreditScoreV4",
        model_version="tampered",
        expected_artifact_sha256="different-digest",
    )
    with pytest.raises(RuntimeError, match="integrity"):
        rejected.load()
    assert events == ["hash"], "Deserialization must not run after a digest mismatch"
