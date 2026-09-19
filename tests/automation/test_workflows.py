from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def workflow(name: str) -> str:
    return (ROOT / ".github/workflows" / name).read_text()


def test_ci_reuses_existing_release_gate_and_validates_terraform() -> None:
    text = workflow("ci.yml")
    assert "make phase7-verify" in text
    assert "terraform validate" in text


def test_security_uses_gitleaks_and_trivy() -> None:
    text = workflow("security.yml")
    assert "gitleaks/gitleaks-action@v3" in text
    assert text.count("aquasecurity/trivy-action@v0.36.0") == 2


def test_image_workflow_builds_without_push_and_smoke_tests() -> None:
    text = workflow("image.yml")
    assert "push: false" in text
    assert "verify_container.py" in text


def test_deploy_workflow_requires_oidc_and_explicit_gate() -> None:
    text = workflow("deploy.yml")
    assert "id-token: write" in text
    assert "AWS_DEPLOY_ENABLED" in text
    assert "confirm_deploy" in text
    assert "configure-aws-credentials@v6" in text


def test_cloud_image_contains_generated_model_artifact() -> None:
    dockerfile = (ROOT / "docker/phase6/Dockerfile").read_text()
    assert "COPY models/baseline/creditscorev4.joblib" in dockerfile


def test_security_workflow_can_read_pull_request_metadata() -> None:
    text = workflow("security.yml")
    assert "pull-requests: read" in text
