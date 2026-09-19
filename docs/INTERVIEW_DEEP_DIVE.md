# CreditScoreV4 — Interview Deep-Dive Guide

## Recruiter version — 30 seconds

> “I built CreditScoreV4 to show the parts of ML engineering that happen after training. It reproduces an upstream data incident, detects data-quality, drift, and fairness failures, converts evidence into auditable model-governance decisions, then safely serves and rolls out an approved model through shadow/canary/rollback. The final phase adds CI, security scans, Docker, Terraform, and a gated AWS ECS/Fargate deployment path.”

## Senior engineer version — 90 seconds

> “The project is intentionally built around three distinct failure modes. Vendor B breaks data quality, so it is blocked before use. Vendor C stays contract-valid but causes critical distribution and prediction drift, which proves schema validation is not a drift monitor. Vendor D stays aggregate-stable but creates subgroup disparities, which proves global metrics can hide fairness failures. Phase 5 consumes evidence from those controls using versioned blocking policy, verifies SHA-256 evidence integrity, produces deterministic approve/reject decisions, writes audit artifacts, and constrains registry transitions. Phase 6 separates governance approval from release approval with FastAPI serving, shadow deployment, deterministic canary routing, health gates, and rollback. Phase 7 makes the path repeatable with CI, Gitleaks, Trivy, immutable ECR, ECS/Fargate Terraform, HTTPS ALB, OIDC, and fail-closed deployment configuration.”

## Architecture walk-through

Use this order when whiteboarding:

```text
Reference data/model
   |
   +--> quality contract
   +--> drift baselines
   +--> fairness baselines
   |
Incoming candidate/batch
   |
   +--> Phase 2 quality evidence
   +--> Phase 3 drift evidence
   +--> Phase 4 fairness/SHAP evidence
   |
   v
Phase 5 governance policy + integrity checks
   |
   +--> APPROVE -> registry STAGING
   `--> REJECT  -> REJECTED + reason

STAGING -> SHADOW -> CANARY -> PRODUCTION
              \          /
               -> rollback -> STAGING

CI/security/Terraform validate the delivery path
```

## Deep technical questions

### Why do you need both data-quality and drift monitoring?

Data-quality checks validate structural/business constraints: schema, null limits, valid ranges, expected types, required columns. Drift monitoring compares distributions and model-score behavior against a reference. Vendor C is the test case: it passes the quality contract but still produces critical drift.

### Why is Vendor D important if you already have drift monitoring?

Aggregate drift can be stable while subgroup outcomes change. Vendor D is designed specifically to demonstrate that blind spot. Phase 4 evaluates subgroup metrics and uses SHAP as investigation evidence for proxy behavior.

### Does SHAP prove discrimination?

No. SHAP explains contribution/influence in model predictions; it does not establish causal discrimination. In this project it is an investigation tool attached to a synthetic fairness stress scenario.

### Why not use one combined “risk score” for governance?

A combined score can hide which control failed and creates arbitrary weighting. Blocking gates preserve semantics: data quality, drift, performance/calibration, fairness, and evidence integrity can each independently prevent promotion.

### Why build a custom registry instead of MLflow?

The purpose of Phase 5 is to demonstrate the governance contract and state machine directly: evidence in, policy evaluation, decision artifact, audit record, constrained transition. MLflow could be a backend later, but using it is not required to prove those semantics.

### What makes the governance decision deterministic?

The same versioned policy plus the same evidence bundle and hashes yields the same gate results and decision. The implementation records explicit blocking reasons rather than relying on manual interpretation.

### Why separate approval from production release?

Governance verifies whether a candidate is eligible. Release engineering verifies whether it behaves safely under serving conditions. The project therefore uses `STAGING -> SHADOW -> CANARY -> PRODUCTION` with rollback to staging.

### How does canary routing work?

The project exercises configured shares at 10%, 25%, 50%, and 100% using deterministic routing. This makes test outcomes reproducible and prevents random routing from making the verification flaky.

### What triggers rollback?

The degraded scenario fails release gates for error rate, mean risk delta, and p95 latency. The controller records the failed gates and returns the model to staging.

### What is the strongest Phase 7 safety property?

Deployment is fail-closed. The repository verifies CI, IaC, and deployment prerequisites, but cloud mutation remains disabled by default through `AWS_DEPLOY_ENABLED=false` and requires explicit configuration/confirmation.

### Is this deployed to a real AWS production account?

The repository demonstrates and validates the AWS architecture and deployment contract. The v0.7.0 evidence shown here does not claim that Terraform was applied to a live production account.

## Cross-questions senior engineers may ask

### “Why not block Vendor C in Phase 2?”

Because doing so would blur quality and drift semantics. Vendor C is deliberately contract-valid so the drift layer proves its independent value.

### “If Vendor D is aggregate-stable, what exactly changed?”

The synthetic stress changes model-relevant proxy behavior across evaluation groups while preserving aggregate constraints. The governance failure is driven by subgroup metrics rather than global distribution alarms.

### “What would you persist differently in production?”

Move registry/evidence/audit metadata from local JSON/files to durable object/database storage with immutable artifact references, retention, access control, and queryability.

### “How would you scale serving?”

Keep the API stateless, move model artifacts to versioned storage/registry, use autoscaled ECS/EKS tasks, add load tests/SLOs, and separate operational telemetry from governance evidence.

### “Where does Airflow fit?”

It is a future orchestration layer for scheduled data-quality, drift, fairness, retraining, and evidence workflows. The verified v0.7.0 lifecycle uses scripts, Make targets, and GitHub Actions instead of claiming Airflow is already present.

## What to say

- “production-style synthetic case study”
- “deterministic incident fixtures”
- “contract-valid drift”
- “aggregate-stable subgroup failure”
- “evidence-backed governance decision”
- “explicit registry state machine”
- “governance approval is separate from release approval”
- “fail-closed deployment path”

## What not to say

Do not claim:

- a real bank production incident
- legal/regulatory compliance certification
- causality from SHAP
- MLflow integration unless you actually add it
- Airflow orchestration unless you actually add it
- a live AWS production deployment unless you have apply/runtime evidence
- that fairness is “solved” by one threshold

## Best final answer to “What did you personally learn?”

> “The biggest lesson was that model quality is a layered systems problem. Schema validity, distribution stability, subgroup behavior, governance eligibility, and release health are different controls. Treating them as separate evidence-producing gates made the system easier to test, explain, and audit.”
