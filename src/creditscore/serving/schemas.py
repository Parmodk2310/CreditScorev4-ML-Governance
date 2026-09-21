"""FastAPI request/response schemas for CreditScoreV4 serving."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CreditApplicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str
    age: int
    annual_income: float
    employment_length_years: float
    debt_to_income: float
    credit_utilization: float
    credit_history_years: float
    delinquencies_2y: int
    inquiries_6m: int
    open_credit_accounts: int
    device_risk_score: float | None = None
    bank_transaction_risk: float
    employment_verification_score: float
    region: str
    employment_type: str


class BatchPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applications: list[CreditApplicationRequest]


class PredictionResponse(BaseModel):
    application_id: str | None
    risk_probability: float
    predicted_default: int
    approved: bool
    model_name: str
    model_version: str


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]
    count: int


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    model_ready: bool


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    artifact_sha256: str
    decision_threshold: float
