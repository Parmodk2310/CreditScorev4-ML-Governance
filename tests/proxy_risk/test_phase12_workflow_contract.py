import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase12_is_current_cumulative_workflow_gate() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    deploy = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "make phase12-verify" in ci
    assert "make phase12-verify" in deploy
    assert "make phase11-verify" not in ci
    assert "make phase11-verify" not in deploy

    phase12_target = makefile.split("phase12-verify:", 1)[1].split("\n\n", 1)[0]
    assert "$(MAKE) phase11-verify" in phase12_target


def test_phase12_release_version_contract() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    config = yaml.safe_load((ROOT / "configs/phase12.yaml").read_text(encoding="utf-8"))

    assert project["version"] == "0.12.0"
    assert config["target_release"] == "0.12.0"


def test_phase12_is_in_current_scheduled_monitoring_path() -> None:
    workflow = (ROOT / ".github/workflows/monitoring.yml").read_text(encoding="utf-8")

    assert "make phase11-run" in workflow
    assert "python scripts/verify_phase11.py" in workflow
    assert "make phase12-analyze" in workflow
    assert "python scripts/verify_phase12.py" in workflow
    assert "phase12-fairness-proxy-evidence" in workflow
    assert "data/evidence/phase12" in workflow
    assert "contents: read" in workflow


def test_phase12_preserves_historical_fairness_regression_boundary() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "PHASE4_FAIRNESS_TESTS :=" in makefile
    assert "tests/fairness/test_expanded_fairness.py" not in makefile.split(
        "phase7-verify:", 1
    )[1].split("\n\n", 1)[0]
