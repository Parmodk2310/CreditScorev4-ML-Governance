# CreditScoreV4 ML Governance Manifest — Through Phase 5

## Phase 1 — incident and baseline

- deterministic synthetic lending data
- CreditScoreV4 XGBoost baseline
- Vendor B upstream migration simulation
- same-model incident evidence and regression tests

## Phase 2 — blocking data-quality governance

- versioned scoring data contract
- custom validator + Great Expectations
- blocking quality gate, quarantine, evidence hashes
- exact Phase 1 Vendor B fixture continuity

## Phase 3 — statistical drift governance

- contract-valid Vendor C drift fixture
- PSI + two-sample KS monitoring
- prediction-distribution drift
- reference profile and machine-readable evidence

## Phase 4 — fairness and explainability

- aggregate-stable Vendor D subgroup proxy stress
- Fairlearn subgroup metrics and governance evidence
- SHAP global/group/local explanation evidence
- evaluation-only demographic attributes excluded from the model feature space

## Phase 5 — promotion governance and model registry

- `configs/phase5.yaml` — promotion policy, thresholds, registry lifecycle, scenario versions
- `src/creditscore/governance/` — evidence normalization/hashing, policy gates, evaluator, registry, audit, decisions
- `scripts/register_model.py` — register and move a version into CANDIDATE
- `scripts/evaluate_governance.py` — policy evaluation without final promotion
- `scripts/promote_model.py` — apply APPROVE/REJECT registry transition
- `scripts/show_registry.py` — inspect registry state
- `scripts/verify_phase5.py` — healthy/Vendor C/Vendor D acceptance gate
- `tests/governance/` — policy, gate, evaluator, registry, and audit tests
- `tests/integration/test_phase5_governance_pipeline.py` — one-policy approve/reject integration test
- `docs/PHASE5.md` — methodology, registry state machine, decision semantics, and limitations
- generated Phase 5 evidence, registry, audit, decision, and quarantine artifacts remain ignored except `.gitkeep`

Phase 6 will add serving, shadow/canary rollout, runtime observability, and rollback. Phase 7 will add workflow automation and cloud deployment.
