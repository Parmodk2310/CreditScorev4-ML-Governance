# Immutable GitHub Actions Pinning Manifest

Initially established during v0.8.1 hardening and revalidated for the current v1.x release line.

All workflow `uses:` references are pinned to immutable 40-character commit
SHAs. The human-readable release/tag is retained only as an inline comment.

| Action | Tag | Commit |
|---|---|---|
| `actions/checkout` | `v7` | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-python` | `v7` | `5fda3b95a4ea91299a34e894583c3862153e4b97` |
| `hashicorp/setup-terraform` | `v4` | `dfe3c3f87815947d99a8997f908cb6525fc44e9e` |
| `gitleaks/gitleaks-action` | `v3` | `e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e` |
| `aquasecurity/trivy-action` | `v0.36.0` | `ed142fd0673e97e23eac54620cfb913e5ce36c25` |
| `docker/setup-buildx-action` | `v4` | `f87e5991a6d7451dcb8d9637bfbc97413f497069` |
| `docker/build-push-action` | `v7` | `c3c9e263c25d99ce0380d002d59b67737d91b0dc` |
| `aws-actions/configure-aws-credentials` | `v6` | `e1253824e5c10ff9df46874f81ed3ec929e19cfd` |
| `aws-actions/amazon-ecr-login` | `v2` | `03f1aad4c6c7ffd436567f42f9384779290529bd` |
| `actions/upload-artifact` | `v7` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |

`aquasecurity/trivy-action@v0.36.0` and
`aws-actions/configure-aws-credentials@v6` are annotated tags; the workflow pins
the underlying commit, not the tag object.
