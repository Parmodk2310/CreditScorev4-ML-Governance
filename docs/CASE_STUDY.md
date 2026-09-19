# CreditScoreV4 ML Governance — Engineering Case Study

## 1. Executive Summary

CreditScoreV4 ML Governance is a synthetic credit-risk governance system. It demonstrates how an ML engineering team can detect upstream data failures, quantify model and subgroup degradation, explain likely proxy behavior, enforce deterministic governance gates, and move only approved candidates through a safe serving and release lifecycle.

The project is deliberately structured as a sequence of increasingly subtle failure modes. Vendor B is visibly bad and should be blocked by data-quality controls. Vendor C remains contract-valid yet creates critical drift. Vendor D remains aggregate-stable yet creates material subgroup disparities. These scenarios prevent the governance story from collapsing into a single “schema validation” check.

The final lifecycle is:

```text
Incident reproduction
  -> Data-quality governance
  -> Drift governance
  -> Fairness + explainability
  -> Evidence-backed model governance
  -> Governed serving
  -> Shadow / canary / rollback
  -> Automated, fail-closed cloud delivery
```

The v0.8.0 code line verifies 63 Phase 1–7 regression tests plus 6 Phase 8 evidence-contract tests, together with quality, Terraform, container, secret-scanning, and IaC security controls.

## 2. Why I Built This

Typical ML projects answer: “Can I train a model?” Production ML systems must answer harder questions:

- Is incoming data still trustworthy?
- Is it statistically similar to the reference population?
- Is model behavior stable for relevant subgroups?
- Can an engineer explain why a candidate is blocked?
- Can a promotion decision be reproduced from evidence?
- Can an approved candidate still be rolled out safely?
- Can CI/CD fail closed when deployment prerequisites are absent?

This project was built to demonstrate those engineering questions in one coherent system.

## 3. Failure Scenario

The simulated system is a credit-risk model consuming vendor-supplied risk signals. The baseline is healthy, and then controlled vendor variants introduce three different classes of incident:

```text
Vendor A = healthy reference
Vendor B = material data-quality degradation
Vendor C = contract-valid distribution drift
Vendor D = aggregate-stable subgroup/fairness stress
```

The purpose is not to imitate a real bank dataset. The purpose is to create deterministic evidence that exercises each governance boundary.

## 4. Healthy Baseline

Phase 1 generates and trains the baseline, then records healthy metrics before introducing the incident fixture.

Measured baseline evidence:

| Metric | Healthy baseline |
|---|---:|
| ROC-AUC | **0.8025** |
| `device_risk_score` null rate | **3.14%** |

The baseline is important because later phases compare against known reference behavior rather than arbitrary thresholds.

## 5. Vendor B — Data Quality Failure

Vendor B reproduces an obvious upstream failure:

| Metric | Healthy | Vendor B |
|---|---:|---:|
| ROC-AUC | 0.8025 | **0.7329** |
| AUC degradation | — | **0.0696** |
| `device_risk_score` null rate | 3.14% | **22.00%** |

Phase 2 applies schema/contract and data-quality controls. Vendor A passes; Vendor B is blocked, produces failed contract/evaluation evidence, and is quarantined.

The design point is simple: obviously degraded input should not reach later model-promotion decisions.

## 6. Vendor C — Contract-Valid Drift

Vendor C is intentionally more subtle. It preserves the data-quality contract, row count, schema, and required missingness behavior, so Phase 2 passes. Phase 3 then detects distributional change.

Measured Phase 3 evidence:

- Phase 2 decision: **PASS**
- Overall drift: **CRITICAL**
- Critical features: `device_risk_score`, `bank_transaction_risk`
- Prediction drift: **CRITICAL**
- Prediction PSI: **0.2379**
- Prediction KS: **0.1863**

Contract validation and drift monitoring are separate controls. A dataset can be structurally valid and still be operationally unsafe.

## 7. Vendor D — Subgroup/Fairness Stress

Vendor D exercises a third failure mode: aggregate monitoring can look healthy while subgroup outcomes degrade.

