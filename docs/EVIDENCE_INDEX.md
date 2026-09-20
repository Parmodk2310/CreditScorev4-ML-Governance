# Evidence Index

## Purpose

This index connects documented claims to repository locations that generate
or store supporting evidence.

## Phase 1 — incident reproduction

```bash
python scripts/verify_phase1.py
```

Evidence: `data/evidence/phase1/`

Important artifacts include baseline/incident metrics, performance comparison,
missingness comparison, and ROC figures.

## Phase 2 — data quality

```bash
python scripts/verify_phase2.py
```

Evidence: `data/evidence/phase2/` and blocked input under
`data/quarantine/phase2/`.

## Phase 3 — drift

```bash
python scripts/verify_phase3.py
```

Evidence:

- `data/evidence/phase3/drift_report.json`
- `data/evidence/phase3/feature_drift.csv`

## Phase 4 — fairness and SHAP

```bash
python scripts/verify_phase4.py
```

Evidence:

- `data/evidence/phase4/fairness_report.json`
- `data/evidence/phase4/fairness_by_group.csv`
- `data/evidence/phase4/shap_summary.json`
- SHAP importance/delta CSVs

## Phase 5 — governance

```bash
python scripts/verify_phase5.py
```

Evidence families:

- `data/evidence/phase5/healthy/`
- `data/evidence/phase5/vendor_c/`
- `data/evidence/phase5/vendor_d/`

Important artifact: `governance_decision.json`.

Expected decisions: healthy `APPROVE`, Vendor C `REJECT`, Vendor D `REJECT`.

## Phase 6 — serving and release

```bash
python scripts/verify_phase6.py
```

Evidence: `data/evidence/phase6/phase6_release_report.json`.

## Phase 7 — delivery

```bash
python scripts/verify_phase7.py
```

Evidence: `data/evidence/phase7/release_manifest.json`.

Implementation evidence also lives under `.github/workflows/`,
`infra/terraform/`, `docker/phase6/`, and `configs/phase7.yaml`.

## Phase 8 — reviewer evidence

```bash
python scripts/verify_phase8.py
```

Output: `data/evidence/phase8/reviewer_evidence_manifest.json`.

The Phase 8 manifest summarizes the evidence contract and acceptance results; it
does not replace the source evidence.

## Phase 9 — business-impact evidence

Run `python scripts/analyze_business_impact.py` followed by
`python scripts/verify_phase9.py`.

Generated evidence:

- `data/evidence/phase9/business_impact.json`
- `data/evidence/phase9/cohort_summary.csv`
- `data/evidence/phase9/decision_transition_summary.json`

The controlled Vendor A/Vendor B comparison preserves the same 15,000
applicants and identical `default_30d` labels. Verified effects include an
approval-rate increase from 73.91% to 78.60%, approved-cohort 30-day default
increase from 21.80% to 26.37%, 2,500 decision flips, and 1,602 newly approved
applicants. The newly approved synthetic cohort has a 61.99% observed 30-day
default rate.

These are deterministic synthetic case-study measurements, not estimates of
real-world lending loss or customer harm.

## Phase 10 — root-cause and remediation evidence

Run `python scripts/analyze_root_cause.py` followed by
`python scripts/verify_phase10.py`.

Generated evidence:

- `data/evidence/phase10/root_cause_ablation.json`
- `data/evidence/phase10/scenario_summary.csv`
- `data/evidence/phase10/factorial_effects.csv`
- `data/evidence/phase10/remediation_summary.csv`

The 2x2 ablation separates Vendor B semantic migration from elevated
missingness. q75 is recorded as a diagnostic validation candidate only; Vendor
B remains blocked by Phase 2 and the production preprocessing policy is
unchanged.

## Phase 11 — scheduled monitoring/orchestration evidence

Run:

```bash
python scripts/run_monitoring_cycle.py --run-id reviewer-demo
python scripts/verify_phase11.py
```

Generated evidence:

- `data/evidence/phase11/monitoring_run.json`
- `data/evidence/phase11/monitoring_events.jsonl`

The manifest records the source commit, final status, fail-closed state,
automatic-retraining/promotion flags, per-task status/attempts, command result,
and SHA-256 hashes for configured evidence artifacts. The event log preserves
one machine-readable record per task.

The scheduled workflow runs with read-only repository permissions and validates
the manifest before uploading Phase 11 evidence. It does not automatically
retrain or promote a model.

## Cumulative verification

```bash
make quality
make phase11-verify
git diff --check
```

A claim should not be treated as release evidence merely because it appears in a
Markdown file. Configuration, source, tests, and generated evidence are the
authoritative implementation boundary.
