import tomllib
from pathlib import Path

from scripts.write_release_manifest import build_manifest

ROOT = Path(__file__).resolve().parents[2]


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        payload = tomllib.load(handle)

    return str(payload["project"]["version"])


def test_release_manifest_is_traceable_and_fail_closed() -> None:
    manifest = build_manifest("sha256:test", False)

    assert manifest["application_version"] == project_version()
    assert manifest["image_digest"] == "sha256:test"
    assert manifest["governance_gate"] == "PASS"
    assert manifest["phase6_release_gate"] == "PASS"
    assert manifest["deployment_enabled"] is False
