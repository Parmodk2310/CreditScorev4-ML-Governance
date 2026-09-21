# Main Branch Protection

This file documents the protection policy applied to `main` for this
single-maintainer repository. The canonical checked-in policy lives in
`ops/main-branch-protection.json`; `scripts/configure_main_protection.sh` applies
that policy through the GitHub API.

`main` is currently protected and the required quality, Terraform, security,
and container checks below are enforced before merge.

## Required checks

| Workflow | Required job/check |
|---|---|
| Quality and governance | `quality` |
| Quality and governance | `terraform` |
| Security | `secrets` |
| Security | `trivy` |
| Container image | `build-smoke` |

These names match the current workflow job names.

## Protection behavior

The included policy:

- requires the branch to be current with `main` before merge;
- requires a pull request before merge;
- requires all five checks above;
- applies protection to administrators;
- requires review conversations to be resolved;
- disables force pushes;
- disables branch deletion;
- keeps merge commits allowed;
- requires 0 approving reviews, appropriate for a single-maintainer repository.

If collaborators are added, raise `required_approving_review_count` to `1`.

## Apply

```bash
chmod +x scripts/configure_main_protection.sh

# Dry run
./scripts/configure_main_protection.sh

# Apply
./scripts/configure_main_protection.sh --apply
```

## Repository-state note

Protection is an external GitHub repository setting, while this file and
`ops/main-branch-protection.json` are the versioned policy definition. After any
repository visibility or plan change, re-run the configuration script and verify
the required checks through the GitHub branch-protection API.

## Deployment workflow

`Gated AWS deployment` is intentionally manual and fail-closed. It is not a
required merge check.
