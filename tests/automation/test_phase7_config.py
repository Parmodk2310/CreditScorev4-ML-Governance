from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase7_config_version_and_default_region() -> None:
    config = yaml.safe_load((ROOT / "configs/phase7.yaml").read_text())
    assert config["phase"] == 7
    assert config["version"] == "0.7.0"
    assert config["aws"]["default_region"] == "ap-south-1"


def test_phase7_config_requires_blocking_security() -> None:
    config = yaml.safe_load((ROOT / "configs/phase7.yaml").read_text())
    assert config["security"]["gitleaks"] is True
    assert config["security"]["blocking_severities"] == ["HIGH", "CRITICAL"]
