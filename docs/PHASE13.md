# Phase 13 — Incident SLA, Alerting & Operational Evidence

Phase 13 adds a deterministic incident-operations evidence layer around the
existing Vendor B data-quality incident. It does not introduce a new model,
automatic remediation, or live on-call integration.

## Goal

The phase answers a new operational question:

> Can the system prove when an incident was detected, alerted, blocked, triaged,
> and root-caused, and whether that simulated response met explicit project SLAs?

The source incident remains the existing deterministic Vendor B fixture.

## Control flow

```text
Vendor B incident
      |
      v
Phase 2 data-quality evidence ----+
                                  |
Phase 9 business impact ----------+--> Phase 13 incident timeline
                                  |            |
Phase 10 root-cause evidence -----+            +--> synthetic alert record
                                               +--> SLA evaluation
                                               +--> cross-phase SHA-256 lineage
                                               `--> incident report
```

Phase 13 consumes the previously verified Phase 2, 9, and 10 evidence. It does
not rewrite those analyses.

## Deterministic timeline

The configured synthetic timeline is:

| Event | Time (UTC) |
|---|---|
| Incident starts | 2026-01-01 00:00 |
| Vendor B batch ingested | 02:00 |
| Data-quality check starts | 03:00 |
| Incident detected | 03:04 |
| Alert evidence created | 03:05 |
| Governance block recorded | 03:06 |
| Triage starts | 06:00 |
| Root-cause evidence completed | 11:30 |
| Review completed | 13:00 |

This produces:

- detection latency: **184 minutes (3h04m)**
- alert latency: **185 minutes (3h05m)**
- governance-block latency: **186 minutes (3h06m)**
- triage latency: **360 minutes (6h00m)**
- root-cause completion: **690 minutes (11h30m)**

The configured root-cause project SLA is **<= 2,880 minutes (48h)**.

## Alerting boundary

Phase 13 generates a machine-readable alert artifact with severity `HIGH`,
the measured Vendor B `device_risk_score` missingness, the existing data-contract
`max_null_rate: 0.05` threshold, and `BLOCK_AND_QUARANTINE` as the response action.

The alert is explicitly:

- synthetic;
- evidence-only;
- not routed to PagerDuty, Slack, email, SNS, or another live paging system.

## Safety boundary

Phase 13 keeps:

```text
automatic_retraining = false
automatic_promotion  = false
live_paging          = false
```

Alert generation cannot bypass the existing Phase 5 governance authority or
Phase 6 safe-release state machine.

## Evidence

Phase 13 writes:

- `data/evidence/phase13/incident_timeline.json`
- `data/evidence/phase13/incident_events.jsonl`
- `data/evidence/phase13/alert_record.json`
- `data/evidence/phase13/sla_summary.json`
- `data/evidence/phase13/incident_report.json`

The incident report stores SHA-256 hashes for the existing data contract and the
Phase 2, 9, and 10 source evidence. Verification also checks that the JSONL
event stream exactly matches the timeline JSON.

## Verification

```bash
make phase13-analyze
python scripts/verify_phase13.py
make phase13-test
make phase13-verify
```

`make phase13-verify` first runs the cumulative Phase 12 boundary, then
generates and verifies Phase 13 operational evidence and runs the focused
Phase 13 tests.

## Claim boundary

Appropriate:

> Built deterministic incident-response evidence measuring detection,
> governance-block, triage, and root-cause latency against explicit simulated
> SLAs; Vendor B root-cause analysis completed in 11h30m against a <=48h
> project SLA.

Not appropriate:

- "Resolved a production incident in 11.5 hours."
- "Achieved 11.5-hour production MTTR."
- "Integrated live PagerDuty/on-call response."

Phase 13 remains a synthetic, production-oriented engineering demonstration.
