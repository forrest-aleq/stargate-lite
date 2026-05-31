# Architecture

Stargate Lite is `S1`, the Aleq execution runtime. It should be reasoned about
as a platform service, not only as an implementation detail behind one client.

## Runtime Shape

Stargate Lite is a FastAPI service with a thin routing layer and a large capability registry.

- `app/main.py` wires routers, CORS, OpenAPI overrides, startup, and shutdown.
- `app/routers/execute.py` is the main execution endpoint.
- `app/services/execution.py` handles idempotency lookup, handler execution, error normalization, telemetry, and delivery events.
- `app/registry/` maps `capability_key` values to connector or utility handlers.
- `app/database.py` stores encrypted credentials and exposes the credential manager.
- `app/connectors/` contains service-specific integrations.

## Request Flow

1. The caller sends `POST /api/v1/execute` with `capability_key`, tenant identity, `turn_id`, and `args`.
2. `verify_api_key` validates the API key and optional request signature.
3. The execute router applies rate limiting, requires Redis idempotency storage, checks the org-scoped cache, and acquires an execution lock.
4. The capability registry resolves the abstract capability to a concrete handler.
5. The execution service runs the handler with timeout protection, circuit-breaker checks, and telemetry hooks.
6. Stargate returns a normalized success or error payload and caches the result by `org_id + turn_id + capability_key`.

## Key Design Constraints

- Redis is required for the idempotency contract and is also used by rate limiting and webhook durability helpers. `/execute` fails closed when Redis is unavailable so retries cannot double-run side-effecting handlers.
- Capability availability is environment-gated. Missing service credentials can hide whole service groups from the runtime registry.
- Credentials are multi-tenant and keyed by `org_id`, `user_id`, `service`, and `credential_type`.
- Google and Microsoft connectors share credential stores across multiple product-specific connectors.
- `openapi.json` is committed and should match `app.openapi()` output exactly.

## Source Files Worth Knowing

- `app/main.py`
- `app/routers/execute.py`
- `app/services/execution.py`
- `app/database.py`
- `app/registry/__init__.py`
- `app/errors.py`
- `openapi.json`

## Canonical Public Families

The stable `S1` route families are:

- capabilities
- schemas
- credentials
- execute

OAuth callbacks, webhook receivers, and registry mechanics remain operational
surfaces rather than primary public SDK families.
