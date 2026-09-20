# Phase 11 — Scheduled Monitoring & Governance Orchestration

Phase 11 turns the previously manual governance verification path into a
scheduled, fail-closed monitoring control run.

## Design goal

The objective is not to add another model or retraining loop. The objective is
to orchestrate the existing data-quality, drift, fairness, governance, release,
business-impact, and root-cause controls as one auditable scheduled run.

```text
GitHub Actions schedule / manual dispatch
                 |
                 v
        Phase 11 orchestrator
                 |
   +-------------+-------------+
   |             |             |
   v             v             v
data quality    drift        fairness
   |             |             |
   +-------------+-------------+
                 |
                 v
       governance + release
                 |
                 v
     business impact + root cause
                 |
                 v
       run manifest + event log
```

## Fail-closed behavior

Tasks declare explicit dependencies. If a required task fails, dependent tasks
are marked `SKIPPED` rather than continuing with incomplete evidence.

Commands are executed without a shell. Each successful task must also produce
its configured evidence artifacts; missing evidence converts an otherwise
successful command into a failed monitoring task.

## Scheduling

The concrete scheduler for Phase 11 is GitHub Actions using a UTC cron schedule
plus manual `workflow_dispatch`.

The orchestration engine itself is Python and scheduler-independent. Airflow is
not introduced in this phase because the current repository does not need a
separate scheduler database, executor, worker fleet, or backfill control plane
to demonstrate the governance contract.

A future production deployment could move the same orchestration contract to
Airflow, Dagster, Argo Workflows, or another scheduler when operational scale
justifies it.

## Retraining and promotion boundary

Phase 11 deliberately keeps:

```text
automatic_retraining = false
automatic_promotion  = false
```

Drift or fairness findings remain investigation/governance inputs. The
scheduler cannot create a production promotion shortcut around the existing
Phase 5 governance authority or Phase 6 safe-release state machine.

## Evidence

Each run writes:

- `data/evidence/phase11/monitoring_run.json`
- `data/evidence/phase11/monitoring_events.jsonl`

The manifest records task status, attempt count, command result, evidence
SHA-256 hashes, fail-closed state, and the source commit.

## Verification

```bash
make phase11-run
python scripts/verify_phase11.py
make phase11-test
```

The first implementation is a deterministic synthetic control-monitoring
workflow. It is not a claim of live bank monitoring, real alert routing, or a
production incident-response system.
