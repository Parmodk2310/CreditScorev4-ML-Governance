# Evidence Index

## Purpose

This index connects reviewer-facing claims to repository locations that generate
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

## Cumulative verification

```bash
make quality
make phase8-verify
git diff --check
```

A claim should not be treated as release evidence merely because it appears in a
Markdown file. Configuration, source, tests, and generated evidence are the
authoritative implementation boundary.
