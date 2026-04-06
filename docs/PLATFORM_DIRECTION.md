# S1 Platform Direction

This document records how Stargate Lite fits into the new Aleq platform
direction.

## Role

Stargate Lite is now `S1`: the hosted execution runtime.

It is responsible for:

- capability discovery
- schema discovery
- credential status and connector state
- execution against external services

## Relationship To M1

`M1` is the cognition runtime.
`S1` is the execution runtime.

Most clients should call `M1`, which will call `S1` as needed. Some trusted
clients and internal tools may call `S1` directly when they need raw execution
without the full M1 loop.

## Direct Auth

Direct `S1` access now supports two auth modes:

- legacy shared key via `API_SECRET_KEY`
- env-backed multi-client registry via `API_CLIENT_KEYS_JSON`

The client registry supports:

- per-client `key_id`
- secret rotation through env/config changes
- optional `org_allowlist` enforcement

This is an intentional bridge, not the final end state. Full control-plane
issuance and management for direct `S1` clients still belongs in the broader
Aleq platform control plane.

## What Changes

The platform is moving away from:

- N3-centric integration glue
- app-specific knowledge of Stargate routes
- implicit assumptions about which Stargate features are public

The platform is moving toward:

- stable `S1` route families
- explicit SDK modules
- clear separation between public execution surfaces and operational internals

## Public S1 Families

The canonical `S1` families are:

- `Capabilities`
- `Schemas`
- `Credentials`
- `Execute`

These map to the first universal SDK families:

- `client.s1.capabilities`
- `client.s1.schemas`
- `client.s1.credentials`
- `client.s1.execute`

## Internal / Operational Families

These remain important, but they are not the first public SDK surface:

- OAuth callback flows
- webhook receivers
- connector-specific maintenance endpoints
- internal registry or service gating details

They should stay documented, but they should not define the external platform
shape.

## Success Criteria

`S1` is ready for the new direction when:

- its public route families are stable and documented
- `M1` can depend on it as the default execution substrate
- the universal SDK exposes clean `s1.*` modules
- internal console and evaluation tools can reason about `S1` without reading
  connector internals
