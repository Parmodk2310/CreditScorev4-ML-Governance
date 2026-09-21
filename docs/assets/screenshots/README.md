# CreditScoreV4 ML Governance — Project Evidence

These screenshots are captured from the CreditScoreV4 ML Governance verification workflows, deterministic synthetic evidence pipeline, GitHub Actions, and release process.

> **Scope:** All evidence comes from the project's deterministic synthetic environment. It does **not** represent a real banking production incident, real applicant/customer data, regulatory certification, live production paging, or an active production AWS deployment.

## Evidence Index

| Evidence | Demonstrates |
|---|---|
| `01-incident-baseline.png` | Healthy baseline versus Vendor B model degradation |
| `02-data-quality-block.png` | Blocking data-quality governance and quarantine |
| `03-critical-drift.png` | Contract-valid critical feature/prediction drift |
| `04-fairness-shap.png` | Subgroup fairness governance and SHAP-supported investigation |
| `05-governance-decisions.png` | Evidence-backed model promotion/rejection decisions |
| `06-release-rollback.png` | Progressive shadow/canary release and deterministic rollback |
| `07-phase7-controls.png` | Automated delivery, security, container, and Terraform controls |
| `08-github-checks.png` | GitHub Actions quality, security, image, and infrastructure gates |
| `09-release-v070.png` | Historical v0.7.0 automated-delivery milestone |
| `10-phase8-evidence-contract.png` | Evidence contract, reviewer manifest, policy consistency, and traceability |
| `11-phase9-business-impact.png` | Decision and observed-outcome impact of the Vendor B incident |
| `12-phase10-root-cause.png` | Controlled root-cause ablation and remediation counterfactual evidence |
| `13-phase11-monitoring-orchestration.png` | Scheduled fail-closed governance orchestration and evidence manifest |
| `14-phase12-intersectional-fairness.png` | Intersectional fairness failure and proxy-risk review signals |
| `15-phase13-incident-sla.png` | Synthetic incident timeline, alerting, SLA evaluation, and cross-phase lineage |

### Recommended current-release screenshot

For the strongest recruiter-facing evidence set, also capture:

| Evidence | Demonstrates |
|---|---|
| `16-release-v101.png` | Current stable v1.0.1 hardening release and feature-freeze boundary |

The current stable release is **v1.0.1**. The older `09-release-v070.png` screenshot is useful as historical delivery evidence, but `16-release-v101.png` should be shown near the end of a portfolio walkthrough because it represents the current stable repository state.
