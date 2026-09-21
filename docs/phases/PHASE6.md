# Phase 6 — Serving, Safe Release & Runtime Observability

## Objective

Phase 6 takes a model version that Phase 5 has already approved into `STAGING` and verifies that the version can be served and promoted safely without bypassing governance. The phase uses a local release simulation: it exercises real FastAPI inference against the persisted CreditScoreV4 artifact while rollout traffic, health, and rollback conditions are deterministic local controls.

## Boundary with Phase 5

Phase 5 answers **may this candidate enter staging?** Phase 6 answers **can an approved staging candidate reach production safely?**

```text
Phase 5 APPROVE
      |
      v
   STAGING
      |
      v
   SHADOW
      |
      v
   CANARY
10% -> 25% -> 50% -> 100%
      |
      +---- failed gates ----> STAGING (rollback)
      |
      v
 PRODUCTION
```

A direct `CANDIDATE -> PRODUCTION` transition remains illegal.

## Serving API

`src/creditscore/serving/` loads the same persisted sklearn/XGBoost pipeline used by earlier phases and exposes:

- `GET /health` — process liveness
- `GET /ready` — model readiness
- `POST /predict` — single application inference
- `POST /batch-predict` — bounded batch inference
- `GET /model` — model/version/hash metadata
- `GET /metrics` — Prometheus exposition

The API returns `P(default_30d=1)`. The synthetic decision summary remains separate: `approved = risk_probability < decision_threshold`.

## Runtime metrics

The Prometheus surface includes:

- request counts by method/path/status
- request latency histogram
- prediction counts by predicted outcome
- risk-probability histogram
- model readiness gauge
- release-stage gauge
- canary-share gauge
- rollback-event gauge

The Docker Compose stack includes the API, Prometheus, and a provisioned Grafana dashboard for local demonstration.

## Shadow release

An approved `STAGING` version transitions to `SHADOW`. Shadow health is evaluated using configurable project guardrails:

- minimum observed request count
- maximum error rate
- maximum p95 latency
- maximum mean prediction-risk delta from the comparison baseline

Passing shadow evaluation moves the model to `CANARY`. Failing shadow evaluation returns it to `STAGING`.

## Canary rollout

The default rollout is configured in `configs/phase6.yaml`:

```text
10% -> 25% -> 50% -> 100%
```

`CanaryRouter` uses SHA-256-derived request buckets, so the same request key is deterministically routed to the same side for a fixed traffic share. Each checkpoint is evaluated before the controller advances.

At the final healthy 100% checkpoint, the registry moves `CANARY -> PRODUCTION`.

## Automatic rollback

If a shadow or canary checkpoint violates a blocking release gate, the controller transitions the candidate back to `STAGING`, writes an explicit rollback reason, and appends an audit event. Phase 6 verification includes a degraded canary with elevated error rate, latency, and prediction delta to prove this path.

## Registry state machine through Phase 6

```text
REGISTERED
    |
    v
CANDIDATE
   / \
  /   \
 v     v
STAGING REJECTED
   |
   v
 SHADOW
  |  \
  |   +------ rollback ------> STAGING
  v
 CANARY
  |  \
  |   +------ rollback ------> STAGING
  v
PRODUCTION
```

## Verification

```bash
make phase6-verify
```

The Phase 6 release gate checks the real API, model readiness, prediction endpoints, Prometheus metrics, deterministic traffic routing, every configured canary checkpoint, production promotion, rollback, audit evidence, illegal transition protection, and the cumulative test suite.

## Docker demonstration

After generating the Phase 1 model artifact and Phase 5 registry state:

```bash
docker compose -f docker/runtime/docker-compose.yml up --build
```

Local ports:

- API: `8000`
- Prometheus: `9090`
- Grafana: `3000`

## Scope boundary

Phase 6 is a local safe-release simulation. It does not claim a live banking deployment, real customer traffic, or regulatory certification. Workflow orchestration, CI/CD deployment automation, and cloud infrastructure remain Phase 7.
