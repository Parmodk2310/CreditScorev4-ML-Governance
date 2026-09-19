# Phase 8 — Governance Evidence & Traceability

## Objective

Phase 8 turns the verified Phase 1–7 implementation into a reviewer-ready,
evidence-driven ML governance case study.

It does not add another ML platform, orchestration framework, or cloud stack.
Instead, it makes existing implementation claims easier to verify, reproduce,
explain, and trace.

> Every important public claim should be traceable to executable
> configuration, source code, tests, or generated evidence.

## Existing baseline

Phase 8 builds on:

1. deterministic incident reproduction,
2. data-quality governance,
3. PSI/KS drift governance,
4. fairness and SHAP investigation,
5. evidence-backed promotion policy and registry,
6. FastAPI serving plus shadow/canary/rollback,
7. CI, security scanning, Docker, Terraform, and gated AWS ECS/Fargate delivery.

## Documentation paths

### Overview

`README -> 60-second story -> architecture -> evidence -> outcomes -> case study`

### Senior ML / MLOps engineer

`README -> ARCHITECTURE -> TECHNICAL_DEEP_DIVE -> GOVERNANCE_POLICY -> source -> tests -> REPRODUCIBLE_DEMO`

### Governance review

`MODEL_CARD -> MODEL_VALIDATION_REPORT -> GOVERNANCE_POLICY -> MONITORING_PLAN -> EVIDENCE_INDEX -> LIMITATIONS`

## Phase 8 deliverables

Governance documentation:

- `docs/GOVERNANCE_POLICY.md`
- `docs/MODEL_CARD.md`
- `docs/MODEL_VALIDATION_REPORT.md`
- `docs/MONITORING_PLAN.md`
- `docs/LIMITATIONS.md`

Governance documentation:

- `docs/EVIDENCE_INDEX.md`
- `docs/TECHNICAL_DEEP_DIVE.md`
- `docs/REPRODUCIBLE_DEMO.md`

Executable verification:

- `configs/phase8.yaml`
- `scripts/verify_phase8.py`
- `tests/evidence/test_phase8_evidence_contract.py`
- `data/evidence/phase8/.gitkeep`

## Governance contract

Phase 8 documents, but does not redefine, the Phase 5 promotion policy.

Current project guardrails:

- data-quality result must be `PASS`,
- ROC-AUC must be at least `0.75`,
- PR-AUC must be at least `0.60`,
- Brier score must be at most `0.20`,
- `CRITICAL` drift blocks promotion,
- fairness `FAIL` blocks promotion,
- at least 6 evidence artifacts are required,
- evidence integrity is verified.

These are project engineering heuristics for a synthetic case study, not
regulatory thresholds.

## Scenario contract

- Vendor A: healthy reference.
- Vendor B: data quality `BLOCK`.
- Vendor C: data quality `PASS`, drift `CRITICAL`, governance `REJECT`.
- Vendor D: data quality `PASS`, aggregate drift `STABLE`, fairness `FAIL`, governance `REJECT`.
- Healthy candidate: `REGISTERED -> CANDIDATE -> STAGING`, then `STAGING -> SHADOW -> CANARY -> PRODUCTION`.
- Degraded release: `CANARY -> STAGING` with a recorded rollback reason.

## Release contract

Phase 6 owns runtime release safety.

Canary shares: `10% -> 25% -> 50% -> 100%`.

Shadow project guardrails:

- error rate <= `0.02`,
- p95 latency <= `250 ms`,
- mean risk delta <= `0.05`,
- minimum request count >= `50`.

Canary project guardrails:

- error rate <= `0.03`,
- p95 latency <= `300 ms`,
- mean risk delta <= `0.06`,
- minimum request count >= `100`.

## Delivery contract

Phase 7 uses GitHub Actions, Docker, Gitleaks, Trivy, Terraform, ECR,
ECS/Fargate, and an ALB deployment path.

AWS mutation remains fail-closed by default: `AWS_DEPLOY_ENABLED=false`.

## Phase 8 verifier

`python scripts/verify_phase8.py` validates required Phase 8 docs/visuals,
Phase 5 policy consistency, registry transition safety, Phase 6 release
configuration, Phase 7 fail-closed deployment behavior, generated Phase 1–7
evidence, expected governance decisions, production promotion, rollback, and the
reviewer evidence manifest.

The verifier returns non-zero when a blocking evidence contract fails.

## Non-goals

Phase 8 intentionally does not add Airflow, MLflow, Kafka, Kubernetes/EKS, RDS,
a feature store, another model, or another dashboard without a verified
operational requirement.

## Acceptance criteria

Phase 8 is complete only when documentation matches executable configuration,
the reviewer evidence manifest is generated programmatically, Phase 8 tests and
the cumulative Phase 1–7 regression boundary pass, quality checks pass,
`git diff --check` passes, historical root-level package artifacts are cleaned,
README contains only implemented claims, and PR checks pass.

## Release procedure

The v0.8.0 release followed this sequence:

implementation
-> Phase 8 verification
-> cumulative verification
-> quality
-> PR checks
-> merge
-> verify main
-> tag/release

Future releases must follow the same verification-first sequence.

Release sequence:

`implementation -> phase8 verify -> cumulative verify -> quality -> PR checks -> merge -> verify main -> tag/release`
