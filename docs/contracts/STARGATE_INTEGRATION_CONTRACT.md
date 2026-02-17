# Stargate Integration Contract v1.2
**Last Updated:** February 3, 2026
**Status:** DRAFT - Requires agreement from MARS, NAOS, and Stargate teams
**Purpose:** Define explicit integration contract between Stargate and consuming systems
**Total Capabilities:** 770 across 34 services

---

## 1. Overview

This contract defines the **guaranteed behavior** of Stargate Lite that MARS and NAOS can rely on. No assumptions should be made beyond what is explicitly stated here.

### 1.1 Stargate's Role
- **Execution Layer** ("The Hands") - Executes capabilities against third-party APIs
- **Credential Management** - Securely stores and refreshes OAuth tokens
- **Idempotency Enforcement** - Prevents duplicate executions via Redis caching
- **Error Classification** - Maps external API errors to standardized error taxonomy

### 1.2 Consumer Responsibilities
- **MARS** (Workflow Orchestration) - Sends capability execution requests, handles retry logic
- **NAOS** (Agent Orchestration) - May call Stargate directly or via MARS
- **MIND** (Brain) - Does NOT call Stargate directly (only via MARS/NAOS)

---

## 2. API Contract

### 2.1 Execution Endpoint

**Endpoint:** `POST /api/v1/execute`

**Request Schema:**
```json
{
  "capability_key": "qb.vendor.create",
  "org_id": "org_abc123",
  "user_id": "user_xyz789",
  "turn_id": "turn_uuid_12345",
  "args": {
    "vendor_name": "Acme Corp",
    "email": "vendor@acme.com"
  }
}
```

**Field Contracts:**

| Field | Type | Required | Constraints | Purpose |
|-------|------|----------|-------------|---------|
| `capability_key` | string | ✅ YES | Must exist in registry | Identifies what to execute |
| `org_id` | string | ✅ YES | 3-100 chars | Multi-tenant isolation |
| `user_id` | string | ✅ YES | 3-100 chars | Credential lookup |
| `turn_id` | string | ✅ REQUIRED | UUID format | **Idempotency key (422 if missing)** |
| `args` | object | ✅ YES | Varies by capability | Capability-specific parameters |

**⚠️ CRITICAL: `turn_id` Contract**
- **`turn_id` is REQUIRED — Stargate returns 422 if omitted**
- **Stargate caches responses by `turn_id + capability_key` for 24 hours**
- **If MARS retries with same `turn_id`, Stargate returns cached response (no re-execution)**

**Response Schema (Success — HTTP 200):**
```json
{
  "status": "success",
  "capability_key": "qb.vendor.create",
  "tool_used": "quickbooks.create_vendor",
  "outputs": {
    "vendor_id": "123",
    "vendor_name": "Acme Corp"
  },
  "logs": [
    "Retrieved QuickBooks credentials for org_abc123",
    "Created vendor in QuickBooks: Acme Corp"
  ],
  "credential_type": "customer",
  "timestamp": "2025-11-23T10:30:00Z"
}
```

**Response Schema (Error — HTTP 200 for business errors, HTTP 429 for rate limits):**
```json
{
  "status": "error",
  "error_code": "CREDENTIALS_INVALID",
  "error_message": "QuickBooks OAuth token expired",
  "retry_strategy": "human_intervention",
  "details": {
    "service": "quickbooks"
  },
  "capability_key": "qb.vendor.create",
  "timestamp": "2025-11-23T10:30:00Z"
}
```

---

## 3. Error Taxonomy & Retry Contract

### 3.1 Error Codes (10 canonical codes)

Stargate uses a **standardized error taxonomy** (defined in `app/errors.py`). MARS/NAOS **MUST** use the `error_code` field to determine retry behavior.

