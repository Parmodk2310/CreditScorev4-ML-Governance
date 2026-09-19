<p align="center">
  <h1 align="center">CreditScoreV4 ML Governance</h1>
  <p align="center">
    Evidence-backed ML governance for data quality, drift, fairness, model promotion,
    progressive delivery, rollback, and fail-closed AWS deployment.
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
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12" />
</p>

> **A credit-risk model can be accurate and still be unsafe to promote.**
> CreditScoreV4 demonstrates how an ML platform can detect upstream failures,
> require evidence before promotion, and progressively release an approved model
> without silently bypassing governance controls.

This repository implements a **synthetic ML governance system**. It
uses deterministic synthetic data and controlled failure scenarios so the
complete lifecycle can be reproduced without claiming a real banking incident,
live lending system, or regulatory certification.

<p align="center">
  <img src="docs/assets/diagrams/phase1-7-end-to-end.svg"
       alt="CreditScoreV4 end-to-end ML governance architecture"
       width="100%" />
</p>

## Why CreditScoreV4

Many ML projects end after model training and evaluation. In a production ML
system, that is only the beginning.

CreditScoreV4 focuses on the controls between **a trained model** and
**production traffic**:

- **Valid schema does not mean healthy data.**
- **Healthy aggregate metrics do not mean healthy subgroup outcomes.**
- **A governance approval does not mean a model should receive 100% traffic immediately.**
- **A deployment pipeline should fail closed when evidence or configuration is missing.**

The project connects those concerns into one reproducible control path:

```text
Incoming data
    |
    v
Data quality
    |
    v
Drift
    |
    v
Fairness + explainability
    |
    v
Governance policy
    |
    v
Evidence verification
    |
    v
Model registry
    |
    v
STAGING -> SHADOW -> CANARY -> PRODUCTION
               \          \
                \-----------> STAGING (rollback)
```

## Failure scenarios

The repository deliberately separates failure modes that can look similar from
the outside but require different controls.

| Scenario | What changes | What catches it | Outcome |
|---|---|---|---|
| **Healthy Vendor A** | Reference behavior | Full governance path | Eligible for promotion |
| **Vendor B — data-quality failure** | `device_risk_score` nulls rise from **3.14%** to **22.00%** | Data contract + Great Expectations | **BLOCK + quarantine** |
| **Vendor C — contract-valid drift** | Schema remains valid while feature/prediction distributions shift | PSI + KS drift governance | **CRITICAL → REJECT** |
| **Vendor D — subgroup stress** | Aggregate drift remains stable while subgroup outcomes degrade | Fairlearn + SHAP-supported review | **FAIRNESS FAIL → REJECT** |

The baseline model records **ROC-AUC 0.8025**. Under the Vendor B incident
fixture, ROC-AUC falls to **0.7329**. Vendor C produces **prediction PSI 0.2379**
and **KS 0.1863**. Vendor D reaches a **demographic-parity ratio of 0.7480**,
a **selection-rate difference of 0.1860**, and an **equalized-odds difference
of 0.2269**.

These thresholds and scenarios are project governance heuristics for the
synthetic case study; they are not legal or regulatory standards.

## Failure scenarios and controls

### Data-quality governance

Incoming batches are checked against a versioned contract and Great
Expectations rules. Material violations are blocked before downstream model
governance and written to quarantine/evidence paths.

### Drift governance

Contract-valid data is compared with the healthy reference using feature and
prediction drift checks. This demonstrates why schema validation and
distribution monitoring are separate controls.

### Fairness and explainability

Protected attributes are used for evaluation scenarios and excluded from model
features. Fairness checks can reject a candidate even when aggregate drift is
stable, while SHAP explains the non-protected proxy features driving the
stressed scenario.

### Evidence-backed promotion

Performance, calibration, data quality, drift, fairness, and evidence integrity
are evaluated by a configurable policy engine. Promotion is a deterministic
governance decision, not a manual deployment shortcut.

