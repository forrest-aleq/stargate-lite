# Operations

## Prerequisites

- Python 3.12
- A reachable database for `DATABASE_URL`
- A reachable Redis instance for idempotency and rate limiting
- `ENCRYPTION_KEY` and `API_SECRET_KEY`

The app will not start cleanly without those basics in place. If Redis becomes
unavailable after startup, `/api/v1/execute` refuses execution with a retryable
error rather than risking duplicate side effects.

## Local Run

```bash
./setup.sh
source .venv/bin/activate
alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## Verification

Use the project Python 3.12 environment for all checks.

```bash
python -m pytest tests
python scripts/check_api_contracts.py
python scripts/generate_openapi.py --check
```

## Deployment Notes

- `Procfile` starts the web process with `uvicorn app.main:app`.
- `scripts/generate_openapi.py` should be run any time API models or routes change.
- Connector availability depends on environment variables that gate services in `app/registry/__init__.py`.
- Production deploys also require every enabled customer-facing connector to
  have its full provider env set from `app/constants/services.py`
  `CUSTOMER_CONNECT_ENV_REQUIREMENTS`. This prevents exposing a connector that
  appears enabled but cannot complete OAuth or credential setup.
- Observability hooks exist for Datadog, Sentry, PostHog, and structured logs; configure them explicitly per environment.

## Railway Readiness Audit

Use the `Audit Railway Readiness` GitHub Actions workflow for a read-only
environment audit. It validates the Railway service variables without deploying
or mutating runtime state, then uploads the missing-variable report as a run
artifact.

Production audits are intentionally stricter than staging: every connector in
`ENABLED_SERVICES` must also satisfy its full
`CUSTOMER_CONNECT_ENV_REQUIREMENTS` provider env set. If production is not ready,
run this workflow first and fix the reported Railway variables before attempting
`Deploy to Production`.

## Documentation Policy

This repository intentionally keeps a small doc surface.

- `README.md` is the onboarding document.
- `docs/ARCHITECTURE.md` is the human architecture summary.
- `docs/OPERATIONS.md` is the runbook.

If new documentation is needed, update one of these files instead of creating a new long-lived markdown tree unless the new file clearly replaces an existing source of truth.
