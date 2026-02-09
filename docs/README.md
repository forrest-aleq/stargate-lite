# Documentation

## Directory Layout

| Directory | Purpose |
|-----------|---------|
| `contracts/` | API contracts between Stargate and upstream consumers (N3, TAMI, Primitives). **The crown jewels** -- changes here require versioned reviews. |
| `operations/` | Deployment, release process, logging schema, production readiness. |
| `architecture/` | Living system-design documents (Aleq architecture, MAP, observability). |
| `design/` | Research notes and technical designs (financial models, FCI, connectors). |
| `analysis/` | Point-in-time assessments and gap analyses. |
| `schemas/` | Generated capability schema exports. Large files are gitignored -- see `schemas/README.md` to regenerate. |
| `parity/` | Service parity tracking. |
| `scenarios/` | End-to-end test scenarios. |
| `archive/` | Historical build notes from initial development. Frozen, not maintained. |

## Key Files

### Contracts
- `contracts/STARGATE_INTEGRATION_CONTRACT.md` -- master integration contract (v1.2)
- `contracts/N3_API_SPEC.md` -- N3 API specification
- `contracts/PRIMITIVES_CONTRACT.md` -- primitives layer contract

### Operations
- `operations/RELEASE_GUIDE.md` -- release process (read before any release)
- `operations/DEPLOYMENT_GUIDE.md` -- deployment instructions
- `operations/LOG_SCHEMA.md` -- structured logging schema
