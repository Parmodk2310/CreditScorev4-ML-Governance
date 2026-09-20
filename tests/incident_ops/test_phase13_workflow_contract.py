import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase13_is_current_cumulative_workflow_gate() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    deploy = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "make phase13-verify" in ci
    assert "make phase13-verify" in deploy
    assert "make phase12-verify" not in ci
    assert "make phase12-verify" not in deploy

    phase13_target = makefile.split("phase13-verify:", 1)[1].split("\n\n", 1)[0]
    assert "$(MAKE) phase12-verify" in phase13_target


def test_phase13_release_version_contract() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    config = yaml.safe_load((ROOT / "configs/phase13.yaml").read_text(encoding="utf-8"))

    assert project["version"] == "0.13.0"
    assert config["target_release"] == "0.13.0"


def test_phase13_is_in_current_scheduled_monitoring_path() -> None:
    workflow = (ROOT / ".github/workflows/monitoring.yml").read_text(encoding="utf-8")

    assert "make phase11-run" in workflow
    assert "python scripts/verify_phase11.py" in workflow
    assert "make phase12-analyze" in workflow
    assert "python scripts/verify_phase12.py" in workflow
    assert "make phase13-analyze" in workflow
    assert "python scripts/verify_phase13.py" in workflow
    assert "phase13-incident-ops-evidence" in workflow
    assert "data/evidence/phase13" in workflow
    assert "contents: read" in workflow


def test_phase13_preserves_phase12_historical_release_contract() -> None:
    phase12 = yaml.safe_load((ROOT / "configs/phase12.yaml").read_text(encoding="utf-8"))
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert phase12["target_release"] == "0.12.0"
    phase12_target = makefile.split("phase12-verify:", 1)[1].split("\n\n", 1)[0]
    assert "$(MAKE) phase11-verify" in phase12_target
