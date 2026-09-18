"""Deterministic synthetic lending data for the CreditScoreV4 incident case study."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SyntheticDataConfig:
    n_samples: int = 50_000
    random_seed: int = 42
    baseline_device_null_rate: float = 0.03


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


def generate_lending_dataset(config: SyntheticDataConfig) -> pd.DataFrame:
    """Generate a reproducible synthetic consumer-lending dataset.

    Protected/evaluation attributes are included for later governance phases but are
    explicitly excluded from Phase 1 model features.
    """
    rng = np.random.default_rng(config.random_seed)
    n = config.n_samples

    age = np.clip(rng.normal(41, 11, n), 21, 70).round().astype(int)
    annual_income = np.clip(rng.lognormal(np.log(62_000), 0.55, n), 16_000, 320_000)
    employment_length = np.clip(rng.gamma(2.2, 3.1, n), 0, 35)
    debt_to_income = np.clip(rng.beta(2.3, 4.2, n), 0.02, 0.90)
    credit_utilization = np.clip(rng.beta(2.0, 3.2, n), 0.01, 0.99)
    credit_history_years = np.clip((age - 18) * rng.uniform(0.25, 0.90, n), 0.5, 45)
    device_risk_score = np.clip(rng.beta(2.0, 2.8, n), 0.001, 0.999)
    bank_transaction_risk = np.clip(rng.beta(1.8, 3.4, n), 0.001, 0.999)
    employment_verification_score = np.clip(rng.beta(4.0, 1.8, n), 0.001, 0.999)

    delinq_lambda = 0.12 + 0.75 * credit_utilization + 0.50 * device_risk_score
    delinquencies_2y = np.clip(rng.poisson(delinq_lambda), 0, 7)
    inquiries_6m = np.clip(rng.poisson(0.8 + 1.2 * credit_utilization), 0, 8)
    open_credit_accounts = np.clip(rng.poisson(5.5, n) + 1, 1, 20)

    region = rng.choice(["north", "south", "east", "west", "central"], n, p=[0.22, 0.22, 0.18, 0.21, 0.17])
    employment_type = rng.choice(
        ["salaried", "self_employed", "contract", "other"],
        n,
        p=[0.58, 0.22, 0.14, 0.06],
    )
    sex = rng.choice(["female", "male"], n, p=[0.48, 0.52])
    synthetic_demographic_group = rng.choice(["group_a", "group_b", "group_c"], n, p=[0.55, 0.30, 0.15])
    age_group = pd.cut(age, bins=[20, 29, 44, 59, 70], labels=["21-29", "30-44", "45-59", "60-70"], include_lowest=True).astype(str)

    # The latent risk function is intentionally non-linear enough to make a tree
    # model useful, but noisy enough that the baseline AUC remains realistic.
    income_scaled = np.log1p(annual_income) - np.log(62_000)
    latent = (
        -4.55
        + 2.35 * debt_to_income
        + 2.55 * credit_utilization
        + 4.75 * device_risk_score
        + 1.55 * bank_transaction_risk
        - 1.35 * employment_verification_score
        + 0.42 * delinquencies_2y
        + 0.14 * inquiries_6m
        - 0.68 * income_scaled
        - 0.030 * credit_history_years
        + 0.30 * (employment_type == "contract")
        + 0.26 * (employment_type == "self_employed")
        + 0.52 * (device_risk_score * credit_utilization)
        + rng.normal(0.0, 0.24, n)
    )
    default_probability = _sigmoid(latent)
    default_30d = rng.binomial(1, default_probability)

    df = pd.DataFrame(
        {
            "application_id": [f"APP-{i:07d}" for i in range(1, n + 1)],
            "age": age,
            "annual_income": annual_income.round(2),
            "employment_length_years": employment_length.round(2),
            "debt_to_income": debt_to_income.round(5),
            "credit_utilization": credit_utilization.round(5),
            "credit_history_years": credit_history_years.round(2),
            "delinquencies_2y": delinquencies_2y,
            "inquiries_6m": inquiries_6m,
            "open_credit_accounts": open_credit_accounts,
            "device_risk_score": device_risk_score.round(5),
            "bank_transaction_risk": bank_transaction_risk.round(5),
            "employment_verification_score": employment_verification_score.round(5),
            "region": region,
            "employment_type": employment_type,
            "sex": sex,
            "age_group": age_group,
            "synthetic_demographic_group": synthetic_demographic_group,
            "default_30d": default_30d,
        }
    )

    # Healthy vendor data still has a small amount of ordinary missingness.
    missing_count = round(n * config.baseline_device_null_rate)
    missing_idx = rng.choice(df.index.to_numpy(), size=missing_count, replace=False)
    df.loc[missing_idx, "device_risk_score"] = np.nan
    return df
