# Model Registry and Release-State Model

![Release-state diagram](assets/diagrams/release-state.svg)

## Governance states

```text
CANDIDATE
  |
  +-- APPROVE --> STAGING
  |
  `-- REJECT ---> REJECTED
```

Phase 5 owns the governance decision. A candidate cannot enter the release lifecycle until evidence-based policy approval allows `CANDIDATE -> STAGING`.

## Release states

```text
STAGING -> SHADOW -> CANARY -> PRODUCTION
   ^          |          |
   |          |          |
   +----------+----------+
        rollback on failed release gates
```

Phase 6 owns release safety. It intentionally separates **model eligibility** from **production readiness**.

### STAGING

The model has passed governance but is not serving production traffic.

### SHADOW

The candidate can execute alongside the existing path without controlling production decisions. This is where compatibility/behavior can be observed before traffic allocation.

### CANARY

Traffic is progressively routed to the candidate using configured checkpoints:

```text
10% -> 25% -> 50% -> 100%
```

Release gates evaluate health at the checkpoints.

### PRODUCTION

Reached only after successful governance and release gates.

### Rollback

The degraded verification scenario fails:

- error rate
- mean risk delta
- p95 latency

The candidate returns to `STAGING`, and the rollback reason is persisted as release evidence.

## Illegal transition

A direct path such as:

```text
CANDIDATE -> PRODUCTION
```

is intentionally blocked. This prevents bypassing both governance and safe-release controls.
