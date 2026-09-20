from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase11_monitoring_workflow_matches_schedule_contract() -> None:
    config = yaml.safe_load((ROOT / "configs/phase11.yaml").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows/monitoring.yml").read_text(encoding="utf-8")

    assert str(config["scheduler"]["cron_utc"]) in workflow
    assert "make phase11-run" in workflow
    assert "contents: read" in workflow
    assert "phase11-monitoring-evidence" in workflow
    assert "data/evidence/phase11" in workflow
    assert "workflow_dispatch" in workflow


def test_phase11_does_not_enable_automatic_retraining_or_promotion() -> None:
    config = yaml.safe_load((ROOT / "configs/phase11.yaml").read_text(encoding="utf-8"))

    assert config["orchestration"]["fail_closed"] is True
    assert config["orchestration"]["automatic_retraining"] is False
    assert config["orchestration"]["automatic_promotion"] is False
