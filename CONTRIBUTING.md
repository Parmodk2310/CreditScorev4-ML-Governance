# Contributing

Thanks for helping improve CreditScoreV4 ML Governance.

This repository uses deterministic synthetic data to test ML governance controls.
Contributions should preserve that boundary and should not introduce claims of
real-bank production use, regulatory certification, or live AWS deployment
without corresponding evidence.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Python 3.12 is the supported development runtime.

## Branch and pull-request workflow

Do not push directly to `main`.

Create a focused branch:

```bash
git switch -c fix/<short-description>
# or
git switch -c feat/<short-description>
```

Before opening a pull request:

```bash
make quality
make phase8-verify
make phase7-terraform
git diff --check
```

For workflow/security changes:

```bash
python -m pytest -v tests/automation/test_workflows.py tests/evidence/test_phase8_evidence_contract.py
```

## Required checks on `main`

The branch-protection policy expects these exact job/check names:

- `quality`
- `terraform`
- `secrets`
- `trivy`
- `build-smoke`

The branch must be up to date with `main` before merge.

## GitHub Actions supply-chain rule

Every external `uses:` reference must be pinned to a **full 40-character commit
SHA**.

Example:

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
```

Do not replace SHA pins with mutable tags such as `@v7`, `@main`, or `@master`.

When updating an Action:

1. verify the upstream release/tag;
2. resolve it to the underlying commit SHA;
3. update the SHA and tag comment together;
4. rerun workflow contract tests and Phase 8 verification.

## ML governance invariants

Changes must preserve or deliberately update the executable contracts for:

- data-quality gating and quarantine;
- drift governance;
- fairness/explainability boundaries;
- evidence integrity;
- registry state transitions;
- shadow/canary/rollback controls;
- fail-closed cloud deployment.

If a threshold or expected outcome changes, update the corresponding config,
verification code, tests, evidence contract, and public documentation
in the same pull request.

## Documentation

Keep documentation claims synchronized with executable behavior. Avoid unsupported
statements about real customer/bank data, production traffic, regulatory
compliance, deployed AWS infrastructure, or causal conclusions from SHAP.

## Security

See [`SECURITY.md`](SECURITY.md). Do not publish suspected vulnerabilities,
secrets, or credentials in a public issue.
