"""FastAPI application factory for governed CreditScoreV4 serving."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import PlainTextResponse

from creditscore.utils.config import load_yaml

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
    predictor = predictor or ModelPredictor(
        model_path=project_root / str(serving["model_path"]),
        model_name=str(serving["model_name"]),
        model_version=str(serving["model_version"]),
        decision_threshold=float(serving["decision_threshold"]),
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
        version="0.6.0",
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
            metrics.requests.labels(request.method, request.url.path, str(response_status)).inc()
            metrics.request_latency.labels(request.url.path).observe(elapsed)

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
            raise HTTPException(status_code=503, detail="Model is not ready")
        return ModelInfoResponse(
            model_name=predictor.model_name,
            model_version=predictor.model_version,
            model_path=str(predictor.model_path),
            artifact_sha256=predictor.artifact_sha256,
            decision_threshold=predictor.decision_threshold,
        )

    @app.post("/predict", response_model=PredictionResponse)
    def predict(payload: CreditApplicationRequest) -> PredictionResponse:
        try:
            result = predictor.predict_one(payload.model_dump())
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
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
        try:
            results = predictor.predict_batch([item.model_dump() for item in payload.applications])
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
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
