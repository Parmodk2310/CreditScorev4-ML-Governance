from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase9_remains_historical_cumulative_boundary() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    phase9_target = makefile.split("phase9-verify:", 1)[1].split("\n\n", 1)[0]
    phase10_target = makefile.split("phase10-verify:", 1)[1].split("\n\n", 1)[0]

    assert "$(MAKE) phase8-verify" in phase9_target
    assert "$(MAKE) phase9-verify" in phase10_target