| Error Code | Retry Strategy | Typical Cause |
|------------|----------------|---------------|
| `CAPABILITY_NOT_FOUND` | `none` | Unknown capability_key |
| `CREDENTIALS_MISSING` | `human_intervention` | User hasn't connected OAuth |
| `CREDENTIALS_INVALID` | `human_intervention` | Token expired/revoked |
| `CREDENTIALS_INSUFFICIENT` | `human_intervention` | Missing OAuth scopes |
| `RATE_LIMIT` | `backoff` | API rate limit exceeded (HTTP 429) |
| `NETWORK_ERROR` | `backoff` | Network timeout/connection failed |
| `VALIDATION_ERROR` | `none` | Invalid input parameters |
| `EXECUTION_ERROR` | `backoff` | Generic execution failure |
| `QUOTA_EXCEEDED` | `human_intervention` | External service quota hit |
| `PERMISSION_DENIED` | `human_intervention` | User lacks required permission |

### 3.2 Retry Strategy Mapping (3 strategies)

**`none`** — Permanent failure, do not retry
- `CAPABILITY_NOT_FOUND` — Fix the capability key
- `VALIDATION_ERROR` — Fix input parameters

**`human_intervention`** — User action required before retry
- `CREDENTIALS_MISSING` — User must connect OAuth
- `CREDENTIALS_INVALID` — User must re-authorize
- `CREDENTIALS_INSUFFICIENT` — Admin must grant scopes
- `QUOTA_EXCEEDED` — Upgrade plan or wait for quota reset
- `PERMISSION_DENIED` — Admin must grant permissions

**`backoff`** — Transient failure, retry with exponential backoff
- `RATE_LIMIT` — Check `details.retry_after_seconds` before retrying
- `NETWORK_ERROR` — Network issues, try again with backoff
- `EXECUTION_ERROR` — Tool failed, may be transient

### 3.3 Example Retry Logic (MARS)

```python
def execute_with_retry(capability_key, org_id, user_id, turn_id, args):
    max_retries = 3
    backoff = 2  # seconds

    for attempt in range(max_retries):
        response = stargate.execute(
            capability_key=capability_key,
            org_id=org_id,
            user_id=user_id,
            turn_id=turn_id,  # Same turn_id for idempotency!
            args=args
        )

        if response["status"] == "success":
            return response

        error_code = response["error_code"]
        retry_strategy = response["retry_strategy"]

        if retry_strategy == "none":
            raise Exception(f"Permanent failure: {response['error_message']}")

        elif retry_strategy == "human_intervention":
            raise Exception(f"User action needed: {response['error_message']}")

        elif retry_strategy == "backoff":
            if error_code == "RATE_LIMIT":
                retry_after = response.get("details", {}).get("retry_after_seconds", 60)
                time.sleep(retry_after)
            elif attempt < max_retries - 1:
                time.sleep(backoff ** attempt)
            else:
                raise Exception(f"Max retries exceeded: {response['error_message']}")

    raise Exception("Max retries exceeded")
```

---

## 4. Idempotency Contract

### 4.1 Guarantee

**Stargate GUARANTEES:**
- If MARS sends the same `turn_id + capability_key` combination within 24 hours, Stargate will:
  1. **NOT re-execute** the capability
  2. Return the **cached response** from the first execution
  3. Log "Cache hit" for observability

### 4.2 Requirements

**MARS MUST:**
- Use **UUID v4** format for `turn_id`
- Use the **same `turn_id`** for all retry attempts of a single logical operation
- **NOT reuse `turn_id`** across different logical operations
- Send `turn_id` for **ALL capabilities that mutate state** (create, update, delete)

**Stargate MUST:**
- Cache responses in Redis with key: `stargate:idempotency:{turn_id}:{capability_key}`
- Set TTL to 24 hours (86400 seconds)
- **Hard-fail if Redis is unavailable** (per Stargate Command Contract v1.0)

### 4.3 Edge Cases

**Q: What if MARS retries with different `args` but same `turn_id`?**
A: Stargate returns cached response (ignores new `args`). First execution wins.

**Q: What if Redis goes down mid-execution?**
A: Stargate **refuses to start** if Redis unavailable (fails health check).

**Q: What if `turn_id` is omitted?**
A: Stargate executes capability normally (NO idempotency protection).

**Q: Can MARS use same `turn_id` for different `capability_key`?**
A: YES - cache key includes both `turn_id` and `capability_key`, so they're independent.