### Governed model registry

The registry enforces explicit lifecycle transitions:

```text
REGISTERED -> CANDIDATE -> STAGING -> SHADOW -> CANARY -> PRODUCTION
                       \-> REJECTED
```

Direct `CANDIDATE -> PRODUCTION` promotion is illegal.

### Progressive delivery and rollback

An approved staged candidate moves through shadow evaluation and deterministic
canary checkpoints:

```text
10% -> 25% -> 50% -> 100%
```

Release gates evaluate request volume, errors, latency, and mean risk-output
delta. A degraded canary returns the candidate to `STAGING` with an auditable
rollback reason.

<p align="center">
  <img src="docs/assets/diagrams/release-state.svg"
       alt="CreditScoreV4 governed release-state machine"
       width="900" />
</p>

### Serving and observability

The approved model is exposed through FastAPI:

```text
GET  /health
GET  /ready
POST /predict
POST /batch-predict
GET  /model
GET  /metrics
```

The serving layer exposes Prometheus-compatible operational metrics and model
metadata, including artifact traceability.

### CI/CD and cloud controls

Pull requests exercise quality, governance, security, container, and
infrastructure checks before merge:

```text
Pull request
   |
   +--> Ruff / Black / mypy / compile
   +--> cumulative Phase 8 verification
   +--> Gitleaks
   +--> Trivy filesystem + Terraform scan
   +--> Docker build + smoke test
   `--> Terraform fmt + validate
```

External GitHub Actions are pinned to immutable commit SHAs.

The cloud path uses **GitHub OIDC → AWS → ECR → ECS/Fargate → ALB**, managed by
Terraform. Cloud mutation remains **fail-closed by default** with
`AWS_DEPLOY_ENABLED=false`.

## Verification status

The repository currently verifies the following boundaries:

| Verification | Result |
|---|---:|
| Ruff / Black / mypy / compile | **PASS** |
| Phase 1–7 regression suite | **63 passed** |
| Phase 8 evidence-contract suite | **6 passed** |
| Terraform format + validation | **PASS** |
| Container build + smoke test | **PASS** |
| Gitleaks | **PASS** |
| Trivy filesystem / IaC scan | **PASS** |
| Workflow Action pinning contract | **PASS** |

The FastAPI `TestClient` path currently emits a non-blocking Starlette
deprecation warning; it does not change the verified Phase 6 outcomes.

## Quick start

### Prerequisites

- Python **3.12**
- `make`
- Terraform for infrastructure validation
- Docker for container smoke testing

### Install

```bash
git clone https://github.com/Parmodk2310/CreditScorev4-ML-Governance.git
cd CreditScorev4-ML-Governance

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Verify the full local governance path

```bash
make quality
make phase8-verify
make phase7-terraform
```

### Run focused phase verification

```bash
python scripts/verify_phase1.py
python scripts/verify_phase2.py
python scripts/verify_phase3.py
python scripts/verify_phase4.py
python scripts/verify_phase5.py
python scripts/verify_phase6.py
python scripts/verify_phase7.py
python scripts/verify_phase8.py
```

### Run the test suite

```bash
python -m pytest -q
```

## Architecture

The system is split into four control planes:

| Plane | Responsibility |
|---|---|
| **Data / model risk** | Data quality, drift, fairness, explainability, performance and calibration |
| **Governance** | Policy evaluation, evidence integrity, registry transitions and audit records |
| **Release** | FastAPI serving, shadow evaluation, deterministic canary routing and rollback |
| **Delivery** | CI/security checks, immutable Action references, Terraform and gated AWS deployment |

For implementation details, see
[`ARCHITECTURE.md`](ARCHITECTURE.md) and
[`docs/TECHNICAL_DEEP_DIVE.md`](docs/TECHNICAL_DEEP_DIVE.md).

## Documentation map

You do not need to read every document to understand the project.

