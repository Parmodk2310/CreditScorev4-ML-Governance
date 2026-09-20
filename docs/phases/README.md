# Engineering Evolution

The documents in this directory preserve the implementation history of
CreditScoreV4 ML Governance.

They are useful when reviewing how individual controls were introduced, but
they are **not the recommended starting point for understanding the current
system**.

For the current product-level view, start with:

1. [`../../README.md`](../../README.md)
2. [`../CASE_STUDY.md`](../CASE_STUDY.md)
3. [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md)
4. [`../TECHNICAL_DEEP_DIVE.md`](../TECHNICAL_DEEP_DIVE.md)
5. [`../MODEL_VALIDATION_REPORT.md`](../MODEL_VALIDATION_REPORT.md)
6. [`../EVIDENCE_INDEX.md`](../EVIDENCE_INDEX.md)
7. [`../LIMITATIONS.md`](../LIMITATIONS.md)

The stable current release verification command is:

```bash
make release-verify
```

The numbered phase targets remain available for historical reproducibility.

## Milestone history

| Milestone | Engineering focus |
|---|---|
| [Phase 1](PHASE1.md) | Deterministic baseline and Vendor B incident reproduction |
| [Phase 2](PHASE2.md) | Data-quality contracts, blocking, and quarantine |
| [Phase 3](PHASE3.md) | Contract-valid feature and prediction drift |
| [Phase 4](PHASE4.md) | Fairness governance and SHAP-supported investigation |
| [Phase 5](PHASE5.md) | Evidence-backed governance policy and model registry |
| [Phase 6](PHASE6.md) | FastAPI serving, shadow/canary release, and rollback |
| [Phase 7](PHASE7.md) | CI/security/container verification and gated AWS delivery |
| [Phase 8](PHASE8.md) | Reviewer evidence contracts and repository consistency |
| [Phase 9](PHASE9.md) | Business-impact and decision-transition evidence |
| [Phase 10](PHASE10.md) | Root-cause ablation and remediation counterfactuals |
| [Phase 11](PHASE11.md) | Scheduled fail-closed governance orchestration |
| [Phase 12](PHASE12.md) | Intersectional fairness and proxy-risk screening |
| [Phase 13](PHASE13.md) | Incident-response timeline, synthetic alerts, and SLA evidence |

## Current interpretation

The current repository should be reviewed as one ML-governance system rather
than as thirteen independent projects.

The phase documents explain how that system evolved. The current architecture,
release gate, limitations, and reviewer documentation define the active
repository boundary.
