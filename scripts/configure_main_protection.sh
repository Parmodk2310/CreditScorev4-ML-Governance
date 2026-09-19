#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-Parmodk2310/CreditScorev4-ML-Governance}"
BRANCH="${BRANCH:-main}"
POLICY_FILE="${POLICY_FILE:-ops/main-branch-protection.json}"

command -v gh >/dev/null 2>&1 || {
  echo "ERROR: GitHub CLI (gh) is required." >&2
  exit 1
}

gh auth status >/dev/null

[[ -f "$POLICY_FILE" ]] || {
  echo "ERROR: $POLICY_FILE not found. Run from repository root." >&2
  exit 1
}

echo "Repository: $REPO"
echo "Branch:     $BRANCH"
echo "Policy:     $POLICY_FILE"

if [[ "${1:-}" != "--apply" ]]; then
  echo
  echo "Dry run only. To apply:"
  echo "  ./scripts/configure_main_protection.sh --apply"
  exit 0
fi

echo
echo "Applying branch protection..."
if ! gh api   --method PUT   -H "Accept: application/vnd.github+json"   -H "X-GitHub-Api-Version: 2022-11-28"   "/repos/$REPO/branches/$BRANCH/protection"   --input "$POLICY_FILE"; then
  echo >&2
  echo "ERROR: GitHub rejected branch protection." >&2
  echo "If the repo is private and your plan does not support this feature," >&2
  echo "make it public first or use a plan that supports private-repo protection." >&2
  exit 1
fi

echo
echo "Protection applied. Current required checks:"
gh api   -H "Accept: application/vnd.github+json"   -H "X-GitHub-Api-Version: 2022-11-28"   "/repos/$REPO/branches/$BRANCH/protection"   --jq '.required_status_checks.contexts[]'
