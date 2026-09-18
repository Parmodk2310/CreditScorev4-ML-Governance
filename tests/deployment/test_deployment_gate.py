from scripts.check_deployment_gate import evaluate_gate


def test_deployment_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("AWS_DEPLOY_ENABLED", raising=False)
    enabled, reasons = evaluate_gate()
    assert enabled is False
    assert reasons


def test_enabled_deployment_requires_all_inputs(monkeypatch) -> None:
    monkeypatch.setenv("AWS_DEPLOY_ENABLED", "true")
    for name in ("AWS_ROLE_TO_ASSUME", "AWS_REGION", "TF_STATE_BUCKET", "TF_STATE_KEY"):
        monkeypatch.delenv(name, raising=False)
    enabled, reasons = evaluate_gate()
    assert enabled is False
    assert "AWS_ROLE_TO_ASSUME" in reasons
