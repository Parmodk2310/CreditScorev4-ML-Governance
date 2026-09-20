# Security Policy

## Project scope

CreditScoreV4 ML Governance uses a **synthetic** ML governance environment. It does not process real applicant PII, does not represent a live
banking decision system, and does not claim regulatory certification.

The AWS deployment path is fail-closed by default. Reports that could enable
unsafe cloud mutation, expose credentials, bypass governance controls, or
compromise build/release integrity are security-relevant.

## Supported version

| Version | Supported |
|---|---|
| `0.8.x` | Yes |
| `< 0.8` | No |

## Reporting a vulnerability

Please **do not open a public GitHub issue** for a suspected vulnerability,
credential exposure, or exploitable workflow problem.

Preferred reporting path:

1. Use the repository's **Security → Report a vulnerability** flow / private
   security advisory when available.
2. Include the affected file, commit/tag, impact, reproduction steps, and any
   suggested mitigation.
3. Remove real credentials, tokens, account identifiers, or personal data from
   screenshots and logs.

If private vulnerability reporting is unavailable, contact the repository owner
through the GitHub profile and request a private reporting channel.

## Security boundaries

Reports are especially useful for:

- exposed secrets or credentials;
- GitHub Actions permission escalation;
- unpinned or compromised third-party Actions;
- bypasses of `make phase9-verify` or required CI gates;
- model-governance state-transition bypasses;
- unsafe deployment-gate bypasses;
- container or infrastructure vulnerabilities;
- artifact/evidence integrity failures;
- injection, path traversal, or unsafe deserialization.

## Build and supply-chain controls

Repository workflows should:

- use least-privilege `permissions`;
- pin external GitHub Actions to full 40-character commit SHAs;
- retain the human-readable release tag as an inline comment;
- run Gitleaks and Trivy;
- build/smoke-test the container before merge;
- run cumulative Phase 9 verification before merge;
- keep AWS mutation disabled unless explicitly enabled and confirmed.

## Disclosure expectations

Please allow reasonable time to reproduce, fix, test, and release a security
change before public disclosure.
