# Main Branch Protection

This policy is designed for a single-maintainer repository while still forcing
changes through a pull request and required CI.

## Required checks

| Workflow | Required job/check |
|---|---|
| Quality and governance | `quality` |
| Quality and governance | `terraform` |
| Security | `secrets` |
| Security | `trivy` |
| Container image | `build-smoke` |

These names match the current v0.8.0 workflows.

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

## Private-repository note

GitHub plan entitlements can limit branch-protection features for private
repositories. If GitHub returns an entitlement error, apply this policy after
the repository is public or on a plan that supports private-repo protection.

## Deployment workflow

`Gated AWS deployment` is intentionally manual and fail-closed. It is not a
required merge check.
