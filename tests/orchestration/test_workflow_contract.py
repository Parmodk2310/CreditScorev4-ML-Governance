import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase11_is_current_cumulative_workflow_gate() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    deploy = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "make phase11-verify" in ci
    assert "make phase11-verify" in deploy
    assert "make phase10-verify" not in ci
    assert "make phase10-verify" not in deploy

    phase11_target = makefile.split("phase11-verify:", 1)[1].split("\n\n", 1)[0]
    assert "$(MAKE) phase10-verify" in phase11_target


def test_phase11_monitoring_workflow_matches_schedule_contract() -> None:
    config = yaml.safe_load((ROOT / "configs/phase11.yaml").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows/monitoring.yml").read_text(encoding="utf-8")

    assert str(config["scheduler"]["cron_utc"]) in workflow
    assert "make phase11-run" in workflow
    assert "python scripts/verify_phase11.py" in workflow
    assert "contents: read" in workflow
    assert "phase11-monitoring-evidence" in workflow
    assert "data/evidence/phase11" in workflow
    assert "workflow_dispatch" in workflow


def test_phase11_release_version_and_safety_contract() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    config = yaml.safe_load((ROOT / "configs/phase11.yaml").read_text(encoding="utf-8"))

    assert project["version"] == "0.11.0"
    assert config["target_release"] == "0.11.0"
    assert config["orchestration"]["fail_closed"] is True
    assert config["orchestration"]["automatic_retraining"] is False
    assert config["orchestration"]["automatic_promotion"] is False
