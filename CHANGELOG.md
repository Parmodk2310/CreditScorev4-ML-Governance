# Changelog

All notable portfolio releases of CreditScoreV4 ML Governance are documented here.

The project uses phased releases to demonstrate the evolution from incident reproduction to governed model delivery.

<!-- PHASE8_CHANGELOG -->
## v0.8.0 — Governance Evidence & Reviewer Experience

- Added reviewer-specific navigation and evidence traceability.
- Enforced cumulative Phase 8 verification in CI and the gated deployment preflight.
- Removed stale Airflow/MLflow/MinIO platform scaffolding that was not part of the verified implementation.
- Reduced `env.example` to the actual fail-closed AWS deployment contract.
- Added governance policy documentation tied to executable Phase 5 thresholds.
- Added a model card, validation report, monitoring plan, and limitations.
- Added technical design-decision documentation and a reproducible demo.
- Added a Phase 8 evidence contract and reviewer evidence manifest.
- Added focused tests for policy, registry, release, documentation, and deployment contracts.
- Removed/moved historical implementation-package material from the repository root.
- Kept Phase 1–7 runtime behavior unchanged.

## v0.7.0 — Automated Delivery and Gated Cloud Deployment

- Added GitHub Actions quality and cumulative verification.
- Added Docker image build and runtime smoke testing.
- Added Gitleaks secret scanning.
- Added Trivy filesystem and Terraform security scanning.
- Added Terraform-managed AWS ECS/Fargate deployment architecture.
- Added immutable ECR configuration.
- Added HTTPS Application Load Balancer configuration.
- Added GitHub OIDC deployment authentication path.
- Added fail-closed cloud deployment controls.
- Retired the superseded legacy ML pipeline.
- Verified 63 cumulative tests.

## v0.6.0 — Governed Serving and Safe Release

- Added FastAPI model serving.
- Added health, readiness, prediction, model, batch and metrics endpoints.
- Extended the registry lifecycle through SHADOW, CANARY and PRODUCTION.
- Added progressive canary checkpoints.
- Added runtime release gates.
- Added deterministic rollback to STAGING.

## v0.5.0 — Model Governance and Registry

- Added project governance policy engine.
- Added evidence integrity verification.
- Added deterministic governance decisions.
- Added audit records.
- Added model registry state transitions.
- Added fail-closed promotion behavior.
- Demonstrated drift- and fairness-based rejection.

## v0.4.0 — Fairness and Explainability

- Added Fairlearn subgroup metrics.
- Added SHAP explanation evidence.
- Added deterministic Vendor D subgroup stress.
- Demonstrated aggregate-stable but subgroup-sensitive failure detection.
- Kept evaluation-only demographic attributes outside model inputs.

## v0.3.0 — Drift Governance

- Added deterministic Vendor C contract-valid distribution shift.
- Added feature PSI.
- Added two-sample KS analysis.
- Added prediction-distribution drift.
- Added STABLE, WARNING and CRITICAL governance states.

## v0.2.0 — Data-Quality Governance

- Added versioned data contracts.
- Added custom validation.
- Added Great Expectations validation.
- Added PASS/BLOCK decision logic.
- Added quarantine handling.
- Added machine-readable quality evidence.

## v0.1.0 — Incident Baseline

- Added deterministic synthetic lending data.
- Added baseline credit-risk model.
- Added Vendor B migration incident simulation.
- Demonstrated ROC-AUC degradation from 0.8025 to 0.7329.
- Demonstrated device-risk missingness increase from 3.14% to 22%.
