# Model Validation Report

## Scope

This report summarizes the deterministic validation scenarios implemented by
CreditScoreV4 ML Governance. It is an engineering validation artifact for a
synthetic case study, not an independent validation report for a real financial
institution.

The executable verification scripts and generated evidence remain the source of
truth.

## Validation strategy

```text
Vendor A -> healthy reference
Vendor B -> data-quality degradation
Vendor C -> contract-valid distribution drift
Vendor D -> aggregate-stable subgroup/fairness stress
```

The project intentionally uses progressively subtler failure modes to show why
one control cannot detect every class of ML failure.

## Phase 1 — healthy reference and incident reproduction

The same trained baseline model is evaluated before and after the Vendor B
migration so the comparison isolates the upstream change rather than mixing it
with model retraining.

| Metric | Healthy Vendor A | Vendor B |
|---|---:|---:|
| ROC-AUC | `0.8025` | `0.7329` |
| AUC drop | — | `0.0696` |
| `device_risk_score` null rate | `3.14%` | `22.00%` |

Evidence: `data/evidence/phase1/`

## Phase 2 — data-quality validation

Expected behavior:

- Vendor A: `PASS`
- Vendor B: `BLOCK`

The blocking scenario is tied to material `device_risk_score` missingness and
produces machine-readable quality evidence plus quarantine output.

Evidence: `data/evidence/phase2/`

## Phase 3 — contract-valid drift

Vendor C is deliberately designed to pass the Phase 2 data-quality contract
while changing model-relevant distributions.

Verified case-study outcome:

- data-quality gate: `PASS`
- aggregate drift: `CRITICAL`
- prediction PSI: `0.2379`
- prediction KS: `0.1863`
- required critical features include `device_risk_score` and
  `bank_transaction_risk`

Evidence: `data/evidence/phase3/`

## Phase 4 — fairness and explainability

Vendor D is designed so aggregate drift remains stable while synthetic
`group_c` creates subgroup stress.

Verified case-study outcome:

- Phase 2: `PASS`
- aggregate drift: `STABLE`
- fairness governance: `FAIL`
- demographic parity ratio: `0.7480`
- selection-rate difference: `0.1860`
- equalized-odds difference: `0.2269`

SHAP is used as investigative evidence for proxy/model-input behavior. It is not
presented as causal proof.

Evidence: `data/evidence/phase4/`

## Phase 5 — governance validation

| Candidate | Decision | Registry state |
|---|---|---|
| healthy | `APPROVE` | `STAGING` |
| Vendor C | `REJECT` | `REJECTED` |
| Vendor D | `REJECT` | `REJECTED` |

Validation also covers evidence hashes, deterministic decision identity, audit
records, persistence, and illegal transition blocking.

Evidence: `data/evidence/phase5/`

## Phase 6 — serving and safe release

The service exposes `/health`, `/ready`, `/predict`, `/batch-predict`, `/model`,
and `/metrics`.

Healthy path:

`STAGING -> SHADOW -> CANARY -> PRODUCTION`

Degraded path:

`CANARY -> STAGING`

The healthy path exercises 10%, 25%, 50%, and 100% canary shares.

Evidence: `data/evidence/phase6/phase6_release_report.json`

## Phase 7 — delivery controls

Validation covers Python quality checks, cumulative tests, Docker smoke
behavior, Gitleaks, Trivy, Terraform format/validation, ECR/ECS/Fargate
infrastructure contracts, and fail-closed deployment behavior.

Cloud deployment remains disabled by default.

Evidence: `data/evidence/phase7/release_manifest.json`

## Phase 8 — reviewer/evidence contracts

Phase 8 verifies that reviewer-facing documentation, policy thresholds,
registry transitions, release controls, deployment defaults, and generated
evidence remain consistent with executable configuration.

Evidence: `data/evidence/phase8/reviewer_evidence_manifest.json`

## Phase 9 — business-impact validation

The same 15,000 synthetic applicants and outcome labels are preserved while
healthy and Vendor B inputs are compared. Verified evidence includes 2,500
decision flips, approval-rate movement from 73.91% to 78.60%, and an
approved-cohort 30-day default-rate increase from 21.80% to 26.37%.

Evidence: `data/evidence/phase9/`

## Phase 10 — root-cause validation

Controlled ablation separates semantic migration from elevated missingness.
The q75 counterfactual remains diagnostic-only; Vendor B stays blocked and
production preprocessing remains unchanged.

Evidence: `data/evidence/phase10/`

## Phase 11 — orchestration validation

The scheduled governance run verifies dependency ordering, fail-closed task
behavior, required evidence production, SHA-256 evidence capture, and disabled
automatic retraining/promotion.

Evidence: `data/evidence/phase11/`

## Phase 12 — intersectional fairness and proxy-risk validation

Vendor E passes data quality and keeps aggregate drift STABLE while the
supported `female|group_c` intersection fails configured project fairness
thresholds. Proxy-risk screening combines statistical association with SHAP
model influence and remains investigative evidence rather than causal or legal
proof.

Evidence: `data/evidence/phase12/`

## Phase 13 — incident-operations validation

The deterministic Vendor B incident timeline records 184 minutes to detection,
185 minutes to synthetic alert evidence, 186 minutes to governance block,
360 minutes to triage, and 690 minutes to root-cause completion. The configured
root-cause project SLA is 2,880 minutes (48 hours) and passes.

Phase 13 additionally verifies cross-phase evidence hashes, timeline ordering,
timezone-aware timestamps, synthetic alert scope, and disabled live paging,
automatic retraining, and automatic promotion.

Evidence: `data/evidence/phase13/`

## Validation conclusion

The validation results show layered controls: obvious upstream failure is stopped
by data quality, contract-valid shift is caught by drift monitoring,
aggregate-stable subgroup stress is caught by fairness governance, evidence
becomes a promotion decision, approved candidates still pass release-health
controls, and cloud mutation requires explicit enablement.

This conclusion applies to the synthetic engineering case study only.
