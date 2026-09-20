import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_release_verify_wraps_phase13_boundary() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    deploy = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "make release-verify" in ci
    assert "make release-verify" in deploy
    assert "make phase13-verify" not in ci
    assert "make phase13-verify" not in deploy

    release_target = makefile.split("release-verify:", 1)[1].split("\n\n", 1)[0]
    phase13_target = makefile.split("phase13-verify:", 1)[1].split("\n\n", 1)[0]

    assert "$(MAKE) phase13-verify" in release_target
    assert "$(MAKE) phase12-verify" in phase13_target


def test_release_metadata_and_phase13_history_contract() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    config = yaml.safe_load((ROOT / "configs/phase13.yaml").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    current_version = str(project["version"])

    assert f"## v{current_version} " in changelog
    assert config["target_release"] == "0.13.0"


def test_phase13_is_in_current_scheduled_monitoring_path() -> None:
    workflow_path = ROOT / ".github/workflows/monitoring.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    payload = yaml.safe_load(workflow)

    assert "make phase11-run" in workflow
    assert "python scripts/verify_phase11.py" in workflow
    assert "make phase12-analyze" in workflow
    assert "python scripts/verify_phase12.py" in workflow
    assert "make phase13-analyze" in workflow
    assert "python scripts/verify_phase13.py" in workflow
    assert "contents: read" in workflow

    steps = payload["jobs"]["monitor"]["steps"]

    phase13_uploads = [
        step
        for step in steps
        if isinstance(step, dict)
        and isinstance(step.get("with"), dict)
        and step["with"].get("name") == "phase13-incident-ops-evidence"
    ]

    assert len(phase13_uploads) == 1
    assert phase13_uploads[0]["with"]["path"] == "data/evidence/phase13"
    assert phase13_uploads[0]["if"] == "always()"


def test_phase13_preserves_phase12_historical_release_contract() -> None:
    phase12 = yaml.safe_load((ROOT / "configs/phase12.yaml").read_text(encoding="utf-8"))
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert phase12["target_release"] == "0.12.0"
    phase12_target = makefile.split("phase12-verify:", 1)[1].split("\n\n", 1)[0]
    assert "$(MAKE) phase11-verify" in phase12_target