---

## 5. Credential Management Contract

### 5.1 Dual Credential System

Stargate supports **two credential types:**

| Credential Type | User ID | Use Case | Example |
|----------------|---------|----------|---------|
| `customer` | Real user ID | User-specific data access | User's QuickBooks, user's HubSpot |
| `agent` | `ALEQ_AGENT` | Aleq-controlled automation | Linear issues, ClickUp tasks |

### 5.2 Credential Lookup Logic

**When MARS calls `qb.vendor.create`:**

1. Registry lookup: `requires_oauth=true`, `credential_type="customer"`, `service="quickbooks"`
2. Database query: `org_id={request.org_id}, user_id={request.user_id}, service="quickbooks", credential_type="customer"`
3. If credential found: Use it
4. If credential missing: Return `CredentialMissingError`

**When MARS calls `linear.issue.create`:**

1. Registry lookup: `requires_oauth=true`, `credential_type="agent"`, `service="linear"`
2. Database query: `org_id="ALEQ_SYSTEM", user_id="ALEQ_AGENT", service="linear", credential_type="agent"`
3. If credential found: Use Aleq's Linear token
4. If credential missing: Return `CredentialMissingError`

### 5.3 Token Refresh

**Stargate AUTOMATICALLY refreshes OAuth tokens when:**
- Token expires within 5 minutes
- API returns 401 Unauthorized

**MARS does NOT need to handle token refresh** - Stargate manages this transparently.

**If token refresh fails:**
- Stargate returns `CredentialInvalidError`
- User must re-authorize via OAuth flow

---

## 6. Performance Contract

### 6.1 Latency Targets (p95)

| Operation Type | Target Latency | Notes |
|---------------|----------------|-------|
| Simple read (e.g., `qb.vendor.get`) | < 1 second | Single API call |
| Complex read (e.g., `qb.report.profit_loss`) | < 3 seconds | Multiple API calls |
| Write operation (e.g., `qb.invoice.create`) | < 2 seconds | Single API call with validation |
| Bulk operation (e.g., `qb.vendors.list`) | < 5 seconds | Pagination handling |

**⚠️ NOT GUARANTEED:** Latency depends on external API performance. Stargate adds < 100ms overhead.

### 6.2 Timeout Behavior

**Stargate HTTP timeouts:**
- Connect timeout: 5 seconds
- Read timeout: 30 seconds

**If external API exceeds timeout:**
- Stargate returns `NETWORK_ERROR` with `retry_strategy="backoff"`
- MARS should retry with exponential backoff

### 6.3 Concurrency

**Stargate supports:**
- 100 concurrent requests (FastAPI default)
- Database connection pool: 20 base + 10 overflow
- HTTP connection pool: 20 pools × 100 connections

**MARS can safely send:**
- Up to 50 concurrent requests per Stargate instance
- Beyond 50, requests may queue (not fail)

---

## 7. Observability Contract

### 7.1 Health Checks

**Endpoint:** `GET /health`

**Response (Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-23T10:30:00Z",
  "redis": "connected",
  "database": "connected"
}
```

**Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "timestamp": "2025-11-23T10:30:00Z",
  "redis": "disconnected",  // Stargate will fail to start if Redis down
  "database": "connected"
}
```

**MARS/NAOS should:**
- Check `/health` before routing traffic to Stargate instance
- Remove unhealthy instances from load balancer rotation

### 7.2 Metrics (Prometheus)

**Endpoint:** `GET /metrics`

**Key Metrics:**
- `stargate_capability_executions_total{capability_key, service, status}` - Total executions
- `stargate_capability_latency_seconds{capability_key, service}` - Latency histogram
- `stargate_http_requests_total{service, method, status_code}` - External API calls
- `stargate_credential_refresh_total{service, status}` - Token refresh events

**MARS can use these for:**
- Detecting service degradation
- Capacity planning
- Debugging performance issues

### 7.3 Request Correlation

