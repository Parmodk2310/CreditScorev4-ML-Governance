import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def workflow(name: str) -> str:
    return (ROOT / ".github/workflows" / name).read_text()


def assert_actions_pinned(text: str) -> None:
    refs: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()

        if not stripped.startswith("- uses:"):
            continue

        value = stripped.split("uses:", 1)[1].split("#", 1)[0].strip()

        assert "@" in value, value

        action, ref = value.rsplit("@", 1)

        assert action, value
        assert SHA_PATTERN.fullmatch(ref), f"Action is not SHA-pinned: {value}"

        refs.append(ref)

    assert refs, "Expected at least one external GitHub Action"


def test_ci_runs_quality_and_validates_terraform() -> None:
    text = workflow("ci.yml")

    assert "make quality" in text
    assert "terraform validate" in text

    assert_actions_pinned(text)


def test_security_uses_gitleaks_and_trivy() -> None:
    text = workflow("security.yml")

    assert "gitleaks/gitleaks-action@" in text
    assert text.count("aquasecurity/trivy-action@") == 2

    assert_actions_pinned(text)


def test_image_workflow_builds_without_push_and_smoke_tests() -> None:
    text = workflow("image.yml")

    assert "push: false" in text
    assert "verify_container.py" in text

    assert_actions_pinned(text)


def test_deploy_workflow_requires_oidc_and_explicit_gate() -> None:
    text = workflow("deploy.yml")

    assert "AWS_DEPLOY_ENABLED" in text
    assert "confirm_deploy" in text
    assert "aws-actions/configure-aws-credentials@" in text

    assert_actions_pinned(text)


def test_deploy_workflow_scopes_oidc_and_serializes_production() -> None:
    text = workflow("deploy.yml")

    assert "concurrency:" in text
    assert "group: creditscorev4-production" in text
    assert "cancel-in-progress: false" in text

    workflow_header = text.split("jobs:", 1)[0]

    assert "permissions:" in workflow_header
    assert "contents: read" in workflow_header
    assert "id-token: write" not in workflow_header

    jobs_section = text.split("jobs:", 1)[1]

    gate_section, deploy_section = jobs_section.split("  deploy:", 1)

    assert "id-token: write" not in gate_section

    assert "permissions:" in deploy_section
    assert "contents: read" in deploy_section
    assert "id-token: write" in deploy_section


def test_cloud_image_contains_generated_model_artifact() -> None:
    dockerfile = (ROOT / "docker/phase6/Dockerfile").read_text()

    assert "COPY models/baseline/creditscorev4.joblib" in dockerfile


def test_security_workflow_can_read_pull_request_metadata() -> None:
    text = workflow("security.yml")

    assert "pull-requests: read" in text
