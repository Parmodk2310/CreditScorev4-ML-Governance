"""Prometheus instrumentation for the Phase 6 serving surface."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest


class ServingMetrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry(auto_describe=True)
        self.requests = Counter(
            "creditscore_http_requests_total",
            "HTTP requests handled by the CreditScoreV4 API.",
            ["method", "route", "status"],
            registry=self.registry,
        )
        self.request_latency = Histogram(
            "creditscore_http_request_duration_seconds",
            "HTTP request duration in seconds.",
            ["route"],
            registry=self.registry,
        )
        self.predictions = Counter(
            "creditscore_predictions_total",
            "CreditScoreV4 predictions by model outcome.",
            ["predicted_default", "approved"],
            registry=self.registry,
        )
        self.risk_probability = Histogram(
            "creditscore_risk_probability",
            "Observed model risk probabilities.",
            buckets=(0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.0),
            registry=self.registry,
        )
        self.model_ready = Gauge(
            "creditscore_model_ready",
            "Whether the serving model is loaded and ready.",
            registry=self.registry,
        )
        self.release_stage = Gauge(
            "creditscore_release_stage",
            "Current release stage represented as a labeled one-hot gauge.",
            ["stage"],
            registry=self.registry,
        )
        self.canary_share = Gauge(
            "creditscore_canary_share",
            "Fraction of eligible requests routed to the candidate model.",
            registry=self.registry,
        )
        self.rollback_events = Gauge(
            "creditscore_release_rollback_events",
            "Number of rollback events recorded in the Phase 6 release audit.",
            registry=self.registry,
        )

    def record_prediction(self, *, predicted_default: int, approved: bool, risk_probability: float) -> None:
        self.predictions.labels(str(predicted_default), str(approved).lower()).inc()
        self.risk_probability.observe(float(risk_probability))

    def set_stage(self, stage: str) -> None:
        for candidate in ("STAGING", "SHADOW", "CANARY", "PRODUCTION", "REJECTED"):
            self.release_stage.labels(candidate).set(1.0 if candidate == stage else 0.0)

    def render(self) -> bytes:
        return generate_latest(self.registry)
