"""FastAPI request/response schemas for CreditScoreV4 serving."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreditApplicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str | None = None
    age: int = Field(ge=18, le=100)
    annual_income: float = Field(gt=0)
    employment_length_years: float = Field(ge=0)
    debt_to_income: float = Field(ge=0, le=1)
    credit_utilization: float = Field(ge=0, le=1)
    credit_history_years: float = Field(ge=0)
    delinquencies_2y: int = Field(ge=0)
    inquiries_6m: int = Field(ge=0)
    open_credit_accounts: int = Field(ge=0)
    device_risk_score: float | None = Field(default=None, ge=0, le=1)
    bank_transaction_risk: float = Field(ge=0, le=1)
    employment_verification_score: float = Field(ge=0, le=1)
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
    model_path: str
    artifact_sha256: str
    decision_threshold: float
