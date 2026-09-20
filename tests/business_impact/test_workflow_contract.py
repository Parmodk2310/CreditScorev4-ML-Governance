from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase9_is_current_cumulative_workflow_gate() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    deploy = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "make phase9-verify" in ci
    assert "make phase9-verify" in deploy

    assert "make phase8-verify" not in ci
    assert "make phase8-verify" not in deploy

    phase9_target = makefile.split("phase9-verify:", 1)[1].split("\n\n", 1)[0]

    assert "$(MAKE) phase8-verify" in phase9_target
