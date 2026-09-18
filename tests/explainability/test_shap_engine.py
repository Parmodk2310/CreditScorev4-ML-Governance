from __future__ import annotations

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES, PROTECTED_EVALUATION_COLUMNS


def test_protected_evaluation_columns_are_not_model_inputs() -> None:
    assert all(column not in MODEL_INPUT_FEATURES for column in PROTECTED_EVALUATION_COLUMNS)
