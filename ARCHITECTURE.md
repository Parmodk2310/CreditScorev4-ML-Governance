# CreditScoreV4 ML Governance Architecture — Through Phase 7

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
  |-- CI: quality + Phase 6 regression + Phase 7 tests
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

Phase 7 does not bypass Phase 5/6 controls: the deploy workflow reruns quality and the Phase 6 governed release gate before cloud mutation. Deployment remains blocked unless explicitly enabled and confirmed.

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
