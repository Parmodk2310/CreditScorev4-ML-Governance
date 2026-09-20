# Changelog

All notable releases of CreditScoreV4 ML Governance are documented here.

The project uses phased releases to demonstrate the evolution from incident reproduction to governed model delivery.

<!-- PHASE9_CHANGELOG -->
## v0.9.0 — Business Impact & Incident Outcome Evidence

- Added deterministic business-impact analysis for the Vendor B incident.
- Preserved the same 15,000-applicant population and identical `default_30d`
  labels across healthy and incident scenarios.
- Measured approval-rate inflation from 73.91% to 78.60% (+4.69 percentage
  points).
- Measured approved-cohort 30-day default increase from 21.80% to 26.37%
  (+4.57 percentage points).
- Measured 2,500 decision flips across the 15,000-applicant holdout.
- Identified 1,602 newly approved applicants and 898 newly rejected applicants.
- Measured a 61.99% observed 30-day default rate in the newly approved
  synthetic cohort.
- Added traceable Phase 9 JSON/CSV evidence with source/model SHA-256 hashes.
- Added executable Phase 9 acceptance gates and business-impact regression
  tests.
- Promoted `make phase9-verify` to the current cumulative CI and deployment
  preflight gate.
- Preserved the Phase 1–7 historical 63-test verification boundary.

<!-- PHASE8_CHANGELOG -->
## v0.8.1 — Public Repository & Consistency Hardening

- Enabled enforced `main` branch protection with required quality, Terraform,
  security, and container checks.
- Pinned all external GitHub Actions to immutable commit SHAs.
- Added MIT license, security policy, and contribution policy.
- Scoped AWS OIDC permission to the deployment job.
- Serialized production deployment execution.
- Removed stale/dead deployment model-version configuration.
- Aligned release-manifest application version with the package release.
- Hardened the serving container to run as a non-root user.
- Migrated Starlette TestClient development dependency from deprecated
  `httpx` fallback to `httpx2`.
- Updated Phase 7/8 and repository-state documentation.
- Strengthened reviewer-document consistency tests.


## v0.8.0 — Governance Evidence & Traceability

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
