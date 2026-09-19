# Limitations and Non-Claims

CreditScoreV4 ML Governance intentionally uses a constrained synthetic
environment so failure modes and governance behavior are reproducible.

## Data

- Data is synthetic.
- The project does not process real applicant PII.
- Synthetic groups are constructed for deterministic governance testing.
- Results are not evidence about any real lending population.

## Model

- The model is not validated for real credit decisioning.
- Thresholds are project assumptions.
- Reported metrics describe generated project fixtures only.
- No external validation population is claimed.

## Fairness

- Fairness metrics are synthetic governance signals.
- They do not establish legal fairness, non-discrimination, or regulatory conformity.
- SHAP is explanatory/investigative evidence, not causal proof.

## Governance

- Promotion thresholds are engineering heuristics.
- The registry and audit implementation are project-owned.
- The project does not claim regulatory compliance.
- The repository is not a substitute for independent model validation,
  compliance review, or legal review.

## Serving and release

- Shadow/canary behavior is exercised through deterministic controlled simulations/tests.
- It is not equivalent to large-scale live production traffic mirroring.
- Performance under high concurrency has not been established by v0.7.0.
- Multi-region resilience and disaster recovery are outside the current scope.

## Cloud

- Terraform defines and validates an AWS ECS/Fargate path.
- Terraform validation is not proof that the stack is deployed in a live production account.
- AWS mutation is disabled by default.

## Intended interpretation

Correct: a production-style synthetic engineering case study demonstrating
layered ML governance and release controls.

Incorrect: a real bank production system or certified regulatory-compliance
platform.
