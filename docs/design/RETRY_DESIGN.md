# Retry Design: Why Mutating Methods Don't Retry

## Decision

Stargate Lite's HTTP client (`app/http_client.py`) only retries **idempotent** HTTP methods: `GET`, `HEAD`, `OPTIONS`. Mutating methods (`POST`, `PUT`, `PATCH`, `DELETE`) are **never retried** at the Stargate layer.

## Rationale

### The Duplicate Payment Problem

If a `POST /payments` request times out, the payment may have already been created on the provider side. Retrying blindly would create a **duplicate payment** — a critical financial error that is extremely difficult to reverse.

This applies to all mutating operations:
- Creating vendors, bills, invoices (QuickBooks, Xero, Sage)
- Sending payments (Stripe, Square, Bill.com)
- Creating envelopes (DocuSign)
- Sending messages (Slack, Gmail)

### Who Handles Retry?

Baby MARS (the upstream orchestrator) is responsible for retry decisions on mutating operations. Every Stargate error response includes a `retry_strategy` field:

| Strategy | Meaning | Example |
|----------|---------|---------|
| `backoff` | Safe to retry with exponential backoff | Network timeout, rate limit |
| `human_intervention` | User must fix before retry | Expired credentials, missing permissions |
| `none` | Do not retry | Invalid capability key, validation error |

Baby MARS uses this field to decide whether and how to retry, with full context about the operation being performed.

### What Stargate Does Retry

GET requests are retried automatically by the HTTP client:
- **3 attempts** with exponential backoff (0.5s, 1s, 2s)
- On status codes: 429, 500, 502, 503, 504
- This is safe because GET is idempotent — reading data twice has no side effects

### Token Refresh

OAuth token refresh (`POST` to token endpoint) is a special case. Although it uses POST, it is effectively idempotent — refreshing a token twice produces the same result. Each connector retries token refresh once with a 1s delay to handle transient network blips. See the `_refresh_token()` methods in connector base classes.

## References

- `app/http_client.py` — `StargateHTTPClient.__init__()` retry configuration
- `app/errors.py` — `ERROR_RETRY_STRATEGIES` mapping
- Stargate Command Contract v1.0 — `retry_strategy` field specification
