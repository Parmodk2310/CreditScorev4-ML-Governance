# src/serving_api/main.py
"""
FastAPI Serving API for CreditScoreV4.
Production-ready inference endpoint with monitoring, caching, and rate limiting.
"""

import hashlib
import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import redis
import xgboost as xgb
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

# Prometheus metrics
PREDICTION_COUNTER = Counter(
    "model_predictions_total",
    "Total predictions",
    ["model_version", "status"]
)
PREDICTION_LATENCY = Histogram(
    "model_prediction_latency_seconds",
    "Prediction latency",
    ["model_version"]
)
PREDICTION_SCORE = Histogram(
    "model_prediction_score",
    "Distribution of prediction scores",
    ["model_version"]
)


class CreditApplication(BaseModel):
    """Input schema for credit scoring."""
    customer_id: str = Field(..., description="Unique customer identifier")
    annual_income: float = Field(..., ge=0, le=5000000)
    debt_to_income_ratio: float = Field(..., ge=0, le=1)
    credit_history_length: float = Field(..., ge=0, le=50)
    device_risk_score: float = Field(..., ge=0, le=1)
    employment_length: float = Field(..., ge=0, le=50)
    num_credit_lines: int = Field(..., ge=0, le=50)
    avg_credit_utilization: float = Field(..., ge=0, le=1)
    loan_purpose: str
    home_ownership: str
    verification_status: str
    state: str
    race: str
    gender: str
    age_group: str


class BatchPredictionRequest(BaseModel):
    """Batch prediction request."""
    applications: List[CreditApplication]
    return_shap: bool = False


class PredictionResponse(BaseModel):
    """Prediction response schema."""
    customer_id: str
    approved: bool
    risk_score: float
    approval_probability: float
    model_version: str
    prediction_id: str
    latency_ms: float
    shap_values: Optional[Dict[str, float]] = None


class ModelRegistry:
    """Simple model registry for loading production models."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("MODEL_PATH", "models/creditscorev4.pkl")
        self.model = None
        self.preprocessor = None
        self.version = "4.2.1"
        self.load_model()
    
    def load_model(self):
        """Load model and preprocessor from disk."""
        import pickle
        with open(self.model_path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.preprocessor = data.get("preprocessor")
        self.version = data.get("version", "4.2.1")
        logger.info(f"Loaded model version {self.version}")
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Generate predictions."""
        return self.model.predict_proba(features)[:, 1]


class PredictionCache:
    """Redis-based prediction cache."""
    
    def __init__(self, redis_url: Optional[str] = None, ttl: int = 300):
        self.redis_client = redis.from_url(redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        self.ttl = ttl
    
    def _make_key(self, application: CreditApplication) -> str:
        """Create cache key from application data."""
        data = application.model_dump_json()
        return f"pred:{hashlib.sha256(data.encode()).hexdigest()[:16]}"
    
    def get(self, application: CreditApplication) -> Optional[Dict[str, Any]]:
        """Get cached prediction."""
        key = self._make_key(application)
        cached = self.redis_client.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    def set(self, application: CreditApplication, result: Dict[str, Any]):
        """Cache prediction result."""
        key = self._make_key(application)
        self.redis_client.setex(key, self.ttl, json.dumps(result))


# Global instances
model_registry: Optional[ModelRegistry] = None
prediction_cache: Optional[PredictionCache] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global model_registry, prediction_cache
    model_registry = ModelRegistry()
    prediction_cache = PredictionCache()
    logger.info("CreditScoreV4 API started")
    yield
    logger.info("CreditScoreV4 API shutting down")


app = FastAPI(
    title="CreditScoreV4 API",
    description="Production ML inference API for credit scoring",
    version="4.2.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID and timing to all requests."""
    request_id = hashlib.sha256(
        f"{request.url}{time.time()}".encode()
    ).hexdigest()[:12]
    request.state.request_id = request_id
    request.state.start_time = time.time()
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_version": model_registry.version if model_registry else "unknown",
        "timestamp": time.time(),
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from starlette.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict", response_model=PredictionResponse)
async def predict(application: CreditApplication, request: Request):
    """
    Single prediction endpoint.
    
    Returns approval decision and risk score.
    """
    start_time = time.time()
    
    # Check cache
    cached = prediction_cache.get(application) if prediction_cache else None
    if cached:
        return PredictionResponse(**cached)
    
    try:
        # Prepare features
        features_df = pd.DataFrame([application.model_dump()])
        
        # Remove protected attributes from model input
        protected = ["race", "gender", "age_group"]
        model_features = features_df.drop(columns=protected, errors="ignore")
        
        # Generate prediction
        risk_score = model_registry.predict(model_features)[0]
        approved = risk_score >= 0.5  # Default threshold
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Create response
        prediction_id = f"{request.state.request_id}-{application.customer_id}"
        
        response = PredictionResponse(
            customer_id=application.customer_id,
            approved=approved,
            risk_score=round(risk_score, 4),
            approval_probability=round(1 - risk_score, 4),
            model_version=model_registry.version,
            prediction_id=prediction_id,
            latency_ms=round(latency_ms, 2),
        )
        
        # Update metrics
        PREDICTION_COUNTER.labels(
            model_version=model_registry.version,
            status="success"
        ).inc()
        PREDICTION_LATENCY.labels(
            model_version=model_registry.version
        ).observe(latency_ms / 1000)
        PREDICTION_SCORE.labels(
            model_version=model_registry.version
        ).observe(risk_score)
        
        # Cache result
        prediction_cache.set(application, response.model_dump())
        
        # Audit log
        logger.info(
            f"Prediction: customer={application.customer_id}, "
            f"score={risk_score:.4f}, approved={approved}, "
            f"latency={latency_ms:.2f}ms"
        )
        
        return response
        
    except Exception as e:
        PREDICTION_COUNTER.labels(
            model_version=model_registry.version,
            status="error"
        ).inc()
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict/batch")
async def predict_batch(request: BatchPredictionRequest):
    """Batch prediction endpoint."""
    results = []
    
    for app in request.applications:
        try:
            result = await predict(app, Request({"type": "http"}))
            results.append(result.model_dump())
        except Exception as e:
            results.append({
                "customer_id": app.customer_id,
                "error": str(e),
            })
    
    return {
        "predictions": results,
        "model_version": model_registry.version if model_registry else "unknown",
        "count": len(results),
    }


@app.get("/model/info")
async def model_info():
    """Get current model information."""
    return {
        "model_name": "CreditScoreV4",
        "version": model_registry.version if model_registry else "unknown",
        "framework": "xgboost",
        "features": [
            "annual_income", "debt_to_income_ratio", "credit_history_length",
            "device_risk_score", "employment_length", "num_credit_lines",
            "avg_credit_utilization", "loan_purpose", "home_ownership",
            "verification_status", "state",
        ],
        "protected_attributes": ["race", "gender", "age_group"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)