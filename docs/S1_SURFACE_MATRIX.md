# S1 Surface Matrix

This document defines the canonical `S1` surfaces for the universal SDK and
platform documentation.

## Canonical Families

| Family | Purpose | Current Routes | SDK Module | Exposure |
|---|---|---|---|---|
| Capabilities | Discover executable capability keys and high-level metadata | `GET /api/v1/capabilities` | `client.s1.capabilities` | Public |
| Schemas | Discover rich per-capability schemas and service-level schema coverage | `GET /api/v1/schemas`, `GET /api/v1/schemas/{capability_key}`, `GET /api/v1/services`, `GET /api/v1/capabilities/enhanced` | `client.s1.schemas` | Public |
| Credentials | Check connector readiness and credential metadata, revoke when needed | `POST /api/v1/credentials/status`, `POST /api/v1/credentials/revoke`, `GET /api/v1/credentials/metadata` | `client.s1.credentials` | Public |
| Execute | Execute a capability with idempotency, rate limiting, and normalized errors | `POST /api/v1/execute` | `client.s1.execute` | Public |

## Operational Families

| Family | Purpose | Exposure |
|---|---|---|
| OAuth | Connector auth callbacks and token exchange plumbing | Internal / operational |
| Webhooks | Inbound events from external services | Internal / operational |
| Registry Gates | Startup-time filtering and environment service gates | Internal only |
| Connector Internals | Handler-specific behavior and upstream client logic | Internal only |

## Notes By Family

### Capabilities

This is the top-level discovery surface for `S1`.

It should answer:

- what can this environment execute
- which capability keys exist
- what services are represented

It should remain lightweight and safe to call frequently.

### Schemas

This is the richer discovery surface for agents, SDKs, internal tooling, and
evaluation systems.

It should answer:

- what arguments a capability takes
- what it returns
- whether rich schema metadata exists
- how to progressively disclose service families

### Credentials

This is the connector readiness surface.

It should answer:

- whether the required credential exists
- whether setup is needed
- whether delegation is supported
- what metadata is known about a stored credential

It should not leak raw tokens.

### Execute

This is the core execution surface.

It should preserve the current guarantees around:

- idempotency by `org_id + turn_id + capability_key`
- duplicate in-flight execution is rejected with a retryable error instead of running a second handler
- normalized success and error payloads
- rate limiting
- tenant isolation via credential lookup

## First SDK Shape

Recommended universal SDK surface:

```ts
client.s1.capabilities.list()
client.s1.schemas.list()
client.s1.schemas.get(capabilityKey)
client.s1.schemas.listServices()
client.s1.schemas.listEnhanced(options)
client.s1.credentials.status(input)
client.s1.credentials.metadata(input)
client.s1.credentials.revoke(input)
client.s1.execute.run(input)
```

## Direct Auth Modes

Current direct `S1` auth supports:

- `API_SECRET_KEY`
  Legacy shared server-to-server key.
- `API_CLIENT_KEYS_JSON`
  Env-backed client registry for multiple direct consumers.

Registry entries support:

- `key_id`
- `secret`
- optional `org_allowlist`

This makes direct `S1` usage viable for trusted internal consumers and early
platform clients without requiring the full control-plane issuance path on day
one.

## Non-Goals

This matrix does not attempt to expose:

- raw connector clients
- registry implementation details
- Redis or idempotency internals
- OAuth token exchange steps as first-class SDK modules

Those remain part of the implementation or operational plane.
