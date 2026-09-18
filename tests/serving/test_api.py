from __future__ import annotations

from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from creditscore.serving.app import create_app
from creditscore.serving.predictor import ModelPredictor


class FakeModel:
    def predict_proba(self, frame):  # type: ignore[no-untyped-def]
        positive = np.full(len(frame), 0.35, dtype=float)
        return np.column_stack([1.0 - positive, positive])


def _payload() -> dict:
    return {
        "application_id": "APP-API",
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


def _client(monkeypatch, tmp_path: Path) -> TestClient:
    artifact = tmp_path / "model.joblib"
    artifact.write_bytes(b"fake-model")
    monkeypatch.setattr("creditscore.serving.predictor.load_model", lambda _: FakeModel())
    monkeypatch.setattr("creditscore.serving.predictor.file_sha256", lambda _: "sha-test")
    predictor = ModelPredictor(
        model_path=artifact,
        model_name="CreditScoreV4",
        model_version="test",
        decision_threshold=0.50,
    )
    config = {
        "serving": {
            "model_path": str(artifact),
            "model_name": "CreditScoreV4",
            "model_version": "test",
            "decision_threshold": 0.50,
            "max_batch_size": 10,
        }
    }
    return TestClient(create_app(root=tmp_path, predictor=predictor, config=config))


def test_health_ready_and_model_endpoints(monkeypatch, tmp_path: Path) -> None:
    with _client(monkeypatch, tmp_path) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").json()["model_ready"] is True
        assert client.get("/model").json()["artifact_sha256"] == "sha-test"


def test_predict_and_batch_endpoints(monkeypatch, tmp_path: Path) -> None:
    with _client(monkeypatch, tmp_path) as client:
        prediction = client.post("/predict", json=_payload())
        batch = client.post("/batch-predict", json={"applications": [_payload(), _payload()]})
    assert prediction.status_code == 200
    assert prediction.json()["approved"] is True
    assert batch.status_code == 200
    assert batch.json()["count"] == 2


def test_metrics_endpoint_exposes_prometheus_data(monkeypatch, tmp_path: Path) -> None:
    with _client(monkeypatch, tmp_path) as client:
        client.post("/predict", json=_payload())
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "creditscore_predictions_total" in response.text
    assert "creditscore_http_requests_total" in response.text
