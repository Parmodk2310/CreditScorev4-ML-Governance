# v1.x Maintenance Policy

CreditScoreV4 ML Governance is feature-frozen after v1.0.1.

## Accepted changes

- correctness and bug fixes;
- security and supply-chain fixes;
- reproducibility and dependency maintenance;
- CI, test, coverage, container, and infrastructure-validation hardening;
- documentation corrections that keep claims synchronized with executable behavior.

## Out of scope for v1.x

- new numbered implementation phases;
- new model families added only for breadth;
- automatic retraining or automatic promotion;
- unrelated platform additions such as Kafka, Kubernetes, Airflow, or MLflow without a new design decision;
- claims of real lending production use, regulatory certification, or active production AWS infrastructure without corresponding evidence.

A future expansion should start with a new design decision and version boundary rather than silently extending the v1.x case study.
