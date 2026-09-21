# Reproducibility Guide

## Purpose

This guide defines a short, repeatable verification path through the complete
governance flow.

Run from the repository root with the Python 3.12 virtual environment active.

## Setup

```bash
python -m pip install -e ".[dev]" -c constraints.lock
```

## 1. Incident reproduction

```bash
python scripts/verify_phase1.py
```

Expected observation: healthy Vendor A is the reference, the same saved model is evaluated
after Vendor B migration, and AUC/missingness degrade.

Evidence: `data/evidence/phase1/`

## 2. Data-quality block

```bash
python scripts/verify_phase2.py
```

Expected observation: Vendor A passes, Vendor B is blocked, and failed data/evidence is
preserved rather than silently accepted.

## 3. Contract-valid drift

```bash
python scripts/verify_phase3.py
```

Expected observation: Vendor C passes data quality but creates critical feature/prediction
drift.

Evidence: `data/evidence/phase3/drift_report.json`

## 4. Aggregate-stable fairness failure

```bash
python scripts/verify_phase4.py
```

Expected observation: Vendor D passes quality, aggregate drift stays stable, fairness fails,
and SHAP supports investigation rather than causal claims.

## 5. Governance decision

```bash
python scripts/verify_phase5.py
```

Expected observation:

- healthy -> `APPROVE -> STAGING`
- Vendor C -> `REJECT` because drift blocks
- Vendor D -> `REJECT` because fairness blocks
- evidence hashes and audit records are verified

## 6. Safe release

```bash
python scripts/verify_phase6.py
```

Expected observation: FastAPI endpoint checks, `STAGING -> SHADOW -> CANARY`, the
10/25/50/100% checkpoints, healthy promotion to `PRODUCTION`, and degraded
rollback to `STAGING`.

Evidence: `data/evidence/phase6/phase6_release_report.json`

## 7. Delivery safety

```bash
python scripts/verify_phase7.py
```

Expected observation: GitHub Actions quality/security/image/deploy separation, Terraform
ECS/Fargate architecture, and the default-disabled AWS deployment gate.

## 8. Evidence contract

```bash
python scripts/verify_phase8.py
```

Evidence: `data/evidence/phase8/reviewer_evidence_manifest.json`

## 9. Business-impact evidence

```bash
python scripts/analyze_business_impact.py
python scripts/verify_phase9.py
```

Expected observation: the same 15,000 synthetic applicants and labels are scored under
healthy and Vendor B inputs. Approval rises from 73.91% to 78.60% and approved
30-day default rises from 21.80% to 26.37%.

## 10. Root-cause ablation

```bash
python scripts/analyze_root_cause.py
python scripts/verify_phase10.py
```

Expected observation: semantic migration drives the larger AUC loss, elevated missingness
drives the larger approval inflation, while elevated missingness interacting with the fitted median preprocessing path contributes materially to
the measured synthetic incident behavior. q75 is a diagnostic validation candidate only; Vendor B
remains blocked and production preprocessing is unchanged.

## 11. Scheduled monitoring orchestration

```bash
python scripts/run_monitoring_cycle.py --run-id demo-run
python scripts/verify_phase11.py
```

Expected observation: Phase 11 wraps the existing governance controls in a dependency-ordered
scheduled run. Each task must succeed and produce its configured evidence.
Failures block dependent tasks, the run fails closed, and evidence hashes are
recorded in the monitoring manifest.

Confirm that automatic retraining and automatic promotion remain
disabled; the scheduler cannot bypass the Phase 5 governance decision or Phase
6 release state machine.

Evidence:

- `data/evidence/phase11/monitoring_run.json`
- `data/evidence/phase11/monitoring_events.jsonl`

## 12. Intersectional fairness and proxy-risk evidence

```bash
python scripts/analyze_fairness_proxy.py
python scripts/verify_phase12.py
```

Expected observation: Vendor E preserves protected attributes and labels while shifting only
three non-protected model inputs for the supported `female|group_c`
intersection. Data quality passes and aggregate drift remains STABLE. The
single axes avoid blocking FAIL, but the intersection fails.

Expected observation: demographic-parity ratio
0.7479, equal-opportunity difference 0.1956, equalized-odds difference 0.2600,
and false-approval-rate difference 0.2600.

The proxy-review priorities are:
`device_risk_score`, `credit_utilization`, and
`bank_transaction_risk`. Association plus SHAP influence is treated as a
screening signal, not proof of causality or unlawful proxy use.

## Complete release verification

```bash
make quality
make release-verify
```

The commands above are the stable release-level interface. The numbered steps remain available when evidence for an individual control needs to be regenerated or inspected.

## Phase 13 — incident SLA and alert evidence

```bash
make phase13-analyze
python scripts/verify_phase13.py
make phase13-test
```

Expected deterministic root-cause completion: `690` minutes (`11h30m`) against
the configured `2880` minute (`48h`) project SLA.
