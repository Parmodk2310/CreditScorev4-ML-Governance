# Changelog

All notable releases of CreditScoreV4 ML Governance are documented here.

The phased releases record the evolution from incident reproduction to governed model delivery.

## v1.0.1 — Stability & Consistency Hardening

This maintenance release tightens consistency between the repository's governance claims and the serving/runtime implementation without adding a new project phase.

### Fixed

- Aligned installed package and FastAPI runtime version metadata at `1.0.1`.
- Applied the shared versioned credit-application contract to online scoring requests.
- Recorded the generated model SHA-256 in Phase 1 evidence and verified it before model deserialization.
- Removed internal model-path disclosure from the `/model` response.
- Replaced raw serving exception disclosure with stable client-facing errors.
- Replaced raw request-path Prometheus labels with bounded route-template labels.
- Added a stable product-level decision-policy contract for the synthetic `0.50` approval threshold.

### Validation and scope

- Added coverage measurement with an XML CI artifact without imposing an arbitrary coverage threshold.
- Added Prometheus configuration validation, Docker Compose validation, and an API + Prometheus + Grafana integration smoke test.
- Added direct critical-path tests for SHAP leakage protection and workflow contracts.
- Clarified that the current model fixture uses deterministic stratified random holdout validation, not out-of-time credit validation.
- Clarified that fairness results are deterministic point estimates and do not claim confidence intervals or population-level inference.
- Clarified that SHA-256 integrity checks are not equivalent to signed build provenance.

### Maintenance policy

- v1.0.1 freezes functional expansion of the project. The v1.x line is limited to correctness, security, reproducibility, dependency, CI/test, and documentation maintenance.
- No Phase 14, automatic retraining/promotion, unrelated platform additions, or new model families are planned for this repository.

## v1.0.0 — Stable ML Governance Case Study

CreditScoreV4 reaches its first stable release after the Phase 1–13 engineering
sequence.

This release does not introduce new model behavior. It consolidates the
verified system into a stable product-level review and release boundary.

### Release interface

- Added `make release-verify` as the stable cumulative verification command.
- Preserved Phase 1–13 verification targets for historical reproducibility.
- Updated CI and deployment preflight to use the stable release interface.
- Added structural validation for all GitHub Actions workflows.

### Documentation and navigation

- Reframed the repository as one integrated ML-governance system rather than
  thirteen separate implementation phases.
- Moved Phase 1–13 implementation history under `docs/phases/`.
- Added structured documentation links for architecture, governance, evidence, and operations.
- Added Phase 8–13 architecture diagrams in DOT, Mermaid, and rendered SVG.
- Updated case-study, monitoring, validation, limitations, and evidence
  documentation to the current release boundary.

### Verified engineering boundary

The stable release includes:

- deterministic synthetic incident reproduction;
- fail-closed data-quality governance;
- feature and prediction drift governance;
- single-axis and intersectional fairness review;
- SHAP-supported proxy-risk investigation;
- deterministic evidence-backed promotion decisions;
- governed registry state transitions;
- shadow/canary release and rollback;
- business-impact evidence;
- root-cause ablation and remediation diagnostics;
- scheduled fail-closed governance orchestration;
- deterministic incident-response and simulated SLA evidence;
- GitHub Actions, security scanning, container verification, Terraform, and
  gated AWS ECS/Fargate delivery architecture.

### Claim boundaries

v1.0.0 remains a deterministic synthetic engineering case study.

It does not claim:

- a real banking production incident;
- real customer or applicant data;
- regulatory certification or legal compliance;
- live production paging/on-call operations;
- automatic model retraining or promotion;
- an active production AWS deployment.

## v0.13.0 — Incident SLA & Operational Evidence

- Added deterministic Vendor B incident timeline and machine-readable event log.
- Added synthetic `HIGH` alert evidence for the existing Phase 2 data-quality block.
- Added project SLA evaluation for detection, alerting, governance block, triage, and root-cause completion.
- Added SHA-256 lineage to Phase 2, Phase 9, and Phase 10 evidence.
- Preserved automatic retraining/promotion as disabled and kept live paging out of scope.
- Promoted `make phase13-verify` to CI and deployment preflight.
- Extended scheduled monitoring to generate and upload Phase 13 operational evidence.
- Bumped the application release line to 0.13.0.