Measured Phase 4 evidence:

- Phase 2 data-quality gate: **PASS**
- Phase 3 aggregate drift: **STABLE**
- Fairness governance: **FAIL**
- Demographic parity ratio: **0.7480**
- Selection-rate difference: **0.1860**
- Equalized-odds difference: **0.2269**

Protected/evaluation-only attributes remain absent from the model and SHAP feature set. SHAP analysis instead highlights stressed proxy features including `bank_transaction_risk`, `credit_utilization`, and `device_risk_score`.

This phase is not a claim that SHAP proves causality. It demonstrates how explainability can help an engineer investigate which model inputs participate in a subgroup stress scenario.

## 8. Governance Architecture

Phase 5 converts previously generated evidence into deterministic promotion decisions.

```text
                        +--------------------+
Data quality ---------->|                    |
Drift ----------------->|                    |
Performance ----------->| Governance policy  |----> APPROVE / REJECT
Calibration ----------->| + blocking gates   |            |
Fairness -------------->|                    |            +--> registry transition
Evidence integrity ---->|                    |            +--> audit record
                        +--------------------+            +--> decision artifact
```

Key properties:

- versioned policy configuration
- configurable blocking gates
- explicit blocking reasons
- SHA-256 evidence integrity verification
- deterministic decisions
- machine-readable decision artifacts
- append-only audit evidence

## 9. Model Registry

The project uses a project-owned registry/state machine rather than claiming MLflow integration.

Phase 5 scenarios:

| Candidate | Governance decision | Registry result |
|---|---|---|
| Healthy | **APPROVE** | `CANDIDATE -> STAGING` |
| Vendor C | **REJECT** | `REJECTED` because drift blocks |
| Vendor D | **REJECT** | `REJECTED` because fairness blocks |

Phase 5 verification also checks persistence, illegal transition blocking, 15 audit records, and 22 evidence artifacts.

A future production implementation could back this contract with MLflow or another model registry without changing the policy semantics.

## 10. Serving Architecture

Phase 6 turns the approved model into a governed FastAPI service.

```text
Client
  |
  v
FastAPI service
  |-- /health
  |-- /ready
  |-- /predict
  |-- /batch-predict
  |-- /model
  `-- /metrics
          |
          +--> model artifact
          +--> Prometheus-compatible metrics
```

Verification confirms HTTP 200 behavior for all six endpoints.

## 11. Shadow / Canary / Rollback

Approval is not equivalent to immediate production release. Phase 6 extends the lifecycle:

```text
STAGING -> SHADOW -> CANARY -> PRODUCTION
              |         |
              +---------+----> STAGING (rollback)
```

The healthy path exercises canary shares at **10%, 25%, 50%, and 100%**, then reaches production.

A degraded release intentionally fails release gates for:

- error rate
- mean risk delta
- p95 latency

The result is a rollback to **STAGING** with a recorded reason. Direct `CANDIDATE -> PRODUCTION` promotion remains illegal.

## 12. CI/CD and Security

Phase 7 adds the delivery controls needed to make the previous phases repeatable in pull requests:

- Python 3.12 quality workflow
- Ruff
- Black
- mypy
- compile checks
- cumulative verification
- Docker image build and smoke test
- Gitleaks secret scanning
- Trivy Terraform/IaC scanning
- Terraform format/validation
- release manifest generation

The final Phase 7 pull request completed with **5/5 successful checks**.

## 13. AWS/Terraform Architecture

The Terraform design defines a gated AWS path:

```text
GitHub Actions
   |
   +-- OIDC role assumption
   |
   v
Amazon ECR (immutable image)
   |
   v
ECS/Fargate service
   |
   v
HTTPS Application Load Balancer
   |
   v