**⚠️ TO BE IMPLEMENTED:**
- Stargate will accept `correlation_id` in request headers
- All logs will include `correlation_id` for distributed tracing
- **QUESTION FOR TEAMS:** Should we use OpenTelemetry?

---

## 8. Capability Versioning (Future)

### 8.1 Current State

**NO versioning support** - Capabilities have single version

**Example:**
- `qb.customer.create` - No version suffix

### 8.2 Proposed Future State (MAP)

**Versioned capabilities:**
- `qb.customer.create@v1` - Original version
- `qb.customer.create@v2` - New version with different signature
- `qb.customer.create` - Alias to latest stable version

**QUESTION FOR TEAMS:**
- Do we need versioning BEFORE MAP?
- How should MARS handle version upgrades?
- Should Stargate auto-upgrade MARS to latest version?

---

## 9. Backward Compatibility Contract

### 9.1 Breaking Changes

**Stargate WILL NOT make breaking changes without:**
1. 30-day advance notice to MARS/NAOS teams
2. Version bump in contract (v1.1 → v2.0)
3. Migration guide

**Breaking changes include:**
- Removing capabilities
- Changing error taxonomy
- Changing idempotency behavior
- Changing credential lookup logic

### 9.2 Non-Breaking Changes

**Stargate MAY make these changes without notice:**
- Adding new capabilities
- Adding new fields to response `outputs`
- Adding new error `details` fields
- Improving performance

**MARS/NAOS should:**
- Ignore unknown fields in responses
- NOT rely on undocumented behavior

### 9.3 Current Compatibility Aliases

**Backward-compatible aliases (for legacy MARS code):**

| Alias (Unprefixed) | Routes To | Notes |
|--------------------|-----------|-------|
| `vendor.create` | `qb.vendor.create` | QuickBooks vendor |
| `vendor.list` | `qb.vendor.list` | QuickBooks vendor list |
| `customer.create` | `qb.customer.create` | QuickBooks customer |
| `invoice.create` | `qb.invoice.create` | QuickBooks invoice |
| `invoice.list` | `qb.invoice.list` | QuickBooks invoice list |
| `bill.create` | `qb.bill.create` | QuickBooks bill |
| `payment.create` | `qb.payment.create` | QuickBooks payment |

**⚠️ DEPRECATION NOTICE:**
- These aliases will be removed in Stargate v2.0 (6 months)
- MARS should migrate to namespaced keys (`qb.*`, `stripe.*`, etc.)

---

## 10. Security Contract

### 10.1 Authentication

**Stargate requires:**
- `X-API-Key` header on ALL requests (except `/health` and `/metrics`)

**MARS/NAOS MUST:**
- Store API key securely (environment variable, secrets manager)
- NOT log API key in plaintext
- Rotate API key quarterly

### 10.2 Credential Encryption

**Stargate GUARANTEES:**
- All OAuth tokens encrypted at rest (Fernet AES-128)
- Encryption key stored in `ENCRYPTION_KEY` environment variable
- Credentials isolated by `org_id:user_id:service:credential_type`

**MARS/NAOS can assume:**
- Credentials never shared across orgs/users
- Credentials never logged in plaintext
- Credentials automatically encrypted on write

### 10.3 Data Isolation

**Multi-tenant guarantee:**
- `org_abc123` cannot access credentials/data for `org_xyz789`
- Enforced by composite key in database
- No cross-org data leakage

---

## 11. Open Questions (Require Agreement)

### 11.1 Observability

**Q1: Distributed tracing?**
- Should we use OpenTelemetry for request correlation?
- Should Stargate propagate `trace_id` from MARS to external APIs?

**Q2: Log aggregation?**
- Where should Stargate logs go? (CloudWatch, Datadog, etc.)
- Should Stargate use structured JSON logging?

### 11.2 Error Handling

**Q3: Partial success?**
- If bulk operation fails midway, should Stargate return partial results?
- Example: `qb.vendors.create_batch` creates 5/10 vendors before error

**Q4: Error enrichment?**
- Should Stargate include raw API error responses in `details`?
- How much detail is too much?

### 11.3 Idempotency

