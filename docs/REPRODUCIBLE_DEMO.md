# Reproducible Demo

## Goal

This walkthrough gives a reviewer a short, repeatable path through the complete
governance story.

Run from the repository root with the Python 3.12 virtual environment active.

## Setup

```bash
python -m pip install -e ".[dev]"
```

## 1. Incident reproduction

```bash
python scripts/verify_phase1.py
```

Explain: healthy Vendor A is the reference, the same saved model is evaluated
after Vendor B migration, and AUC/missingness degrade.

Evidence: `data/evidence/phase1/`

## 2. Data-quality block

```bash
python scripts/verify_phase2.py
```

Explain: Vendor A passes, Vendor B is blocked, and failed data/evidence is
preserved rather than silently accepted.

## 3. Contract-valid drift

```bash
python scripts/verify_phase3.py
```

Explain: Vendor C passes data quality but creates critical feature/prediction
drift.

Evidence: `data/evidence/phase3/drift_report.json`

## 4. Aggregate-stable fairness failure

```bash
python scripts/verify_phase4.py
```

Explain: Vendor D passes quality, aggregate drift stays stable, fairness fails,
and SHAP supports investigation rather than causal claims.

## 5. Governance decision

```bash
python scripts/verify_phase5.py
```

Point out:

- healthy -> `APPROVE -> STAGING`
- Vendor C -> `REJECT` because drift blocks
- Vendor D -> `REJECT` because fairness blocks
- evidence hashes and audit records are verified

## 6. Safe release

```bash
python scripts/verify_phase6.py
```

Point out FastAPI endpoint checks, `STAGING -> SHADOW -> CANARY`, the
10/25/50/100% checkpoints, healthy promotion to `PRODUCTION`, and degraded
rollback to `STAGING`.

Evidence: `data/evidence/phase6/phase6_release_report.json`

## 7. Delivery safety

```bash
python scripts/verify_phase7.py
```

Explain GitHub Actions quality/security/image/deploy separation, Terraform
ECS/Fargate architecture, and the default-disabled AWS deployment gate.

## 8. Reviewer evidence

```bash
python scripts/verify_phase8.py
```

Evidence: `data/evidence/phase8/reviewer_evidence_manifest.json`

## 9. Business-impact evidence

```bash
python scripts/analyze_business_impact.py
python scripts/verify_phase9.py
```

Explain: the same 15,000 synthetic applicants and labels are scored under
healthy and Vendor B inputs. Approval rises from 73.91% to 78.60% and approved
30-day default rises from 21.80% to 26.37%.

## 10. Root-cause ablation

```bash
python scripts/analyze_root_cause.py
python scripts/verify_phase10.py
```

Explain: semantic migration drives the larger AUC loss, elevated missingness
drives the larger approval inflation, and the fitted median pathway amplifies
the synthetic incident. q75 is a diagnostic validation candidate only; Vendor B
remains blocked and production preprocessing is unchanged.

For the complete release gate:

```bash
make quality
make phase10-verify
```

## 3–5 minute speaking sequence

```text
0:00  Problem and healthy baseline
0:30  Vendor B: quality failure
1:00  Vendor C: contract-valid drift
1:30  Vendor D: aggregate-stable fairness failure
2:00  Evidence-backed governance decisions
2:45  Shadow/canary/rollback lifecycle
3:15  Business impact and decision flips
3:40  Root-cause ablation + q75 diagnostic candidate
4:20  CI/security/Terraform fail-closed delivery
4:45  Limitations and production-hardening path
```

Useful close:

> No single control is expected to detect every ML failure. The architecture
> uses defense in depth so data quality, drift, fairness, governance, and release
> controls independently stop unsafe progression at the correct layer.
