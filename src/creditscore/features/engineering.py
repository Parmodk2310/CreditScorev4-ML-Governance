"""Leakage-safe feature engineering shared by training and inference."""
from __future__ import annotations

import pandas as pd

ENGINEERED_FEATURES = [
    "utilization_x_dti",
    "income_per_open_account",
    "history_to_age_ratio",
]


def add_engineered_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["utilization_x_dti"] = result["credit_utilization"] * result["debt_to_income"]
    result["income_per_open_account"] = result["annual_income"] / result["open_credit_accounts"].clip(lower=1)
    result["history_to_age_ratio"] = result["credit_history_years"] / result["age"].clip(lower=1)
    return result
