from scripts.write_release_manifest import build_manifest


def test_release_manifest_is_traceable_and_fail_closed() -> None:
    manifest = build_manifest("sha256:test", False)
    assert manifest["application_version"] == "0.7.0"
    assert manifest["image_digest"] == "sha256:test"
    assert manifest["governance_gate"] == "PASS"
    assert manifest["phase6_release_gate"] == "PASS"
    assert manifest["deployment_enabled"] is False
