"""FastAPI application factory for governed CreditScoreV4 serving."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import PlainTextResponse

from creditscore import __version__
from creditscore.utils.config import decision_threshold, load_yaml
from creditscore.validation import RecordContractValidator, load_data_contract

from .metrics import ServingMetrics
from .predictor import ModelPredictor
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    CreditApplicationRequest,
    HealthResponse,
    ModelInfoResponse,
    PredictionResponse,
    ReadyResponse,
)

LOGGER = logging.getLogger(__name__)


def _resolve_path(project_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _load_expected_model_digest(project_root: Path, serving: dict[str, Any]) -> str:
    evidence_path = _resolve_path(
        project_root,
        str(serving.get("model_evidence_path", "data/evidence/phase1/baseline_metrics.json")),
    )
    if not evidence_path.is_file():
        raise RuntimeError("Model integrity evidence is missing")

    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    digest = str(payload.get("model_artifact_sha256", "")).strip().lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RuntimeError("Model integrity evidence does not contain a valid SHA-256 digest")
    return digest


def create_app(
    *,
    root: str | Path | None = None,
    predictor: ModelPredictor | None = None,
    config: dict[str, Any] | None = None,
    metrics: ServingMetrics | None = None,
) -> FastAPI:
    project_root = Path(root or Path.cwd())
    phase6 = config or load_yaml(project_root / "configs" / "phase6.yaml")
    serving = phase6["serving"]

    contract_path = _resolve_path(
        project_root,
        str(serving.get("contract_path", "contracts/credit_application_contract.yaml")),
    )
    record_validator = RecordContractValidator(load_data_contract(contract_path))

    if predictor is None:
        expected_digest = _load_expected_model_digest(project_root, serving)
        predictor = ModelPredictor(
            model_path=project_root / str(serving["model_path"]),
            model_name=str(serving["model_name"]),
            model_version=str(serving["model_version"]),
            decision_threshold=decision_threshold(project_root),
            expected_artifact_sha256=expected_digest,
        )

    metrics = metrics or ServingMetrics()
    max_batch_size = int(serving["max_batch_size"])

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        predictor.load()
        metrics.model_ready.set(1.0)
        metrics.set_stage("STAGING")
        metrics.canary_share.set(0.0)
        yield

    app = FastAPI(
        title="CreditScoreV4 Serving API",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.predictor = predictor
    app.state.metrics = metrics

    @app.middleware("http")
    async def instrument(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        started = time.perf_counter()
        response_status = 500
        try:
            response = await call_next(request)
            response_status = response.status_code
            return response
        finally:
            elapsed = time.perf_counter() - started
            route = request.scope.get("route")
            route_label = str(getattr(route, "path", "unmatched") or "unmatched")
            metrics.requests.labels(request.method, route_label, str(response_status)).inc()
            metrics.request_latency.labels(route_label).observe(elapsed)

    def validated_records(items: list[CreditApplicationRequest]) -> list[dict[str, Any]]:
        records = [item.model_dump() for item in items]
        violations: list[dict[str, Any]] = []
        for index, record in enumerate(records):
            for violation in record_validator.validate(record):
                item: dict[str, Any] = violation.to_dict()
                item["record_index"] = index
                violations.append(item)
        if violations:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INPUT_CONTRACT_VIOLATION",
                    "message": "Request does not satisfy the governed scoring contract.",
                    "violations": violations,
                },
            )
        return records

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/ready", response_model=ReadyResponse)
    def ready(response: Response) -> ReadyResponse:
        is_ready = predictor.ready
        if not is_ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(status="ready" if is_ready else "not_ready", model_ready=is_ready)

    @app.get("/model", response_model=ModelInfoResponse)
    def model_info() -> ModelInfoResponse:
        if not predictor.ready:
            raise HTTPException(status_code=503, detail="Model service unavailable")
        return ModelInfoResponse(
            model_name=predictor.model_name,
            model_version=predictor.model_version,
            artifact_sha256=predictor.artifact_sha256,
            decision_threshold=predictor.decision_threshold,
        )

    @app.post("/predict", response_model=PredictionResponse)
    def predict(payload: CreditApplicationRequest) -> PredictionResponse:
        record = validated_records([payload])[0]
        try:
            result = predictor.predict_one(record)
        except ValueError as exc:
            LOGGER.warning("Prediction rejected by model-input validation", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid model input",
            ) from exc
        except RuntimeError as exc:
            LOGGER.exception("Prediction service unavailable")
            raise HTTPException(status_code=503, detail="Model service unavailable") from exc

        metrics.record_prediction(
            predicted_default=result.predicted_default,
            approved=result.approved,
            risk_probability=result.risk_probability,
        )
        return PredictionResponse(**result.to_dict())

    @app.post("/batch-predict", response_model=BatchPredictionResponse)
    def batch_predict(payload: BatchPredictionRequest) -> BatchPredictionResponse:
        if not payload.applications:
            raise HTTPException(status_code=422, detail="At least one application is required")
        if len(payload.applications) > max_batch_size:
            raise HTTPException(
                status_code=413,
                detail=f"Batch size exceeds configured maximum of {max_batch_size}",
            )

        records = validated_records(payload.applications)
        try:
            results = predictor.predict_batch(records)
        except ValueError as exc:
            LOGGER.warning("Batch prediction rejected by model-input validation", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid model input",
            ) from exc
        except RuntimeError as exc:
            LOGGER.exception("Batch prediction service unavailable")
            raise HTTPException(status_code=503, detail="Model service unavailable") from exc

        for result in results:
            metrics.record_prediction(
                predicted_default=result.predicted_default,
                approved=result.approved,
                risk_probability=result.risk_probability,
            )
        predictions = [PredictionResponse(**result.to_dict()) for result in results]
        return BatchPredictionResponse(predictions=predictions, count=len(predictions))

    @app.get("/metrics", response_class=PlainTextResponse)
    def prometheus_metrics() -> PlainTextResponse:
        release = phase6.get("release")
        if isinstance(release, dict):
            state_path = project_root / str(release.get("state_path", ""))
            if state_path.is_file():
                state_payload = json.loads(state_path.read_text(encoding="utf-8"))
                metrics.set_stage(str(state_payload.get("stage", "STAGING")))
                metrics.canary_share.set(float(state_payload.get("canary_share", 0.0)))
            audit_path = project_root / str(release.get("audit_log", ""))
            if audit_path.is_file():
                rollback_events = 0
                for line in audit_path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    rollback_events += int(record.get("event_type") == "RELEASE_ROLLED_BACK")
                metrics.rollback_events.set(float(rollback_events))
        return PlainTextResponse(metrics.render().decode("utf-8"), media_type="text/plain; version=0.0.4")

    return app
