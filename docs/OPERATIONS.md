# Operations

## Prerequisites

- Python 3.12
- A reachable database for `DATABASE_URL`
- A reachable Redis instance for idempotency and rate limiting
- `ENCRYPTION_KEY` and `API_SECRET_KEY`

The app will not start cleanly without those basics in place.

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
- Observability hooks exist for Datadog, Sentry, PostHog, and structured logs; configure them explicitly per environment.

## Documentation Policy

This repository intentionally keeps a small doc surface.

- `README.md` is the onboarding document.
- `docs/ARCHITECTURE.md` is the human architecture summary.
- `docs/OPERATIONS.md` is the runbook.

If new documentation is needed, update one of these files instead of creating a new long-lived markdown tree unless the new file clearly replaces an existing source of truth.
