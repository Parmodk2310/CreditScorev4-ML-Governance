"""Model feature contract and preprocessing pipeline."""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from creditscore.features.engineering import ENGINEERED_FEATURES

NUMERIC_FEATURES = [
    "age",
    "annual_income",
    "employment_length_years",
    "debt_to_income",
    "credit_utilization",
    "credit_history_years",
    "delinquencies_2y",
    "inquiries_6m",
    "open_credit_accounts",
    "device_risk_score",
    "bank_transaction_risk",
    "employment_verification_score",
    *ENGINEERED_FEATURES,
]

CATEGORICAL_FEATURES = ["region", "employment_type"]

MODEL_INPUT_FEATURES = [
    "age",
    "annual_income",
    "employment_length_years",
    "debt_to_income",
    "credit_utilization",
    "credit_history_years",
    "delinquencies_2y",
    "inquiries_6m",
    "open_credit_accounts",
    "device_risk_score",
    "bank_transaction_risk",
    "employment_verification_score",
    "region",
    "employment_type",
]

PROTECTED_EVALUATION_COLUMNS = ["sex", "age_group", "synthetic_demographic_group"]


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median", add_indicator=True))])
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
