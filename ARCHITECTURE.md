# CreditScoreV4 ML Governance Architecture — Through Phase 11

```text
                           PHASE 1
Vendor A train ----------------------> CreditScoreV4
Vendor A holdout -------------------> healthy evaluation (~0.80 AUC)
        |
        +--> Vendor B migration ----> same model (~0.73 AUC)
                         |
                         v
                         PHASE 2
              versioned data contract
                 + Great Expectations
                         |
                  Vendor B --> BLOCK
                    quarantine/evidence
                         |
                         v
                         PHASE 3
Vendor A reference -------------------------------+
                                                   |
Vendor C: schema/type/range/null contract valid    |
        |                                          |
        +--> Phase 2 gate --> PASS                 |
        +--> feature PSI + KS <--------------------+
        +--> prediction PSI + KS
                         |
                  overall drift CRITICAL
                         |
                         v
                         PHASE 4
Vendor D: aggregate-valid subgroup proxy stress
        |
        +--> Phase 2 quality --> PASS
        +--> Phase 3 aggregate drift --> STABLE
        +--> Fairlearn subgroup assessment --> FAIL
        +--> SHAP explains non-protected proxy drivers
                         |
                         v
                         PHASE 5
quality + performance + calibration + drift + fairness + hashes
                         |
                  configurable policy engine
                         |
                   +-----+-----+
                   |           |
                APPROVE      REJECT
                   |           |
                   v           v
                STAGING     REJECTED
                   |
                   v
                         PHASE 6
                 governed FastAPI serving
                   /predict /batch-predict
             /health /ready /model /metrics
                   |
                   v
                 SHADOW
                   |
                   v
                 CANARY
          10% -> 25% -> 50% -> 100%
                   |
             +-----+-----+
             |           |
          healthy      degraded
             |           |
             v           v
        PRODUCTION     STAGING
                      rollback
```

## Phase 6 release boundary

Phase 5 decides whether a model may enter `STAGING`. Phase 6 is the only layer that can move an approved staged model through `SHADOW`, `CANARY`, and `PRODUCTION`.

The registry transitions are:

```text
REGISTERED -> CANDIDATE -> STAGING -> SHADOW -> CANARY -> PRODUCTION
                       \-> REJECTED      \-----------> STAGING rollback
                                      SHADOW --------> STAGING rollback
```

`CANDIDATE -> PRODUCTION` remains illegal.

## Serving plane

The serving process loads the same persisted sklearn/XGBoost pipeline used by the governance evidence. Request validation is handled by Pydantic/FastAPI, inference is serialized through the predictor wrapper, and `/model` exposes the model artifact SHA-256 used for operational traceability.

## Observability plane

The API exposes Prometheus metrics for request counts, latency, prediction outcomes, risk distribution, readiness, rollout stage, canary share, and rollback count. `docker/phase6/` provisions a local Prometheus + Grafana demonstration stack.

## Safe-release controller

Traffic assignment is deterministic from a SHA-256 request bucket. Shadow and canary checkpoints use configurable project guardrails for request volume, error rate, p95 latency, and mean risk-output delta. Failed blocking gates trigger rollback to `STAGING` and append a release audit event.

## Phase 7 automation/deployment plane

```text
GitHub PR / main
  |-- CI: quality + cumulative Phase 11 verification
  |-- Security: Gitleaks + Trivy fs/config
  |-- Image: deterministic model generation -> Docker build -> smoke test
  `-- Terraform: fmt + init -backend=false + validate

Manual workflow_dispatch only
  -> fail-closed deployment gate
  -> GitHub OIDC -> AWS role
  -> persistent S3 Terraform backend
  -> Terraform-managed ECR bootstrap
  -> immutable image push + digest resolution
  -> ECS/Fargate + ALB deployment
  -> deployed health verification
  -> release manifest evidence
```

Phase 7 does not bypass the governance controls: the deploy workflow reruns quality and the cumulative Phase 11 verification gate before cloud mutation. Deployment remains blocked unless explicitly enabled and confirmed.

<!-- PHASE8_ARCHITECTURE -->
## Phase 8 evidence/reviewer plane

Phase 8 does not change the prediction or release data plane. It adds a
cross-cutting evidence/reviewer plane:

```text
Phase 1-7 configs + source + tests + generated evidence
                         |
                         v
              Phase 8 evidence contract
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
   governance docs   evidence index   reviewer manifest
          |              |              |
          +--------------+--------------+
                         |
                         v
          reproducible technical review
```

The Phase 8 verifier checks documentation/visual presence, policy thresholds,
registry transitions, release guardrails, fail-closed deployment behavior, and
generated governance/release evidence.

## Phase 9–10 incident-analysis plane

Phase 9 measures decision/outcome impact for the exact Vendor B fixture. Phase
10 then decomposes that same fixture without retraining the model:

```text
healthy -----------------------------+
  |                                  |
  +--> semantic-only                 |
  +--> missingness-only              |
  +--> combined Vendor B             |
                                      v
                              2x2 root-cause evidence
                                      |
                          +-----------+-----------+
                          |                       |
                          v                       v
                 oracle restoration       q60/q75/q90
                 diagnostic only          fixed-model candidates
                          |                       |
                          +-----------+-----------+
                                      v
                         q75 validation candidate only
                                      |
                                      v
                         Vendor B remains BLOCKED
                         production policy unchanged
```

The analysis keeps the applicant population, labels, baseline model artifact,
and decision threshold fixed. The fitted missingness indicator is preserved
during counterfactual value overrides so the experiment isolates the numeric
replacement path rather than silently changing the fitted preprocessing
contract.


## Phase 11 scheduled monitoring/orchestration plane

Phase 11 adds a control-plane scheduler around the existing verified lifecycle;
it does not create a second promotion authority.

```text
GitHub Actions schedule / workflow_dispatch
                  |
                  v
        run_monitoring_cycle.py
                  |
                  v
        dependency-ordered tasks
 Phase 1 -> ... -> Phase 10 verification
                  |
        +---------+----------+
        |                    |
        v                    v
 command status       required evidence
        |                    |
        +---------+----------+
                  |
                  v
       SHA-256 evidence hashes
                  |
        +---------+----------+
        |                    |
        v                    v
 monitoring_run.json   monitoring_events.jsonl
                  |
                  v
          verify_phase11.py
```

The orchestration contract is fail closed. A failed prerequisite prevents its
dependents from running and records them as `SKIPPED`. A command that exits
successfully but fails to produce configured evidence is also treated as a
failed task.

The scheduled workflow has read-only repository permissions and verifies the
generated monitoring manifest before uploading the Phase 11 evidence artifact.
`automatic_retraining=false` and `automatic_promotion=false` are explicit
release contracts. Governance eligibility remains owned by Phase 5, and runtime
promotion remains owned by Phase 6.
