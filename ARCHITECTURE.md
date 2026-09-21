# CreditScoreV4 ML Governance Architecture

CreditScoreV4 v1.0.0 is organized as one integrated ML-governance system. The phase numbers remain useful for historical traceability, but the current architecture is better understood through four boundaries:

1. **data and model risk**
2. **governance and evidence integrity**
3. **serving and safe release**
4. **delivery, monitoring, and incident operations**

The diagrams below are the canonical high-level architecture views used by the README and engineering documentation.

---

## 1. System overview

<p align="center">
  <img src="docs/assets/diagrams/system-overview.svg"
       alt="CreditScoreV4 ML Governance system overview"
       width="100%" />
</p>

<p align="center">
  <sub><a href="docs/assets/diagrams/system-overview.mmd">Mermaid source</a></sub>
</p>

The architecture starts with deterministic synthetic scenarios and keeps the control layers independent:

- **Vendor A** provides the healthy reference.
- **Vendor B** exercises data-quality degradation and incident analysis.
- **Vendor C** exercises contract-valid distribution drift.
- **Vendor D** exercises subgroup fairness degradation.
- **Vendor E** exercises supported intersectional fairness and proxy-risk review.

Those scenarios feed independent data/model-risk controls before a model is allowed to reach governance or release state transitions.

### Phase mapping

| Architecture area | Historical implementation |
|---|---|
| Baseline + incident reproduction | Phase 1 |
| Data-quality governance | Phase 2 |
| Feature/prediction drift | Phase 3 |
| Fairness + explainability | Phase 4 |
| Governance policy + registry | Phase 5 |
| Serving + safe release | Phase 6 |
| CI/security/container/Terraform + gated AWS path | Phase 7 |
| Evidence contract + repository consistency | Phase 8 |
| Business-impact analysis | Phase 9 |
| Root-cause ablation | Phase 10 |
| Scheduled fail-closed orchestration | Phase 11 |
| Intersectional fairness + proxy-risk screening | Phase 12 |
| Incident timeline + SLA + lineage | Phase 13 |

The repository is one integrated system; the phase documents preserve its implementation history.

---

## 2. Data and model risk boundary

The first control layer answers whether incoming data and model behavior remain inside the project's accepted engineering envelope.

### Data quality

Phase 2 applies the versioned scoring contract plus Great Expectations-backed validation.

Material violations fail closed:

```text
incoming batch
      |
      v
contract / completeness / range checks
      |
      +---- PASS ----> downstream model-risk controls
      |
      `---- BLOCK ---> quarantine + evidence
```

Vendor B is the deterministic blocking scenario: `device_risk_score` missingness rises from `3.14%` to `22.00%`.

### Drift

Phase 3 uses Vendor C to verify that valid schema and null rates do not imply stable model behavior.

The layer evaluates:

- feature PSI;
- feature KS statistics;
- prediction PSI;
- prediction KS statistics;
- aggregate drift severity.

### Fairness and explainability

Phases 4 and 12 add group-level and intersectional governance.

Protected/evaluation attributes remain excluded from model inputs. SHAP and association statistics are used as investigation evidence; they are not treated as causal or legal conclusions.

---

## 3. Governance and release model

<p align="center">
  <img src="docs/assets/diagrams/governance-release-model.svg"
       alt="CreditScoreV4 governance and release model"
       width="900" />
</p>

<p align="center">
  <sub><a href="docs/assets/diagrams/governance-release-model.mmd">Mermaid source</a></sub>
</p>

A candidate is not promoted because one metric looks healthy. Promotion requires a complete evidence set.

The governance policy evaluates:

- data-quality decision;
- ROC-AUC;
- PR-AUC;
- calibration;
- drift status;
- fairness status;
- minimum evidence count;
- evidence hashes.

The project registry enforces legal transitions:

```text
REGISTERED -> CANDIDATE
CANDIDATE -> STAGING
CANDIDATE -> REJECTED

STAGING -> SHADOW
SHADOW -> CANARY
SHADOW -> STAGING       # rollback

CANARY -> PRODUCTION
CANARY -> STAGING       # rollback
```

A direct:

```text
CANDIDATE -> PRODUCTION
```

transition is disallowed by the registry.

### Governance versus release safety

Phase 5 answers:

> Is this candidate eligible to enter `STAGING`?

Phase 6 separately answers:

> Is the staged candidate healthy enough to progress through `SHADOW` and `CANARY` toward `PRODUCTION`?

That separation prevents governance approval from becoming an automatic production deployment.

### Release gates

The safe-release controller evaluates project guardrails for:

- request count;
- error rate;
- p95 latency;
- mean risk-output delta.

The healthy deterministic path exercises:

```text
STAGING -> SHADOW -> CANARY
                    10%
                    25%
                    50%
                    100%
                       -> PRODUCTION
