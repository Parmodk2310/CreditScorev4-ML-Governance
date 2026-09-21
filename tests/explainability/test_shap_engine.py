from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES, PROTECTED_EVALUATION_COLUMNS
from creditscore.explainability.shap_engine import ShapEngine


class FakeFeatureEngineering:
    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        return frame


class FakePreprocessor:
    def __init__(self, feature_names: list[str]) -> None:
        self.feature_names = feature_names

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        return np.zeros((len(frame), len(self.feature_names)), dtype=float)

    def get_feature_names_out(self) -> np.ndarray:
        return np.asarray(self.feature_names, dtype=object)


class FakeModel:
    def __init__(self, feature_names: list[str]) -> None:
        self.named_steps = {
            "feature_engineering": FakeFeatureEngineering(),
            "preprocessor": FakePreprocessor(feature_names),
            "classifier": object(),
        }

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        positive = np.linspace(0.20, 0.80, len(frame), dtype=float)
        return np.column_stack([1.0 - positive, positive])


class FakeExplainer:
    def __call__(self, matrix: np.ndarray) -> SimpleNamespace:
        values = np.tile(np.asarray([0.20, -0.10], dtype=float), (len(matrix), 1))
        return SimpleNamespace(values=values)


def _frame() -> pd.DataFrame:
    base = {
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
    rows = []
    for index, group in enumerate(["group_a", "group_c", "group_a", "group_c"]):
        row = dict(base)
        row["application_id"] = f"APP-{index}"
        row["synthetic_demographic_group"] = group
        row["sex"] = "female" if index % 2 else "male"
        row["age_group"] = "30-44"
        rows.append(row)
    return pd.DataFrame(rows)


def test_protected_evaluation_columns_are_not_model_inputs() -> None:
    assert all(column not in MODEL_INPUT_FEATURES for column in PROTECTED_EVALUATION_COLUMNS)


def test_explain_builds_global_group_and_local_evidence(monkeypatch) -> None:
    monkeypatch.setattr(
        "creditscore.explainability.shap_engine.shap.TreeExplainer",
        lambda _: FakeExplainer(),
    )
    engine = ShapEngine(FakeModel(["numeric__age", "numeric__device_risk_score"]))

    analysis = engine.explain(
        _frame(),
        sensitive_feature="synthetic_demographic_group",
        primary_group="group_c",
        sample_size=4,
        random_seed=7,
        top_k=2,
        local_examples=1,
    )

    assert analysis.global_importance["feature"].tolist() == ["age", "device_risk_score"]
    assert set(analysis.group_importance["group"]) == {"group_a", "group_c"}
    assert set(analysis.group_delta["group"]) == {"group_c"}
    assert analysis.summary["protected_attributes_present_in_model_feature_space"] is False
    assert len(analysis.summary["local_examples"]) == 1


def test_explain_rejects_protected_feature_leakage() -> None:
    engine = ShapEngine(FakeModel(["numeric__age", "categorical__sex_female"]))

    with pytest.raises(RuntimeError, match="Protected attributes reached SHAP feature space"):
        engine.explain(
            _frame(),
            sensitive_feature="synthetic_demographic_group",
            primary_group="group_c",
            sample_size=4,
            random_seed=7,
            top_k=2,
            local_examples=1,
        )


def test_values_reject_unexpected_shape() -> None:
    class BadExplainer:
        def __call__(self, matrix: np.ndarray) -> SimpleNamespace:
            return SimpleNamespace(values=np.zeros(len(matrix), dtype=float))

    with pytest.raises(ValueError, match="Unexpected SHAP value shape"):
        ShapEngine._values(BadExplainer(), np.zeros((3, 2), dtype=float))
