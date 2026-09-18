# CreditScoreV4 ML Governance Manifest — Through Phase 6

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

- configurable evidence-driven promotion policy
- performance, calibration, drift, fairness, and integrity gates
- model registry and append-only audit trail
- deterministic APPROVE/REJECT decisions
- healthy candidate promoted to STAGING; Vendor C/D rejected for different gates

## Phase 6 — serving, safe release, observability, rollback

- `configs/phase6.yaml` — serving, shadow/canary, release gates, acceptance settings
- `src/creditscore/serving/` — FastAPI schemas, predictor, health, and Prometheus metrics
- `src/creditscore/release/` — deterministic routing, health gates, rollout controller, rollback
- Phase 5 registry extended with `STAGING -> SHADOW -> CANARY -> PRODUCTION`
- rollback paths from SHADOW/CANARY to STAGING
- `scripts/serve_model.py` — local FastAPI server
- `scripts/run_shadow.py` / `run_canary.py` — staged rollout demonstrations
- `scripts/simulate_rollback.py` — degraded canary rollback demonstration
- `scripts/verify_phase6.py` — API + rollout + rollback release gate
- `tests/serving/` and `tests/release/` — serving and safe-release unit tests
- `tests/integration/test_phase6_safe_release_pipeline.py` — end-to-end lifecycle integration test
- `docker/phase6/` — API, Prometheus, and Grafana local stack
- generated Phase 6 evidence/state/audit files remain ignored except `.gitkeep`

Phase 7 will add workflow automation, CI/CD deployment, and cloud infrastructure.
