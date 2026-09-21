<p align="center">
  <h1 align="center">CreditScoreV4 ML Governance</h1>
  <p align="center">
    A synthetic, evidence-backed ML governance system for detecting unsafe data/model changes,
    blocking invalid promotion, and exercising controlled serving, rollback, monitoring, and delivery.
  </p>
</p>

<p align="center">
  <a href="https://github.com/Parmodk2310/CreditScorev4-ML-Governance/actions/workflows/ci.yml">
    <img src="https://github.com/Parmodk2310/CreditScorev4-ML-Governance/actions/workflows/ci.yml/badge.svg" alt="Quality and governance" />
  </a>
  <a href="https://github.com/Parmodk2310/CreditScorev4-ML-Governance/actions/workflows/security.yml">
    <img src="https://github.com/Parmodk2310/CreditScorev4-ML-Governance/actions/workflows/security.yml/badge.svg" alt="Security" />
  </a>
  <a href="https://github.com/Parmodk2310/CreditScorev4-ML-Governance/actions/workflows/image.yml">
    <img src="https://github.com/Parmodk2310/CreditScorev4-ML-Governance/actions/workflows/image.yml/badge.svg" alt="Container image" />
  </a>
  <a href="https://github.com/Parmodk2310/CreditScorev4-ML-Governance/releases">
    <img src="https://img.shields.io/github/v/release/Parmodk2310/CreditScorev4-ML-Governance" alt="Latest release" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12" />
</p>

> **Core idea:** model accuracy alone is not enough to justify promotion.
> CreditScoreV4 requires independent data-quality, drift, fairness, evidence-integrity,
> release-health, and delivery controls before a candidate can progress.

This repository is a **deterministic synthetic engineering case study**. It does not use real applicant data and does not claim regulatory certification, a live banking deployment, or production on-call operations.

<p align="center">
  <img src="docs/assets/diagrams/phase1-13-end-to-end.svg"
       alt="CreditScoreV4 end-to-end ML governance architecture"
       width="100%" />
</p>

## Why this project exists

Many ML projects stop at training and offline evaluation. This project focuses on the harder operational question:

**What evidence should exist between a trained model and production traffic?**

The system demonstrates five independent control areas:

| Control area | What it protects against |
|---|---|
| **Data & model risk** | schema failures, missingness, feature/prediction drift, subgroup degradation |
| **Governance** | unsupported promotion, stale/tampered evidence, illegal registry transitions |
| **Release safety** | unhealthy runtime behavior during shadow/canary rollout |
| **Delivery** | unsafe CI/CD, container, Terraform, secret, and cloud-deployment changes |
| **Operations** | incomplete scheduled governance runs, missing evidence, weak incident traceability |

## Failure scenarios

The same system is exercised against intentionally different failure classes.

| Scenario | Failure mode | Control that catches it | Result |
|---|---|---|---|
| **Vendor A** | healthy reference | complete governance path | eligible for staged promotion |
| **Vendor B** | `device_risk_score` missingness rises from **3.14%** to **22.00%** | data contract + Great Expectations | **BLOCK + quarantine** |
| **Vendor C** | contract-valid feature/prediction shift | PSI + KS drift governance | **CRITICAL → REJECT** |
| **Vendor D** | aggregate-stable subgroup degradation | fairness + SHAP-supported investigation | **FAIRNESS FAIL → REJECT** |
| **Vendor E** | supported intersection degrades while single axes avoid blocking FAIL | intersectional fairness + proxy-risk screening | **INTERSECTION FAIL** |

These thresholds are project engineering heuristics for the synthetic fixture, not legal or regulatory standards.

## Evidence-backed release path

```text
incoming batch
    |
    v
data quality
    |
    v
drift
    |
    v
fairness + explainability
    |
    v
governance decision + evidence integrity
    |
    v
STAGING -> SHADOW -> CANARY -> PRODUCTION
              |          |
              +----------+----> STAGING (rollback)
```

A candidate cannot jump directly from `CANDIDATE` to `PRODUCTION`.

## Key verified outcomes

| Boundary | Verified result |
|---|---:|
| Healthy ROC-AUC | **0.8025** |
| Vendor B incident ROC-AUC | **0.7329** |
| Vendor C prediction PSI / KS | **0.2379 / 0.1863** |
| Vendor D demographic-parity ratio | **0.7480** |
| Vendor E intersection demographic-parity ratio | **0.7479** |
| Healthy canary path | **10% → 25% → 50% → 100% → PRODUCTION** |
| Degraded canary path | **rollback to STAGING** |
| Vendor B decision flips | **2,500 / 15,000 (16.67%)** |
| Phase 13 root-cause completion | **690 min against 2,880 min project SLA** |