**Q5: TTL configuration?**
- Is 24 hours the right TTL for idempotency cache?
- Should it be configurable per capability?

**Q6: Cache invalidation?**
- Should MARS be able to invalidate cached responses?
- Use case: User fixes input and wants to retry immediately

### 11.4 Performance

**Q7: Rate limiting?**
- Should Stargate rate-limit MARS requests?
- Or should MARS self-regulate?

**Q8: Queueing?**
- Should Stargate queue requests when external API is rate-limited?
- Or return error immediately and let MARS retry?

### 11.5 Capability Evolution

**Q9: Versioning strategy?**
- URL-based (`/api/v2/execute`)?
- Capability key suffix (`qb.customer.create@v2`)?
- Header-based (`X-API-Version: 2`)?

**Q10: Deprecation policy?**
- How long to support deprecated capabilities?
- 3 months? 6 months? 12 months?

---

## 12. Next Steps

### 12.1 Approval Process

1. **Review by teams:**
   - [ ] Stargate team reviews technical feasibility
   - [ ] MARS team reviews integration requirements
   - [ ] NAOS team reviews agent orchestration needs

2. **Answer open questions:**
   - Schedule alignment meeting
   - Document decisions in this contract
   - Get sign-off from tech leads

3. **Implementation:**
   - [ ] Stargate implements Phase 1 production fixes
   - [ ] MARS updates retry logic to use error taxonomy
   - [ ] Integration tests between MARS ↔ Stargate

### 12.2 Contract Updates

**Process for updating this contract:**
1. Propose change via GitHub PR
2. Review with all teams
3. Update version number
4. Communicate breaking changes 30 days in advance

**Contract Versions:**
- **v1.0** - Initial contract (Stargate Command Contract)
- **v1.1** - This document (adds retry strategy, idempotency details, open questions)
- **v2.0** - Future (post-MAP architecture)

---

## 13. Summary

**What MARS/NAOS can RELY on:**
- ✅ Standardized error taxonomy with retry strategies
- ✅ Idempotency via `turn_id` for 24 hours
- ✅ Automatic OAuth token refresh
- ✅ Multi-tenant credential isolation
- ✅ < 30s timeout on all external API calls
- ✅ Health check endpoint for monitoring

**What MARS/NAOS MUST do:**
- ✅ Send `turn_id` for idempotent operations
- ✅ Use `error_code` and `retry_strategy` to determine retry behavior
- ✅ Handle `CREDENTIALS_MISSING` by prompting user OAuth
- ✅ Respect `retry_after` in `RateLimitError`
- ✅ Send `X-API-Key` header for authentication

**What needs AGREEMENT:**
- ⏳ Distributed tracing strategy (OpenTelemetry?)
- ⏳ Capability versioning approach
- ⏳ Partial success handling
- ⏳ Rate limiting strategy
- ⏳ Idempotency TTL configuration

---

## Changelog

### v1.2 - February 3, 2026
**Added 36 new capabilities:**
- **Google Workspace (6):** Drive file delete/search, Calendar get event/list calendars, Sheets batch get ranges/create spreadsheet
- **Microsoft 365 (4):** OneDrive file delete/search, Outlook Calendar get event/list calendars
- **Dropbox (3):** File delete, move, search
- **DocuSign (3):** Envelope audit trail, signing URL, status details
- **Power BI (2):** List workspaces, delete datasets
- **Stripe (6):** Coupons (create/retrieve/update/delete), Events (list/retrieve)
- **QuickBooks (6):** Journal entries (CRUD operations)
- **HubSpot (6):** Associations, notes, owners, pipelines, properties, tickets

**Total:** 770 capabilities across 34 services

### v1.1 - November 23, 2025
- Added retry strategy classification
- Clarified idempotency contract with `turn_id`
- Added error taxonomy details
- Documented open questions for alignment

### v1.0 - Initial Release
- Basic execution contract
- Error classification
- Multi-tenant credential isolation

---

**Contact:**
- Stargate questions: [Stargate team]
- MARS questions: [MARS team]
- NAOS questions: [NAOS team]
- Contract disputes: [Engineering leads alignment meeting]