| If you are... | Start here |
|---|---|
| **Overview** | README → [`CASE_STUDY.md`](docs/CASE_STUDY.md) → architecture diagrams |
| **ML / MLOps engineer** | [`ARCHITECTURE.md`](ARCHITECTURE.md) → [`TECHNICAL_DEEP_DIVE.md`](docs/TECHNICAL_DEEP_DIVE.md) → source/tests |
| **Governance review** | [`MODEL_CARD.md`](docs/MODEL_CARD.md) → [`MODEL_VALIDATION_REPORT.md`](docs/MODEL_VALIDATION_REPORT.md) → [`GOVERNANCE_POLICY.md`](docs/GOVERNANCE_POLICY.md) |
| **Reproducing the project** | [`REPRODUCIBLE_DEMO.md`](docs/REPRODUCIBLE_DEMO.md) → [`EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md) |
| **Reviewing operational limits** | [`MONITORING_PLAN.md`](docs/MONITORING_PLAN.md) → [`LIMITATIONS.md`](docs/LIMITATIONS.md) |

### Core documentation

- [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) — problem, incidents, engineering decisions, and outcomes
- [`docs/TECHNICAL_DEEP_DIVE.md`](docs/TECHNICAL_DEEP_DIVE.md) — implementation-level architecture and control flow
- [`docs/GOVERNANCE_POLICY.md`](docs/GOVERNANCE_POLICY.md) — executable promotion/blocking policy
- [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) — model purpose, inputs, intended use, and constraints
- [`docs/MODEL_VALIDATION_REPORT.md`](docs/MODEL_VALIDATION_REPORT.md) — performance and validation evidence
- [`docs/MONITORING_PLAN.md`](docs/MONITORING_PLAN.md) — operational monitoring and escalation plan
- [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md) — generated evidence and reviewer map
- [`docs/REPRODUCIBLE_DEMO.md`](docs/REPRODUCIBLE_DEMO.md) — commands for reproducing the verified scenarios
- [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) — explicit project boundaries and non-claims

Repository security and contribution controls are documented in
[`SECURITY.md`](SECURITY.md), [`CONTRIBUTING.md`](CONTRIBUTING.md),
[`docs/ACTION_PINNING.md`](docs/ACTION_PINNING.md), and
[`docs/BRANCH_PROTECTION.md`](docs/BRANCH_PROTECTION.md).

## Repository boundaries

CreditScoreV4 is intentionally scoped.

It **does demonstrate**:

- deterministic synthetic incident reproduction;
- independent data-quality, drift, fairness, and release controls;
- evidence-backed model promotion and rejection;
- model registry/state-machine behavior;
- FastAPI serving and operational metrics;
- progressive shadow/canary release with rollback;
- CI/security/container/Terraform verification;
- a gated AWS ECS/Fargate deployment architecture.

It **does not claim**:

- a real bank production incident;
- real applicant/customer data;
- regulatory certification or legal compliance;
- causal conclusions from SHAP or fairness metrics;
- a currently active production AWS environment;
- a managed MLflow/Airflow/Kubernetes platform.

## Project structure

```text
.
├── .github/workflows/        # quality, security, image and gated deployment
├── configs/                  # versioned phase/governance configuration
├── data/evidence/            # generated governance/release evidence
├── docker/phase6/            # serving + local observability stack
├── docs/                     # governance, validation and operations documentation
├── infra/terraform/          # AWS ECR/ECS/Fargate/ALB infrastructure
├── models/baseline/          # deterministic persisted baseline artifact
├── scripts/                  # phase verification and release/deployment tooling
├── src/creditscore/          # application and governance implementation
└── tests/                    # quality, governance, serving, release and automation tests
```

## Contributing

Contributions should preserve the project's evidence-first and fail-closed
governance boundaries. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

For security issues, follow [`SECURITY.md`](SECURITY.md) rather than opening a
public vulnerability issue.

## License

Released under the [`MIT License`](LICENSE).

---

**Primary focus:** ML governance · model risk · safe release engineering · MLOps · AWS/Terraform
