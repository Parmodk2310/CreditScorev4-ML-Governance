# CreditScoreV4 ML Governance — Engineering Case Study

## 1. Executive Summary

CreditScoreV4 ML Governance is a synthetic credit-risk governance system covering upstream data failures, model and subgroup degradation, proxy-risk investigation, deterministic governance gates, and controlled serving and release.

The failure scenarios become progressively subtler across the control stack. Vendor B is visibly bad and should be blocked by data-quality controls. Vendor C remains contract-valid yet creates critical drift. Vendor D remains aggregate-stable yet creates material subgroup disparities. These scenarios prevent the governance story from collapsing into a single “schema validation” check.

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
  -> Scheduled, fail-closed governance monitoring
```

The current release preserves the historical 63-test Phase 1–7 regression boundary, then layers evidence contracts, business-impact analysis, root-cause ablation, scheduled fail-closed governance monitoring, intersectional fairness/proxy-risk review, and deterministic incident-operations SLA evidence on top. Quality, Terraform, container, secret-scanning, and IaC security controls remain part of the release boundary.


Current architecture: [`ARCHITECTURE_FIGURES.md`](ARCHITECTURE_FIGURES.md), including the complete Phase 1–13 view.

## 2. Engineering Motivation

The system is designed around operational questions that are not covered by model training alone:

- Is incoming data still trustworthy?
- Is it statistically similar to the reference population?
- Is model behavior stable for relevant subgroups?
- Can an engineer explain why a candidate is blocked?
- Can a promotion decision be reproduced from evidence?
- Can an approved candidate still be rolled out safely?
- Can CI/CD fail closed when deployment prerequisites are absent?

The synthetic environment exercises those engineering questions in one controlled system.

## 3. Failure Scenario

The simulated system is a credit-risk model consuming vendor-supplied risk signals. The baseline is healthy, and then controlled vendor variants introduce three different classes of incident:

```text
Vendor A = healthy reference
Vendor B = material data-quality degradation
Vendor C = contract-valid distribution drift
Vendor D = aggregate-stable subgroup/fairness stress
Vendor E = aggregate-stable intersectional proxy stress
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

Vendor C is subtler. It preserves the data-quality contract, row count, schema, and required missingness behavior, so Phase 2 passes. Phase 3 then detects distributional change.

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

SHAP is used here as investigative evidence for which model inputs participate in the subgroup stress scenario; it is not treated as causal proof.

## 8. Business Impact of Vendor B

Phase 9 connects the Vendor B technical degradation to model decisions and
observed outcomes on the same 15,000 synthetic applicants.

| Metric | Healthy | Vendor B | Change |
|---|---:|---:|---:|
| Approval rate | 73.91% | 78.60% | +4.69 pp |
| Approved 30-day default rate | 21.80% | 26.37% | +4.57 pp |
| Mean predicted risk | 0.3414 | 0.3274 | -0.0140 |

The incident changes 2,500 decisions (16.67%). It creates 1,602 newly approved
applicants and 898 newly rejected applicants. The newly approved synthetic
cohort has a 61.99% observed 30-day default rate.

Because the applicant population and outcome labels are unchanged, this is a
controlled decision-impact comparison. It remains synthetic evidence rather
than a claim about real-world lending loss.

## 9. Root-Cause Ablation and Remediation

Phase 10 decomposes Vendor B into semantic migration and elevated missingness
while keeping the same 15,000 applicants, `default_30d` labels, trained model,
and 0.50 decision threshold fixed.

| Scenario | ROC-AUC | Approval rate | Approved 30-day default |
|---|---:|---:|---:|
| Healthy | 0.8025 | 73.91% | 21.80% |
| Semantic-only | 0.7452 | 75.94% | 25.12% |
| Missingness-only | 0.7796 | 78.46% | 24.41% |
| Combined Vendor B | 0.7329 | 78.60% | 26.37% |
| q75 validation candidate | 0.7418 | 74.25% | 24.78% |