Current v1.0.0 verification:

- Ruff, Black, mypy, compile checks: **PASS**
- full pytest suite: **118 passed**
- Terraform format/validation: **PASS**
- container build/smoke: **PASS**
- Gitleaks: **PASS**
- Trivy filesystem/IaC checks: **PASS**
- architecture source/render validation: **PASS**

## Serving and release controls

The approved model is exposed through FastAPI:

```text
GET  /health
GET  /ready
POST /predict
POST /batch-predict
GET  /model
GET  /metrics
```

Release gates evaluate request volume, error rate, p95 latency, and mean risk-output delta. A failed release gate returns the candidate to `STAGING` with an auditable reason.

## Scheduled governance

The monitoring layer runs the verified control path as a dependency-ordered, fail-closed task graph.

It records:

- task status and attempts;
- configured evidence paths;
- SHA-256 evidence hashes;
- a run manifest;
- a JSONL event log.

`automatic_retraining=false` and `automatic_promotion=false` remain explicit safety boundaries.

## CI/CD and cloud boundary

Pull requests exercise:

```text
Ruff / Black / mypy / compile
        +
current release verification
        +
Gitleaks / Trivy
        +
Docker build + smoke
        +
Terraform fmt + validate
```

The cloud design uses GitHub OIDC, ECR, ECS/Fargate, ALB, and Terraform.

Cloud mutation is disabled by default:

```text
AWS_DEPLOY_ENABLED=false
```

The repository validates the delivery architecture; it does not claim that v1.0.0 is actively deployed to a production AWS environment.

## Quick start

### Requirements

- Python **3.12**
- `make`
- Terraform for infrastructure validation
- Docker for container smoke testing
- Graphviz only if you want to regenerate SVG architecture assets

### Install

```bash
git clone https://github.com/Parmodk2310/CreditScorev4-ML-Governance.git
cd CreditScorev4-ML-Governance

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Verify

```bash
make quality
make release-verify
make phase7-terraform
python -m pytest -q
```

### Run the API

```bash
python scripts/verify_phase1.py
python scripts/serve_model.py --host 0.0.0.0 --port 8000
```

## Repository map

```text
.
├── .github/workflows/        # quality, security, monitoring, image, gated deployment
├── configs/                  # versioned historical/control contracts
├── contracts/                # input data contract
├── data/                     # generated evidence, audit, registry, release, quarantine paths
├── docker/                   # serving/container/observability assets
├── docs/                     # case study, governance, validation, evidence, diagrams, history
├── infra/terraform/          # AWS ECR/ECS/Fargate/ALB infrastructure
├── models/                   # generated model lifecycle locations
├── ops/                      # repository operational policy
├── scripts/                  # verification, analysis, monitoring, serving, release tooling
├── src/creditscore/          # application and governance implementation
└── tests/                    # unit, integration, governance, serving, release, operations tests
```

## Review paths

| Reviewer | Start here |
|---|---|
| **Recruiter / hiring manager** | [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) → [`docs/REPRODUCIBLE_DEMO.md`](docs/REPRODUCIBLE_DEMO.md) |
| **Senior ML / MLOps engineer** | [`ARCHITECTURE.md`](ARCHITECTURE.md) → [`docs/TECHNICAL_DEEP_DIVE.md`](docs/TECHNICAL_DEEP_DIVE.md) → `src/` + `tests/` |
| **Model governance / validation** | [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) → [`docs/MODEL_VALIDATION_REPORT.md`](docs/MODEL_VALIDATION_REPORT.md) → [`docs/GOVERNANCE_POLICY.md`](docs/GOVERNANCE_POLICY.md) |
| **Evidence / reproducibility** | [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md) → `make release-verify` |
| **Architecture figures** | [`docs/ARCHITECTURE_FIGURES.md`](docs/ARCHITECTURE_FIGURES.md) |
| **Historical implementation evolution** | [`docs/phases/`](docs/phases/README.md) |

## Scope and non-claims

CreditScoreV4 demonstrates production-oriented controls in a synthetic environment.

It does **not** claim:

- a real banking production incident;
- real customer/applicant data;
- regulatory certification or legal compliance;
- causal conclusions from SHAP or fairness metrics;
- active production AWS deployment;
- production paging/on-call integration;
- automatic retraining or automatic promotion.

See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) for the complete boundary.

## Release

Current stable release: **v1.0.0**

See [`CHANGELOG.md`](CHANGELOG.md) and the GitHub Releases page for release history.

## License

MIT — see [`LICENSE`](LICENSE).
