# CreditScoreV4 Documentation Guide

This directory contains the current system documentation and the historical
Phase 1–13 implementation record.

The repository is best understood as **one integrated ML-governance system**.
Phase numbers explain how the system evolved; they are not separate products or
the preferred navigation path for the current v1.x release.

## Recommended reading path

For a complete current-system review:

1. [Project README](../README.md) — problem, architecture, verified evidence, and scope
2. [Case Study](CASE_STUDY.md) — incident story, decisions, outcomes, and engineering rationale
3. [Architecture](../ARCHITECTURE.md) — system boundaries, control planes, serving, and delivery
4. [Technical Deep Dive](TECHNICAL_DEEP_DIVE.md) — implementation details and trade-offs
5. [Model Validation Report](MODEL_VALIDATION_REPORT.md) — deterministic model and governance evidence
6. [Evidence Index](EVIDENCE_INDEX.md) — commands and artifact locations
7. [Limitations](LIMITATIONS.md) — explicit non-claims and production gaps

## Choose a path by audience

### Recruiter or hiring manager

Start with:

- [Project README](../README.md)
- [Case Study](CASE_STUDY.md)
- [Architecture Figures](ARCHITECTURE_FIGURES.md)
- [Project Evidence Screenshots](assets/screenshots/README.md)

This path explains what problem the project solves, what controls it implements,
and what the verified synthetic evidence demonstrates.

### ML / MLOps / platform engineer

Use:

- [Architecture](../ARCHITECTURE.md)
- [Technical Deep Dive](TECHNICAL_DEEP_DIVE.md)
- [Governance Policy](GOVERNANCE_POLICY.md)
- [Monitoring Plan](MONITORING_PLAN.md)
- [Evidence Index](EVIDENCE_INDEX.md)
- [Reproducible Demo](REPRODUCIBLE_DEMO.md)

### Governance or model-risk reviewer

Use:

- [Model Card](MODEL_CARD.md)
- [Model Validation Report](MODEL_VALIDATION_REPORT.md)
- [Governance Policy](GOVERNANCE_POLICY.md)
- [Monitoring Plan](MONITORING_PLAN.md)
- [Evidence Index](EVIDENCE_INDEX.md)
- [Limitations](LIMITATIONS.md)

### Reproduce the implementation

Start with:

- [Reproducible Demo](REPRODUCIBLE_DEMO.md)
- [Evidence Index](EVIDENCE_INDEX.md)
- [Maintenance Policy](MAINTENANCE.md)

The stable cumulative verification interface is:

```bash
make quality
make release-verify
make phase7-terraform
```

## Historical phase record

The numbered phase documents are preserved under [`docs/phases/`](phases/README.md).

They document implementation history from deterministic incident reproduction
through evidence contracts, business-impact analysis, root-cause ablation,
scheduled governance, intersectional fairness, and incident-SLA evidence.

Use them when you need milestone-specific design history. For the current
system, prefer the reading paths above.

## Current release boundary

The current stable public release is **v1.0.1** and the repository is
feature-frozen on the v1.x line.

Current documentation describes:

- deterministic synthetic data and failure scenarios;
- independent data-quality, drift, fairness, and evidence-integrity controls;
- governed model registry transitions;
- FastAPI serving with artifact-integrity verification;
- shadow/canary rollout and rollback;
- Prometheus/Grafana observability;
- GitHub Actions, security scanning, Docker, Terraform, and gated AWS delivery;
- scheduled fail-closed monitoring;
- business-impact and root-cause evidence;
- intersectional fairness and proxy-risk review;
- deterministic incident-SLA evidence.

It does **not** claim real lending production use, regulatory certification,
live production paging, automatic retraining/promotion, or active production
AWS infrastructure.
