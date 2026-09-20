from __future__ import annotations

from pathlib import Path

from creditscore.governance.registry import ALLOWED_TRANSITIONS
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase8_required_document_and_visual_contract() -> None:
    config = load_yaml(ROOT / "configs" / "phase8.yaml")

    for relative in config["documents"]["required"]:
        assert (ROOT / str(relative)).exists(), relative

    for relative in config["visuals"]["required"]:
        assert (ROOT / str(relative)).exists(), relative


def test_phase8_policy_contract_matches_phase5() -> None:
    phase8 = load_yaml(ROOT / "configs" / "phase8.yaml")
    phase5 = load_yaml(ROOT / "configs" / "phase5.yaml")

    expected = phase8["policy_contract"]
    actual = phase5["policy"]["gates"]

    assert float(actual["performance"]["minimum_roc_auc"]) == float(expected["minimum_roc_auc"])
    assert float(actual["performance"]["minimum_pr_auc"]) == float(expected["minimum_pr_auc"])
    assert float(actual["calibration"]["maximum_brier_score"]) == float(expected["maximum_brier_score"])
    assert str(expected["blocked_drift_status"]) in actual["drift"]["blocked_statuses"]
    assert str(expected["blocked_fairness_status"]) in actual["fairness"]["blocked_statuses"]
    assert int(actual["evidence_integrity"]["minimum_artifacts"]) == int(expected["minimum_artifacts"])


def test_phase8_registry_state_contract() -> None:
    assert ALLOWED_TRANSITIONS["REGISTERED"] == {"CANDIDATE"}
    assert ALLOWED_TRANSITIONS["CANDIDATE"] == {"STAGING", "REJECTED"}
    assert "PRODUCTION" not in ALLOWED_TRANSITIONS["CANDIDATE"]
    assert ALLOWED_TRANSITIONS["STAGING"] == {"SHADOW"}
    assert ALLOWED_TRANSITIONS["SHADOW"] == {"CANARY", "STAGING"}
    assert ALLOWED_TRANSITIONS["CANARY"] == {"PRODUCTION", "STAGING"}
    assert ALLOWED_TRANSITIONS["PRODUCTION"] == set()
    assert ALLOWED_TRANSITIONS["REJECTED"] == set()


def test_phase8_release_contract_matches_phase6() -> None:
    phase8 = load_yaml(ROOT / "configs" / "phase8.yaml")
    phase6 = load_yaml(ROOT / "configs" / "phase6.yaml")

    expected = phase8["release_contract"]
    actual = phase6["release"]

    assert [float(v) for v in actual["canary_shares"]] == [float(v) for v in expected["canary_shares"]]

    for stage in ("shadow", "canary"):
        for field in (
            "maximum_error_rate",
            "maximum_p95_latency_ms",
            "maximum_mean_risk_delta",
            "minimum_request_count",
        ):
            assert float(actual["gates"][stage][field]) == float(expected[stage][field])


def test_phase8_deployment_contract_matches_phase7() -> None:
    phase8 = load_yaml(ROOT / "configs" / "phase8.yaml")
    phase7 = load_yaml(ROOT / "configs" / "phase7.yaml")

    assert phase8["deployment_contract"]["safe_default"] is False
    assert str(phase7["aws"]["deploy_enabled_env"]) == str(phase8["deployment_contract"]["enable_env"])

    ci_workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    deploy_workflow = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")

    assert any(
        gate in ci_workflow
        for gate in (
            "make phase8-verify",
            "make phase9-verify",
            "make phase10-verify",
            "make phase11-verify",
            "make phase12-verify",
            "make phase13-verify",
            "make release-verify",
        )
    )
    assert any(
        gate in deploy_workflow
        for gate in (
            "make phase8-verify",
            "make phase9-verify",
            "make phase10-verify",
            "make phase11-verify",
            "make phase12-verify",
            "make phase13-verify",
            "make release-verify",
        )
    )
    assert "make phase7-verify" not in ci_workflow
    assert "make phase7-verify" not in deploy_workflow


def test_phase8_reviewer_manifest_path_is_phase8_scoped() -> None:
    config = load_yaml(ROOT / "configs" / "phase8.yaml")
    path = str(config["evidence"]["reviewer_manifest"])
    assert path == "data/evidence/phase8/reviewer_evidence_manifest.json"
