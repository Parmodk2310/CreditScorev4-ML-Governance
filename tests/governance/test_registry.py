import pytest

from creditscore.governance.registry import ModelRegistry, RegistryTransitionError


def test_registry_enforces_phase5_state_machine(tmp_path):
    registry = ModelRegistry(tmp_path / "registry.json")
    record = registry.register(
        model_name="CreditScoreV4",
        version="test",
        artifact_path="model.joblib",
        artifact_sha256="abc",
    )
    assert record.stage == "REGISTERED"
    candidate = registry.transition(
        model_name="CreditScoreV4",
        version="test",
        target_stage="CANDIDATE",
    )
    assert candidate.stage == "CANDIDATE"
    with pytest.raises(RegistryTransitionError):
        registry.transition(
            model_name="CreditScoreV4",
            version="test",
            target_stage="PRODUCTION",
        )