Model-serving container
```

Additional controls include restricted service ingress, ALB health checks, immutable ECR handling, persistent Terraform state requirements, and ACM certificate configuration.

The important safety property is the default:

```text
AWS_DEPLOY_ENABLED=false
```

Terraform is validated and security-scanned, but the repository does not claim that this release was applied to a live production AWS account.

## 14. Verification Evidence

Release-level verified boundaries:

| Boundary | Evidence |
|---|---|
| Phase 1 | incident reproduced with expected AUC/null degradation |
| Phase 2 | healthy pass + Vendor B block/quarantine |
| Phase 3 | Vendor C contract-valid critical drift |
| Phase 4 | aggregate-stable fairness failure + SHAP investigation |
| Phase 5 | approve/reject decisions, integrity hashes, registry/audit evidence |
| Phase 6 | serving endpoints, shadow/canary path, rollback path |
| Phase 7 | CI/security/container/Terraform controls |
| Phase 8 | reviewer evidence contract and documentation/configuration traceability |
| Phase 1–7 regression suite | **63 passed** |
| Phase 8 evidence-contract tests | **6 passed** |
| Phase 1–8 tests exercised by the cumulative gate | **69 passed** |
| Phase 8 implementation PR #9 checks | **5/5 successful** |

## 15. Design Decisions

### Separate quality, drift, and fairness gates

These failures have different semantics. Combining them into one “health score” would hide why a candidate was blocked.

### Keep promotion deterministic

A policy engine is easier to test and audit when the same evidence always produces the same decision.

### Treat explainability as investigation evidence

SHAP helps identify influential inputs. It is not presented as proof of causality or legal fairness compliance.

### Use an explicit state machine

Release transitions are constrained so a model cannot skip governance or safe rollout states.

### Fail cloud delivery closed

The safest default is no AWS mutation unless prerequisites and explicit confirmation are present.

## 16. Limitations

- Synthetic data and incident fixtures, not a real lending dataset.
- No claim of regulatory compliance or certified fairness.
- Protected attributes are evaluation/governance-only and excluded from model inputs.
- The registry/audit implementation is project-owned rather than a managed MLflow deployment.
- Phase 7 defines and validates a cloud path; it does not prove a live production deployment.
- The current repo does not rely on Airflow orchestration; GitHub Actions, scripts, and Make targets drive the verified lifecycle.
- Load, fault-injection, multi-region resilience, and long-running SLO evidence are outside v0.8.0.

## 17. What I Would Build Next

The next iteration should deepen operational realism rather than add more isolated features:

1. **Managed registry backend** — MLflow or equivalent while keeping the current evidence/policy contract.
2. **Workflow orchestration** — Airflow for scheduled quality/drift/fairness jobs and retraining workflows.
3. **Durable control-plane storage** — S3/PostgreSQL-backed registry, audit, and evidence metadata.
4. **Artifact provenance** — SBOM, image signing, attestations, and verifiable build provenance.
5. **Observability** — OpenTelemetry traces, SLOs, error budgets, and alert routing.
6. **Performance testing** — realistic concurrency, latency distributions, capacity limits, and rollback under load.
7. **Live gated environment** — a cost-capped AWS staging environment with actual Terraform apply/destroy evidence.

<!-- PHASE8_CASE_STUDY -->
## 18. Evidence Traceability

Phase 8 adds an evidence-traceability layer over the existing Phase 1–7
implementation. It connects policy, release control, tests, screenshots, and
generated artifacts into a reviewable contract rather than creating a second
governance system.

Useful entry points:

- `docs/GOVERNANCE_POLICY.md`
- `docs/MODEL_CARD.md`
- `docs/MODEL_VALIDATION_REPORT.md`
- `docs/MONITORING_PLAN.md`
- `docs/EVIDENCE_INDEX.md`
- `docs/TECHNICAL_DEEP_DIVE.md`
- `docs/REPRODUCIBLE_DEMO.md`
- `docs/LIMITATIONS.md`

`scripts/verify_phase8.py` checks that reviewer documentation remains aligned
with executable Phase 5–7 configuration and generated Phase 1–7 evidence. This
reduces documentation drift: a README or case study should not silently claim a
threshold, state transition, release outcome, or deployment property the
repository no longer implements.
