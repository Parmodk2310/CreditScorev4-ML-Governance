import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase7_verifier_passes_with_deployment_disabled(monkeypatch) -> None:
    monkeypatch.delenv("AWS_DEPLOY_ENABLED", raising=False)
    result = subprocess.run(
        [sys.executable, "scripts/verify_phase7.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PHASE 7: VERIFIED" in result.stdout