## v0.12.0 — Intersectional Fairness & Proxy-Risk Governance

- Added deterministic Vendor E intersectional proxy-stress evidence while
  preserving the trained model, labels, and protected/evaluation columns.
- Added intersectional fairness evaluation across
  `sex|synthetic_demographic_group` with minimum-support governance.
- Added favorable-decision demographic parity, selection-rate difference,
  equal-opportunity difference, equalized-odds difference, and
  false-approval-rate difference.
- Demonstrated an aggregate-STABLE fixture where `sex` is PASS,
  `synthetic_demographic_group` is WARNING, and `female|group_c` is FAIL.
- Added statistical proxy-risk screening using eta-squared for numeric features
  and Cramér's V for categorical features.
- Paired association shifts with SHAP model influence to produce review-priority
  signals without claiming causal or legal proxy status.
- Preserved the historical Phase 1–7 regression boundary at 63 tests and added
  11 focused Phase 12 tests.
- Promoted `make phase12-verify` to the CI and deployment preflight boundary.
- Extended scheduled monitoring to run and verify Phase 12 after the historical
  Phase 11 monitoring manifest is validated.
- Bumped the application release line to 0.12.0.

## v0.11.0 — Scheduled Monitoring & Governance Orchestration

- Added a scheduler-independent Python orchestration layer for the existing
  Phase 1–10 governance controls.
- Added an explicit dependency graph with fail-closed downstream skipping.
- Required configured evidence artifacts after each successful monitoring task.
- Added SHA-256 evidence capture, a monitoring-run manifest, and JSONL event log.
- Added a scheduled/read-only GitHub Actions monitoring workflow with manual
  dispatch support.
- Added post-run manifest verification before evidence upload.
- Kept automatic retraining and automatic model promotion disabled.
- Promoted `make phase11-verify` to the cumulative CI and deployment preflight
  boundary while preserving Phase 10 as the historical predecessor.
- Added 10 focused orchestration/integration/workflow-contract tests.
- Bumped the application release line to 0.11.0.

## v0.10.0 — Root-Cause Ablation & Remediation Governance

- Added a controlled 2x2 Vendor B ablation separating semantic score migration
  from elevated non-random missingness.
- Preserved the same applicants, labels, trained model, and decision threshold
  across root-cause scenarios.
- Measured semantic-only ROC-AUC at 0.7452 and missingness-only approval at
  78.46%, compared with 0.8025 AUC / 73.91% approval for healthy behavior.
- Validated the fitted median counterfactual control exactly.
- Recorded a fitted device-score median of 0.4036 versus a 0.4721 semantic
  reference mean for newly missing rows.
- Evaluated oracle restoration plus q60/q75/q90 fixed-model counterfactuals.
- Carried q75 forward only as a diagnostic validation candidate; no production
  preprocessing policy was changed.
- Kept Vendor B fail-closed at the existing Phase 2 data-quality gate.
- Added evidence-backed Phase 10 outcome gates and workflow-contract tests.
- Promoted `make phase10-verify` to the current cumulative CI and deployment
  preflight gate.
- Bumped the application release line to 0.10.0.

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

## v0.8.1 — Public Repository & Consistency Hardening

- Added the documented `main` branch-protection policy and required quality,
  Terraform, security, and container check definitions. The current private
  repository does not report `main` as protected; `docs/BRANCH_PROTECTION.md`
  is the authoritative current-state note.
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
- Strengthened documentation-consistency tests.

## v0.8.0 — Governance Evidence & Traceability

- Added structured documentation navigation and evidence traceability.
- Enforced cumulative Phase 8 verification in CI and the gated deployment preflight.
- Removed stale Airflow/MLflow/MinIO platform scaffolding that was not part of the verified implementation.
- Reduced `env.example` to the actual fail-closed AWS deployment contract.
- Added governance policy documentation tied to executable Phase 5 thresholds.
- Added a model card, validation report, monitoring plan, and limitations.
- Added technical design-decision documentation and a reproducible demo.
- Added a Phase 8 evidence contract and evidence manifest.
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
