# Stargate Lite

Stargate Lite is the execution service for Aleq. It exposes a stable
`/api/v1/execute` contract, resolves `capability_key` values through the
registry, loads encrypted credentials, calls connector handlers, and returns
normalized success or error payloads.

In the platform-first direction, Stargate Lite is `S1`: the execution runtime
that sits beneath `M1` and defines the `s1.*` half of the universal SDK
surface.

## Maintained Docs

Only these human-written docs are maintained:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PLATFORM_DIRECTION.md`
- `docs/OPERATIONS.md`
- `docs/S1_SURFACE_MATRIX.md`

`openapi.json` is the machine-readable API contract and should stay in sync with the FastAPI app.

## Repo Layout

- `app/`: FastAPI app, routers, execution flow, connectors, registries, models
- `tests/`: contract, routing, registry, and reliability tests
- `scripts/`: maintenance scripts, OpenAPI generation, contract checks
- `openapi.json`: committed OpenAPI spec used as an external contract

## Local Setup

Use Python 3.12. The repo now pins that locally with `.python-version`, and the supported bootstrap path is `./setup.sh`.

```bash
./setup.sh
source .venv/bin/activate
```

Set the minimum required environment variables before starting the app:

- `ENCRYPTION_KEY`
- `API_SECRET_KEY`
- `DATABASE_URL`
- Redis settings via `REDIS_URL` or `REDIS_HOST` / `REDIS_PORT`

Then run migrations and start the server:

```bash
alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## Main Endpoints

- `POST /api/v1/execute`
- `GET /api/v1/capabilities`
- `POST /api/v1/connectors/status`
- `POST /api/v1/connectors/connected`
- `/oauth/*` for connector auth flows
- `/webhooks/*` for inbound events

## Operational Notes

- Redis is part of the runtime contract for idempotency and rate limiting.
- Capabilities are filtered at startup by environment-driven service gates in `app/registry/__init__.py`.
- OAuth credentials are stored in `stargate_credentials` and encrypted at rest.
- After model or route changes, regenerate `openapi.json` with `python scripts/generate_openapi.py`.