Semantic migration contributes more strongly to discrimination loss, while
missingness contributes more strongly to approval inflation. The fitted
`device_risk_score` median is 0.4036, below the 0.4721 semantic reference mean
for newly missing rows.

The q75 counterfactual reduces decision distortion but does not restore healthy
model quality or approved-cohort outcomes. It is therefore retained only as a
diagnostic validation candidate. Vendor B remains blocked by Phase 2 and the
production preprocessing policy is unchanged.

These conclusions are scoped to the deterministic synthetic fixture and are
not claims about a real lending incident or regulatory compliance.

## 10. Governance Architecture

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

## 11. Model Registry

The project uses a project-owned registry/state machine rather than claiming MLflow integration.

Phase 5 scenarios:

| Candidate | Governance decision | Registry result |
|---|---|---|
| Healthy | **APPROVE** | `CANDIDATE -> STAGING` |
| Vendor C | **REJECT** | `REJECTED` because drift blocks |
| Vendor D | **REJECT** | `REJECTED` because fairness blocks |

Phase 5 verification also checks persistence, illegal transition blocking, 15 audit records, and 22 evidence artifacts.

A future production implementation could back this contract with MLflow or another model registry without changing the policy semantics.

## 12. Serving Architecture

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

## 13. Shadow / Canary / Rollback

Approval is not equivalent to immediate production release. Phase 6 extends the lifecycle:

```text
STAGING -> SHADOW -> CANARY -> PRODUCTION
              |         |
              +---------+----> STAGING (rollback)
```

The healthy path exercises canary shares at **10%, 25%, 50%, and 100%**, then reaches production.

A degraded release fails release gates for:

- error rate
- mean risk delta
- p95 latency

The result is a rollback to **STAGING** with a recorded reason. Direct `CANDIDATE -> PRODUCTION` promotion remains illegal.

## 14. CI/CD and Security

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

The current delivery boundary verifies quality, Terraform, secrets, IaC/filesystem security, and container build/smoke behavior.

## 15. AWS/Terraform Architecture

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

## 16. Verification Evidence

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
| Phase 8 | evidence contract and documentation/configuration traceability |
| Phase 9 | controlled business-impact and decision-transition evidence |
| Phase 10 | controlled root-cause ablation and remediation counterfactual evidence |
| Phase 11 | scheduled fail-closed monitoring, evidence hashing, manifest/event-log verification |
| Phase 12 | intersectional fairness, equal-opportunity evidence, and proxy-risk screening |
| Phase 1–7 regression suite | **63 passed** |
| Phase 8 evidence-contract tests | **6 passed** |
| Phase 9 business-impact tests | **6 passed** |
| Phase 10 root-cause/remediation tests | **6 passed** |
| Phase 11 orchestration/integration/workflow-contract tests | **10 passed** |
| Phase 12 fairness/proxy-risk tests | **11 passed** |
| Phase 13 incident-operations tests | **16 passed** |
| Focused test executions exercised by the cumulative current release gate | **PASS; coverage measured separately in CI** |

## 17. Design Decisions

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

## 18. Limitations

- Synthetic data and incident fixtures, not a real lending dataset.
- No claim of regulatory compliance or certified fairness.
- Protected attributes are evaluation/governance-only and excluded from model inputs.
- The registry/audit implementation is project-owned rather than a managed MLflow deployment.
- Phase 7 defines and validates a cloud path; it does not prove a live production deployment.
- Phase 11 uses GitHub Actions as the concrete scheduler around a Python orchestration engine; it does not claim a managed Airflow deployment.
- Scheduled runs are deterministic synthetic governance-control executions, not continuous monitoring of live lending traffic.
- No production paging/on-call integration or automatic retraining/promotion is implemented.
- Load, fault-injection, multi-region resilience, and long-running SLO evidence remain outside the current scope.

