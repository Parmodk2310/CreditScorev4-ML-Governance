import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase11_remains_historical_cumulative_boundary() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    phase11_target = makefile.split("phase11-verify:", 1)[1].split("\n\n", 1)[0]
    phase12_target = makefile.split("phase12-verify:", 1)[1].split("\n\n", 1)[0]

    assert "$(MAKE) phase10-verify" in phase11_target
    assert "$(MAKE) phase11-verify" in phase12_target


def test_phase11_monitoring_workflow_contract_remains_present() -> None:
    config = yaml.safe_load((ROOT / "configs/phase11.yaml").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows/monitoring.yml").read_text(encoding="utf-8")

    assert str(config["scheduler"]["cron_utc"]) in workflow
    assert "make phase11-run" in workflow
    assert "python scripts/verify_phase11.py" in workflow
    assert "contents: read" in workflow
    assert "phase11-monitoring-evidence" in workflow
    assert "data/evidence/phase11" in workflow
    assert "workflow_dispatch" in workflow

    uses_lines = [
        line.strip().split("uses:", 1)[1].split("#", 1)[0].strip()
        for line in workflow.splitlines()
        if line.strip().startswith("- uses:")
    ]
    assert uses_lines
    for value in uses_lines:
        action, ref = value.rsplit("@", 1)
        assert action
        assert len(ref) == 40
        assert all(character in "0123456789abcdef" for character in ref)


def test_phase11_release_contract_remains_frozen() -> None:
    config = yaml.safe_load((ROOT / "configs/phase11.yaml").read_text(encoding="utf-8"))

    assert config["target_release"] == "0.11.0"
    assert config["orchestration"]["fail_closed"] is True
    assert config["orchestration"]["automatic_retraining"] is False
    assert config["orchestration"]["automatic_promotion"] is False
