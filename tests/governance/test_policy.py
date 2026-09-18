from creditscore.governance.policy import GovernancePolicy


def test_policy_loads_configured_gate_thresholds():
    policy = GovernancePolicy.from_config(
        {
            "policy": {
                "name": "test_policy",
                "version": "1",
                "requested_stage": "STAGING",
                "gates": {"performance": {"minimum_roc_auc": 0.75}},
            }
        }
    )
    assert policy.name == "test_policy"
    assert policy.requested_stage == "STAGING"
    assert policy.gate("performance")["minimum_roc_auc"] == 0.75
