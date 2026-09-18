from creditscore.data.preprocessing import MODEL_INPUT_FEATURES, PROTECTED_EVALUATION_COLUMNS


def test_protected_attributes_are_not_model_features():
    assert not set(PROTECTED_EVALUATION_COLUMNS).intersection(MODEL_INPUT_FEATURES)


def test_target_and_identifier_are_not_model_features():
    assert "default_30d" not in MODEL_INPUT_FEATURES
    assert "application_id" not in MODEL_INPUT_FEATURES
