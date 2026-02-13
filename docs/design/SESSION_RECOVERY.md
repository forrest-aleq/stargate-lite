# Session Recovery Design

## Current State

Stargate Lite is a stateless request executor — it receives a capability key
and args, calls the upstream service, and returns the result. There is no
persistent job queue or long-running background work.

## Mitigations Against Lost Requests

### 1. Idempotency Cache (turn_id)

Every request includes a `turn_id`. Before execution, Stargate checks Redis
for a cached response with that turn_id. If found, it returns the cached
result without re-executing.

This means Baby MARS can safely retry a request after a timeout or deploy
without risking duplicate side effects (e.g., double payments).

### 2. Baby MARS Retry with Backoff

Baby MARS has a 30-second client timeout. If Stargate doesn't respond in time,
Baby MARS retries with exponential backoff. The `retry_strategy` field in error
responses tells Baby MARS how to handle each failure mode:

- `backoff` — retry with exponential delay (network errors, rate limits)
- `human_intervention` — stop and notify user (credential issues, permissions)
- `none` — do not retry (validation errors, unknown capabilities)

### 3. Circuit Breaker

When a service is down, the circuit breaker fast-fails requests in ~1ms instead
of waiting 25 seconds for a timeout. This prevents worker pool saturation during
deploys or service outages, leaving workers available for healthy services.

### 4. Short-Lived Operations

All Stargate operations complete within the 25-second handler timeout. There are
no long-running tasks that span multiple request cycles. This means a restart
loses at most one in-flight request per worker, and Baby MARS retries handle it.

## When Would a Job Queue Be Needed?

If Stargate adds operations that:

- Take longer than 25 seconds (e.g., bulk data migrations, large report generation)
- Need guaranteed delivery (e.g., payment processing that can't rely on client retry)
- Require progress tracking (e.g., multi-step workflows with partial results)

Then consider adding a task queue (arq for async Python, or Celery for heavier
workloads) with Redis as the broker. The idempotency cache would still prevent
duplicate execution.

## Current Assessment

The combination of idempotency cache + client retry + circuit breaker + short
operations provides sufficient reliability for the current workload. No
persistent queue is needed at this time.
