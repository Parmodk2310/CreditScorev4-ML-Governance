from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase12_remains_historical_cumulative_boundary() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    phase12_target = makefile.split("phase12-verify:", 1)[1].split("\n\n", 1)[0]
    phase13_target = makefile.split("phase13-verify:", 1)[1].split("\n\n", 1)[0]

    assert "$(MAKE) phase11-verify" in phase12_target
    assert "$(MAKE) phase12-verify" in phase13_target


def test_phase12_release_contract_remains_frozen() -> None:
    config = yaml.safe_load((ROOT / "configs/phase12.yaml").read_text(encoding="utf-8"))
    assert config["target_release"] == "0.12.0"


def test_phase12_remains_in_scheduled_monitoring_path() -> None:
    workflow = (ROOT / ".github/workflows/monitoring.yml").read_text(encoding="utf-8")

    assert "make phase12-analyze" in workflow
    assert "python scripts/verify_phase12.py" in workflow
    assert "phase12-fairness-proxy-evidence" in workflow
    assert "data/evidence/phase12" in workflow


def test_phase12_preserves_historical_fairness_regression_boundary() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "PHASE4_FAIRNESS_TESTS :=" in makefile
    assert (
        "tests/fairness/test_expanded_fairness.py"
        not in makefile.split("phase7-verify:", 1)[1].split("\n\n", 1)[0]
    )