## 19. Evidence Traceability

Phase 8 adds an evidence-traceability layer over the existing Phase 1–7
implementation. It connects policy, release control, tests, screenshots, and
generated artifacts into a traceable contract rather than creating a second
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

`scripts/verify_phase8.py` checks that documentation remains aligned
with executable Phase 5–7 configuration and generated Phase 1–7 evidence. This
reduces documentation drift by preventing documentation from claiming a
threshold, state transition, release outcome, or deployment property that the
repository no longer implements.


## 20. Scheduled Monitoring and Governance Orchestration

Phase 11 moves the verified controls from an entirely manual execution model to
a scheduled, auditable control run without changing model-promotion authority.

```text
GitHub Actions schedule / manual dispatch
                  |
                  v
       Phase 11 Python orchestrator
                  |
                  v
      dependency-ordered Phase 1–10 tasks
                  |
          +-------+-------+
          |               |
          v               v
      task status     evidence paths
          |               |
          +-------+-------+
                  |
                  v
           SHA-256 evidence
                  |
          +-------+-------+
          |               |
          v               v
 monitoring_run.json  monitoring_events.jsonl
```

The acceptance run executes 12 tasks and requires every task to pass. A failed
dependency causes downstream work to be recorded as `SKIPPED`, and a command
that does not produce configured evidence is treated as failed even if its
process exit code is zero.

The scheduler is not a retraining or promotion authority:
`automatic_retraining=false` and `automatic_promotion=false`. Findings feed
the existing governance path rather than creating a scheduler-to-production
shortcut.


## 21. Vendor E — Intersectional Fairness and Proxy-Risk Review

Phase 12 adds a deterministic failure mode that is harder to
detect with single-axis monitoring.

Vendor E preserves the protected/evaluation columns and `default_30d` labels,
but increases three non-protected model inputs only for the supported
`female|group_c` intersection:

```text
device_risk_score      +0.12
credit_utilization     +0.06
bank_transaction_risk  +0.05
```

The batch still passes the data-quality gate and aggregate drift remains
STABLE. The `sex` axis remains PASS and
`synthetic_demographic_group` is WARNING, while the supported intersection
fails the project fairness thresholds.

Measured intersectional evidence:

| Metric | Vendor E |
|---|---:|
| Target support | 1,058 |
| Demographic-parity ratio | 0.7479 |
| Selection-rate difference | 0.1873 |
| Equal-opportunity difference | 0.1956 |
| Equalized-odds difference | 0.2600 |
| False-approval-rate difference | 0.2600 |

Proxy-risk analysis then asks two separate questions: whether each model input
became more statistically associated with the protected intersection, and
whether the fitted model materially uses that input. Numeric association uses
eta-squared; categorical association uses Cramér's V; model influence uses SHAP
mean absolute attribution.

The three stressed inputs surface as review priorities:
`device_risk_score`, `credit_utilization`, and
`bank_transaction_risk`.

This evidence supports investigation and governance review. It does not prove
causality, legal proxy status, unlawful discrimination, or regulatory
non-compliance.

## 22. Remaining Production Gaps / Future Work

Future work focuses on operational realism rather than additional isolated features:

1. **Managed registry backend** — MLflow or equivalent while keeping the current evidence/policy contract.
2. **Durable orchestration backend when scale warrants it** — Airflow, Dagster, or Argo with backfill/history while preserving the current task/governance contract.
3. **Durable control-plane storage** — S3/PostgreSQL-backed registry, audit, and evidence metadata.
4. **Artifact provenance** — SBOM, image signing, attestations, and verifiable build provenance.
5. **Observability** — OpenTelemetry traces, SLOs, error budgets, and alert routing.
6. **Performance testing** — realistic concurrency, latency distributions, capacity limits, and rollback under load.
7. **Live gated environment** — a cost-capped AWS staging environment with actual Terraform apply/destroy evidence.
