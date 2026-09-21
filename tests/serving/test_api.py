from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from creditscore.serving.app import create_app
from creditscore.serving.predictor import ModelPredictor

ROOT = Path(__file__).resolve().parents[2]
TEST_SHA256 = "a" * 64


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
    monkeypatch.setattr("creditscore.serving.predictor.file_sha256", lambda _: TEST_SHA256)
    predictor = ModelPredictor(
        model_path=artifact,
        model_name="CreditScoreV4",
        model_version="test",
        decision_threshold=0.50,
        expected_artifact_sha256=TEST_SHA256,
    )
    config = {
        "serving": {
            "model_path": str(artifact),
            "model_name": "CreditScoreV4",
            "model_version": "test",
            "contract_path": str(ROOT / "contracts" / "credit_application_contract.yaml"),
            "decision_threshold": 0.50,
            "max_batch_size": 10,
        }
    }
    return TestClient(create_app(root=tmp_path, predictor=predictor, config=config))


def test_health_ready_and_model_endpoints(monkeypatch, tmp_path: Path) -> None:
    with _client(monkeypatch, tmp_path) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").json()["model_ready"] is True

        model = client.get("/model").json()
        assert model["artifact_sha256"] == TEST_SHA256
        assert "model_path" not in model

        openapi = client.get("/openapi.json").json()
        assert openapi["info"]["version"] == version("creditscorev4-ml-governance")

        monkeypatch.setattr(
            ModelPredictor,
            "predict_one",
            lambda self, record: (_ for _ in ()).throw(RuntimeError("/internal/secret/model.joblib")),
        )
        failed = client.post("/predict", json=_payload())
        assert failed.status_code == 503
        assert "/internal/secret/model.joblib" not in failed.text
        assert failed.json()["detail"] == "Model service unavailable"


def test_predict_and_batch_endpoints(monkeypatch, tmp_path: Path) -> None:
    with _client(monkeypatch, tmp_path) as client:
        prediction = client.post("/predict", json=_payload())
        batch = client.post("/batch-predict", json={"applications": [_payload(), _payload()]})

        invalid_age = _payload()
        invalid_age["age"] = 90
        age_response = client.post("/predict", json=invalid_age)

        invalid_region = _payload()
        invalid_region["region"] = "unknown-region"
        region_response = client.post("/predict", json=invalid_region)

    assert prediction.status_code == 200
    assert prediction.json()["approved"] is True
    assert batch.status_code == 200
    assert batch.json()["count"] == 2
    assert age_response.status_code == 422
    assert age_response.json()["detail"]["code"] == "INPUT_CONTRACT_VIOLATION"
    assert region_response.status_code == 422
    assert region_response.json()["detail"]["code"] == "INPUT_CONTRACT_VIOLATION"


def test_metrics_endpoint_exposes_prometheus_data(monkeypatch, tmp_path: Path) -> None:
    with _client(monkeypatch, tmp_path) as client:
        client.post("/predict", json=_payload())
        client.get("/missing/123")
        client.get("/missing/456")
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "creditscore_predictions_total" in response.text
    assert "creditscore_http_requests_total" in response.text
    assert 'route="/predict"' in response.text
    assert 'route="unmatched"' in response.text
    assert "/missing/123" not in response.text
    assert "/missing/456" not in response.text
