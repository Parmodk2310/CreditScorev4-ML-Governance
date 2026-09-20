from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase10_remains_historical_cumulative_boundary() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    phase10_target = makefile.split("phase10-verify:", 1)[1].split("\n\n", 1)[0]
    phase11_target = makefile.split("phase11-verify:", 1)[1].split("\n\n", 1)[0]

    assert "$(MAKE) phase9-verify" in phase10_target
    assert "$(MAKE) phase10-verify" in phase11_target


def test_phase10_release_contract_remains_frozen() -> None:
    phase10 = (ROOT / "configs/phase10.yaml").read_text(encoding="utf-8")

    assert 'target_release: "0.10.0"' in phase10