```

A degraded path returns to `STAGING` and persists the rollback reason.

---

## 4. Serving and observability plane

The governed model is served through FastAPI:

```text
GET  /health
GET  /ready
POST /predict
POST /batch-predict
GET  /model
GET  /metrics
```

The serving process loads the same persisted sklearn/XGBoost pipeline used by governance verification.

Operational telemetry includes:

- request counts;
- latency;
- prediction outcomes;
- risk-distribution metrics;
- readiness;
- rollout stage;
- canary share;
- rollback count.

The local serving demonstration uses Prometheus and Grafana assets under `docker/runtime/`.

---

## 5. Delivery controls

<p align="center">
  <img src="docs/assets/diagrams/delivery-controls.svg"
       alt="CreditScoreV4 delivery controls"
       width="900" />
</p>

<p align="center">
  <sub><a href="docs/assets/diagrams/delivery-controls.mmd">Mermaid source</a></sub>
</p>

Merge verification and cloud mutation are separate systems.

### Pull-request and main-branch verification

The automated delivery boundary exercises:

```text
quality
  -> Ruff
  -> Black
  -> mypy
  -> compile
  -> current release verification

security
  -> Gitleaks
  -> Trivy filesystem
  -> Trivy Terraform/IaC

container
  -> deterministic model generation
  -> Docker build
  -> runtime smoke test
  -> built-image vulnerability report

infrastructure
  -> Terraform fmt
  -> Terraform validate
```

### Gated AWS deployment

Cloud deployment is manual and fail closed.

The path is:

```text
workflow_dispatch
      |
      v
explicit deployment confirmation
      |
      v
AWS_DEPLOY_ENABLED == true ?
      |
  +---+---+
  |       |
 false   true
  |       |
  v       v
no cloud  re-run release/security/IaC gates
mutation       |
               v
           GitHub OIDC
               |
               v
        immutable ECR digest
               |
               v
      persistent Terraform state
               |
               v
          ECS / Fargate
               |
               v
           HTTPS ALB
               |
               v
       health verification
               |
               v
         release manifest
```

`AWS_DEPLOY_ENABLED=false` remains the safe default.

The image workflow blocks on fixable HIGH/CRITICAL findings from the built
container. Filesystem and Terraform HIGH/CRITICAL findings remain blocking
security gates.

The repository validates this delivery architecture; v1.0.0 does not claim an active production AWS deployment.

---

## 6. Monitoring, analysis, and incident operations

### Scheduled governance

Phase 11 wraps the existing verified controls in a dependency-ordered monitoring cycle.

It records:

- task execution status;
- attempts;
- required evidence paths;
- SHA-256 evidence hashes;
- `monitoring_run.json`;
- `monitoring_events.jsonl`.

The scheduler is fail closed. A successful command that fails to produce required evidence is treated as a failed task.

Automatic retraining and automatic promotion remain disabled.

### Business impact

Phase 9 compares the exact same 15,000 synthetic applicants, labels, model artifact, and threshold between healthy and Vendor B inputs.

This isolates decision-impact evidence from model retraining.

### Root cause

Phase 10 decomposes the Vendor B incident into:

- healthy;
- semantic-only;
- missingness-only;
- combined.

Counterfactual replacements remain diagnostic-only. Vendor B stays blocked and production preprocessing is unchanged.

### Incident operations

Phase 13 consumes previously verified Vendor B evidence to produce:

- deterministic incident timeline;
- synthetic alert evidence;
- SLA calculations;
- cross-phase SHA-256 lineage;
- incident report.

It does not perform live paging, automatic retraining, automatic promotion, or production mutation.

---

## 7. Safety boundaries

The system keeps these boundaries explicit:

```text
synthetic evidence only
real applicant PII: not used
regulatory certification: not claimed
live production paging: disabled / not implemented
automatic retraining: false
automatic promotion: false
AWS deployment: false by default
```

Fairness thresholds, SLA thresholds, release thresholds, and model thresholds are engineering guardrails for this deterministic case study.

---

## 8. Architecture sources

The complete figure/source index is maintained in:

[`docs/ARCHITECTURE_FIGURES.md`](docs/ARCHITECTURE_FIGURES.md)

Primary v1 system diagrams:

- [`system-overview.mmd`](docs/assets/diagrams/system-overview.mmd) / [`system-overview.svg`](docs/assets/diagrams/system-overview.svg)
- [`governance-release-model.mmd`](docs/assets/diagrams/governance-release-model.mmd) / [`governance-release-model.svg`](docs/assets/diagrams/governance-release-model.svg)
- [`delivery-controls.mmd`](docs/assets/diagrams/delivery-controls.mmd) / [`delivery-controls.svg`](docs/assets/diagrams/delivery-controls.svg)

Phase-specific diagrams remain available for evidence/history review.

Validate architecture assets with:

```bash
make diagram-validate
```

Regenerate Graphviz-backed SVGs when Graphviz is installed with:

```bash
make diagram-render
```
