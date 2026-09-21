# Reproducible Demo

## Goal

This walkthrough provides a short, repeatable path through the complete
governance flow.

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

Explain: the same 15,000 synthetic applicants and labels are scored under
healthy and Vendor B inputs. Approval rises from 73.91% to 78.60% and approved
30-day default rises from 21.80% to 26.37%.

## 10. Root-cause ablation

```bash
python scripts/analyze_root_cause.py
python scripts/verify_phase10.py
```

Explain: semantic migration drives the larger AUC loss, elevated missingness
drives the larger approval inflation, while elevated missingness interacting with the fitted median preprocessing path contributes materially to
the measured synthetic incident behavior. q75 is a diagnostic validation candidate only; Vendor B
remains blocked and production preprocessing is unchanged.

## 11. Scheduled monitoring orchestration

```bash
python scripts/run_monitoring_cycle.py --run-id reviewer-demo
python scripts/verify_phase11.py
```

Explain: Phase 11 wraps the existing governance controls in a dependency-ordered
scheduled run. Each task must succeed and produce its configured evidence.
Failures block dependent tasks, the run fails closed, and evidence hashes are
recorded in the monitoring manifest.

Also point out that automatic retraining and automatic promotion remain
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

Explain: Vendor E preserves protected attributes and labels while shifting only
three non-protected model inputs for the supported `female|group_c`
intersection. Data quality passes and aggregate drift remains STABLE. The
single axes avoid blocking FAIL, but the intersection fails.

Point out the measured intersectional evidence: demographic-parity ratio
0.7479, equal-opportunity difference 0.1956, equalized-odds difference 0.2600,
and false-approval-rate difference 0.2600.

Then show the proxy-review priorities:
`device_risk_score`, `credit_utilization`, and
`bank_transaction_risk`. Explain that association plus SHAP influence is a
screening signal, not proof of causality or unlawful proxy use.

For the complete release gate:

```bash
make quality
make release-verify
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
4:05  Scheduled fail-closed monitoring orchestration
4:25  Vendor E intersectional fairness + proxy-risk evidence
4:45  CI/security/Terraform fail-closed delivery
4:55  Limitations and production-hardening path
```

Useful close:

> No single control is expected to detect every ML failure. The architecture
> uses defense in depth so data quality, drift, fairness, governance, and release
> controls independently stop unsafe progression at the correct layer.

## Phase 13 — incident SLA and alert evidence

```bash
make phase13-analyze
python scripts/verify_phase13.py
make phase13-test
```

Expected deterministic root-cause completion: `690` minutes (`11h30m`) against
the configured `2880` minute (`48h`) project SLA.
