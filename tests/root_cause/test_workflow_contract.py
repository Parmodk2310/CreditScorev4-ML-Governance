import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase10_is_current_cumulative_workflow_gate() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    deploy = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "make phase10-verify" in ci
    assert "make phase10-verify" in deploy
    assert "make phase9-verify" not in ci
    assert "make phase9-verify" not in deploy

    phase10_target = makefile.split("phase10-verify:", 1)[1].split("\n\n", 1)[0]
    assert "$(MAKE) phase9-verify" in phase10_target


def test_phase10_release_version_matches_config() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    phase10 = (ROOT / "configs/phase10.yaml").read_text(encoding="utf-8")

    assert project["version"] == "0.10.0"
    assert 'target_release: "0.10.0"' in phase10
