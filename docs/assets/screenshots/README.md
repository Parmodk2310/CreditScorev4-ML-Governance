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


---

## Screenshot Gallery

Place the images under:

```text
docs/project-evidence/screenshots/
```

Then GitHub will render the following gallery automatically.

### Phase 1 — Incident Baseline

![Phase 1 incident baseline](screenshots/01-incident-baseline.png)

**What it proves:** the same trained model behaves differently after a controlled upstream Vendor B migration. The project reproduces a deterministic degradation rather than relying on a hypothetical incident.

---

### Phase 2 — Data-Quality Governance

![Phase 2 data-quality block](screenshots/02-data-quality-block.png)

**What it proves:** the data-quality layer detects the Vendor B contract violation, blocks unsafe progression, and writes quarantine/evidence artifacts.

---

### Phase 3 — Drift Governance

![Phase 3 critical drift](screenshots/03-critical-drift.png)

**What it proves:** schema-valid data can still be unsafe. PSI/KS and prediction-distribution monitoring detect critical distribution change even when the structural contract passes.

---

### Phase 4 — Fairness + SHAP

![Phase 4 fairness and SHAP](screenshots/04-fairness-shap.png)

**What it proves:** aggregate model behavior can hide subgroup degradation. Fairness evidence is paired with SHAP-supported investigation while protected attributes remain outside model inputs.

---

### Phase 5 — Governance Decisions

![Phase 5 governance decisions](screenshots/05-governance-decisions.png)

**What it proves:** promotion is evidence-backed and fail-closed. Healthy evidence can progress; critical drift or fairness failure causes rejection.

---

### Phase 6 — Safe Release + Rollback

![Phase 6 release rollback](screenshots/06-release-rollback.png)

**What it proves:** an approved candidate still goes through runtime safety controls. Shadow and progressive canary stages can promote a healthy candidate or roll a degraded candidate back to `STAGING`.

---

### Phase 7 — Delivery Controls

![Phase 7 controls](screenshots/07-phase7-controls.png)

**What it proves:** GitHub Actions, Docker, security scanning, Terraform, and fail-closed AWS deployment controls are part of the delivery boundary.

---

### GitHub Checks


**What it proves:** quality/governance, Terraform, security, and container gates are automated and visible in the repository review process.

---

### Historical v0.7.0 Delivery Release


**What it proves:** the project reached an explicit automated-delivery milestone before later governance and operational-evidence phases were added.

---

### Phase 8 — Evidence Contract & Traceability

![Phase 8 evidence contract](screenshots/10-phase8-evidence-contract.png)

**What it proves:** documentation claims are tied back to executable policy, generated evidence, registry transitions, release behavior, delivery controls, and a reviewer evidence manifest.

Key artifact:

```text
data/evidence/phase8/reviewer_evidence_manifest.json
```

---

### Phase 9 — Business Impact

![Phase 9 business impact](screenshots/11-phase9-business-impact.png)

**What it proves:** the Vendor B technical failure changes actual model decisions in the deterministic fixture.

Key evidence includes:

- healthy approval rate: **73.91%**
- incident approval rate: **78.60%**
- approval-rate change: **+4.69 percentage points**
- healthy approved-cohort default rate: **21.80%**
- incident approved-cohort default rate: **26.37%**
- decision flips: **2,500**
- newly approved applicants: **1,602**

These values are synthetic case-study measurements, not real lending outcomes.

---

### Phase 10 — Root Cause & Remediation Review

![Phase 10 root cause](screenshots/12-phase10-root-cause.png)

**What it proves:** a controlled 2×2 ablation separates semantic score migration from elevated missingness.

The evidence shows:

- semantic migration is the larger contributor to ROC-AUC degradation;
- elevated missingness is the larger contributor to approval inflation;
- the combined failure remains blocked;
- q75 is a diagnostic validation candidate only, not a production fix.

---

### Phase 11 — Scheduled Governance Orchestration

![Phase 11 monitoring orchestration](screenshots/13-phase11-monitoring-orchestration.png)

**What it proves:** existing governance controls can execute as one dependency-ordered, fail-closed monitoring cycle.

The run manifest records:

- run ID and source commit;
- task status and attempts;
- evidence SHA-256 hashes;
- fail-closed state;
- automatic retraining disabled;
- automatic promotion disabled.

Key artifacts:

```text
data/evidence/phase11/monitoring_run.json
data/evidence/phase11/monitoring_events.jsonl
```

---

### Phase 12 — Intersectional Fairness & Proxy Risk

![Phase 12 intersectional fairness](screenshots/14-phase12-intersectional-fairness.png)

**What it proves:** single-axis checks can avoid a blocking failure while a supported intersection fails materially.

Verified deterministic evidence includes:

- aggregate drift: **STABLE**
- `sex`: **PASS**
- `synthetic_demographic_group`: **WARNING**
- `female|group_c`: **FAIL**
- demographic-parity ratio: **0.7479**
- equal-opportunity difference: **0.1956**
- equalized-odds difference: **0.2600**

Proxy-review priority features include:

- `device_risk_score`
- `credit_utilization`
- `bank_transaction_risk`

These are review signals, not causal or legal conclusions.

---

### Phase 13 — Incident SLA & Operational Evidence

![Phase 13 incident SLA](screenshots/15-phase13-incident-sla.png)

**What it proves:** the system can generate a deterministic incident timeline, synthetic alert evidence, SLA evaluation, and cross-phase traceability.

Verified synthetic timeline metrics include:

- detection: **184 min**
- alert: **185 min**
- governance block: **186 min**
- triage: **360 min**
- root-cause completion: **690 min**
- root-cause project SLA: **≤ 2,880 min / 48h**
- SLA result: **PASS**

Live paging, automatic retraining, and automatic promotion remain disabled.

---

### Current Stable Release — v1.0.1

![v1.0.1 release](screenshots/16-release-v101.png)

**What it proves:** the repository reached a stable maintenance boundary with shared offline/online validation, model SHA verification before deserialization, a canonical decision policy, bounded Prometheus labels, sanitized serving errors, coverage reporting, observability validation, security/container/Terraform gates, and a v1.x functional-development freeze.

---

## Evidence Rules

Use screenshots only as a visual review layer. The authoritative evidence remains:

```text
configuration
→ source code
→ tests
→ generated evidence
→ CI/security/container/Terraform gates
→ tagged release
```

Do not describe screenshots as proof of a real production credit system. CreditScoreV4 is a **production-oriented ML-governance engineering case study built with deterministic synthetic data**.
