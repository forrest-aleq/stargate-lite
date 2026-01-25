# Stargate API Specification for N3

**Version:** 0.9.0
**Base URL:** `https://stargate.up.railway.app` (production) | `http://localhost:8001` (local)
**Last Updated:** 2025-01-24

---

## Authentication

All authenticated endpoints require the `X-API-Key` header:

```
X-API-Key: <STARGATE_API_KEY>
```

N3 environment variable: `STARGATE_API_KEY` must match Stargate's `API_SECRET_KEY`.

**Note:** OAuth authorize endpoints (`/oauth/*/authorize`) are public - no API key required (browser redirects cannot set headers).

---

## Endpoints Overview

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /health` | No | Health check |
| `POST /api/v1/connectors/status` | Yes | Check which integrations are connected |
| `GET /oauth/{provider}/authorize` | No | Start OAuth flow (browser redirect) |
| `GET /oauth/{provider}/callback` | No | OAuth callback (handled by Stargate) |
| `POST /api/v1/credentials/status` | Yes | Check if credential exists for capability |
| `GET /api/v1/credentials/metadata` | Yes | Get credential metadata (no tokens) |
| `POST /api/v1/credentials/revoke` | Yes | Disconnect an integration |
| `GET /api/v1/capabilities` | Yes | List all capabilities |
| `POST /api/v1/execute` | Yes | Execute a capability (Baby MARS only) |

---

## 1. Health Check

**Purpose:** Verify Stargate is running

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.9.0",
  "capabilities_count": 614,
  "timestamp": "2025-01-24T10:00:00.000000",
  "services": {
    "quickbooks": "ok",
    "stripe": "ok",
    "hubspot": "ok",
    "google": "ok",
    "slack": "ok"
  }
}
```

---

## 2. Check Connector Status

**Purpose:** Settings page - show which integrations are connected for a user

```
POST /api/v1/connectors/status
Headers:
  X-API-Key: <STARGATE_API_KEY>
  Content-Type: application/json

Body:
{
  "org_id": "org_abc123",
  "user_id": "user_xyz789",
  "services": ["quickbooks", "xero", "stripe", "gmail", "slack"]
}
```

**Response:**
```json
{
  "connectors": [
    {
      "kind": "quickbooks",
      "display_name": "QuickBooks",
      "status": "connected",
      "requires_oauth": true,
      "credential_type": "customer",
      "token_expiry": "2025-03-01T12:00:00",
      "last_updated": "2025-01-24T10:00:00"
    },
    {
      "kind": "gmail",
      "display_name": "Gmail",
      "status": "missing",
      "requires_oauth": true,
      "credential_type": "agent",
      "token_expiry": null,
      "last_updated": null
    }
  ],
  "all_connected": false,
  "missing_count": 1
}
```

**Status Values:**
- `connected` - Valid credential exists
- `expired` - Credential exists but token expired
- `missing` - No credential stored

---

## 3. OAuth Flow

### 3.1 Start OAuth (Authorize)

**Purpose:** User clicks "Connect" button - redirect to OAuth provider

```
GET /oauth/{provider}/authorize?org_id={org_id}&user_id={user_id}&credential_type={type}
```

**Parameters:**
| Param | Required | Description |
|-------|----------|-------------|
| `org_id` | Yes | Organization ID |
| `user_id` | Yes | User ID |
| `credential_type` | No | `customer` (default) or `agent` |

**Providers:**
| Provider | Endpoint |
|----------|----------|
| QuickBooks | `/oauth/quickbooks/authorize` |
| Xero | `/oauth/xero/authorize` |
| HubSpot | `/oauth/hubspot/authorize` |
| Gmail/Google | `/oauth/google/authorize` |
| Slack | `/oauth/slack/authorize` |
| Shopify | `/oauth/shopify/authorize` (requires `shop` param) |
| Square | `/oauth/square/authorize` |
| Gusto | `/oauth/gusto/authorize` |
| DocuSign | `/oauth/docusign/authorize` |
| Airtable | `/oauth/airtable/authorize` |
| Linear | `/oauth/linear/authorize` |
| Notion | `/oauth/notion/authorize` |

**Response:** 302 Redirect to OAuth provider

**N3 Implementation:**
```typescript
function handleConnect(provider: string, orgId: string, userId: string) {
  const url = `${STARGATE_URL}/oauth/${provider}/authorize?org_id=${orgId}&user_id=${userId}`;
  window.location.href = url;
}
```

### 3.2 OAuth Callback

**Purpose:** OAuth provider redirects here after user authorizes

```
GET /oauth/{provider}/callback?code={code}&state={state}
```

Stargate handles this automatically:
1. Exchanges code for tokens
2. Stores encrypted credentials in Stargate DB
3. Redirects to N3 success URL

**Redirect on Success:**
```
{N3_SUCCESS_URL}/settings/integrations?connected={provider}
```

**Redirect on Error:**
```
{N3_SUCCESS_URL}/settings/integrations?error=oauth_failed&provider={provider}
```

**Environment Variable (Stargate):**
```
N3_SUCCESS_URL=https://console.aleq.com
```

---

## 4. Check Credential Status

**Purpose:** Verify credential exists before showing a capability

```
POST /api/v1/credentials/status
Headers:
  X-API-Key: <STARGATE_API_KEY>
  Content-Type: application/json

Body:
{
  "org_id": "org_abc123",
  "user_id": "user_xyz789",
  "capability_key": "vendor.create"
}
```

**Response (credential exists):**
```json
{
  "credential_available": true,
  "credential_type": "customer",
  "access_pattern": null,
  "token_expiry": "2025-03-01T12:00:00",
  "requires_setup": false,
  "delegation_supported": false
}
```

**Response (credential missing):**
```json
{
  "credential_available": false,
  "credential_type": "customer",
  "requires_setup": true,
  "message": "Missing customer credential for quickbooks",
  "delegation_supported": false
}
```

---

## 5. Get Credential Metadata

**Purpose:** Get details about a stored credential (without exposing tokens)

```
GET /api/v1/credentials/metadata?org_id={org_id}&user_id={user_id}&service={service}
Headers:
  X-API-Key: <STARGATE_API_KEY>
```

**Query Parameters:**
| Param | Required | Description |
|-------|----------|-------------|
| `org_id` | Yes | Organization ID |
| `user_id` | Yes | User ID |
| `service` | Yes | Service name (e.g., `quickbooks`) |
| `credential_type` | No | `customer` (default) or `agent` |

**Response:**
```json
{
  "exists": true,
  "service": "quickbooks",
  "credential_type": "customer",
  "access_pattern": null,
  "token_expiry": "2025-03-01T12:00:00",
  "realm_id": "9130348291234567",
  "extra_data": {}
}
```

---

## 6. Revoke Credential (Disconnect)

**Purpose:** User clicks "Disconnect" - remove stored credential

```
POST /api/v1/credentials/revoke
Headers:
  X-API-Key: <STARGATE_API_KEY>
  Content-Type: application/json

Body:
{
  "org_id": "org_abc123",
  "user_id": "user_xyz789",
  "service": "quickbooks"
}
```

**Response:**
```json
{
  "status": "revoked",
  "service": "quickbooks"
}
```

> **Note:** This endpoint needs to be implemented. See [Implementation Status](#implementation-status).

---

## 7. List Capabilities

**Purpose:** Discovery - what can Stargate do?

```
GET /api/v1/capabilities
Headers:
  X-API-Key: <STARGATE_API_KEY>
```

**Response:**
```json
{
  "capabilities": [
    {
      "key": "vendor.create",
      "tool_name": "quickbooks.create_vendor",
      "description": "Create a new vendor in QuickBooks",
      "service": "quickbooks",
      "requires_oauth": true
    },
    {
      "key": "fci.cash",
      "tool_name": "fci.get_cash",
      "description": "Get total cash position across all connected bank accounts",
      "service": "fci",
      "requires_oauth": false
    }
  ],
  "count": 614
}
```

---

## 8. Execute Capability (Baby MARS Only)

**Purpose:** Execute a capability - called by Baby MARS, NOT N3 directly

```
POST /api/v1/execute
Headers:
  X-API-Key: <STARGATE_API_KEY>
  X-Session-ID: <session_id>  # Optional, for analytics correlation
  Content-Type: application/json

Body:
{
  "capability_key": "vendor.create",
  "org_id": "org_abc123",
  "user_id": "user_xyz789",
  "turn_id": "turn_01HZ8Y3K5G4N2M6X9W7Q",
  "args": {
    "vendor_name": "Acme Inc.",
    "email": "billing@acme.com"
  }
}
```

**Response (success):**
```json
{
  "status": "success",
  "capability_key": "vendor.create",
  "tool_used": "quickbooks.create_vendor",
  "outputs": {
    "vendor_id": "qb:123-xyz",
    "status": "pending_w9",
    "created_at": "2025-01-24T12:00:00Z"
  },
  "logs": ["Successfully created vendor in QuickBooks"],
  "credential_type": "customer",
  "timestamp": "2025-01-24T12:00:00.123456"
}
```

**Response (error):**
```json
{
  "status": "error",
  "error_code": "CREDENTIAL_MISSING",
  "error_message": "No QuickBooks credentials found for this user",
  "retry_strategy": "none",
  "capability_key": "vendor.create",
  "turn_id": "turn_01HZ8Y3K5G4N2M6X9W7Q"
}
```

**Rate Limiting:** 100 requests/minute per org_id. Response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1706097600
```

---

## Available Services

| Service | OAuth Provider | Capabilities |
|---------|---------------|--------------|
| `quickbooks` | QuickBooks Online | 45+ (vendors, bills, invoices, reports) |
| `xero` | Xero | 30+ (contacts, invoices, bank) |
| `stripe` | Stripe | 25+ (payments, payouts, customers) |
| `hubspot` | HubSpot | 20+ (contacts, deals, companies) |
| `gmail` | Google | 5+ (send, read, labels) |
| `slack` | Slack | 15+ (messages, channels, users) |
| `shopify` | Shopify | 20+ (orders, products, customers) |
| `square` | Square | 15+ (payments, orders, locations) |
| `gusto` | Gusto | 10+ (employees, payroll, benefits) |
| `docusign` | DocuSign | 5+ (envelopes, templates) |
| `airtable` | Airtable | 5+ (bases, records) |
| `netsuite` | NetSuite | 15+ (journal entries, vendor bills) |
| `sage_intacct` | Sage Intacct | 25+ (GL, AP, AR, cash) |
| `billcom` | Bill.com | 10+ (bills, vendors, payments) |

**Total:** 570+ capabilities across 22 platforms

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `CAPABILITY_NOT_FOUND` | 400 | Unknown capability_key |
| `CREDENTIAL_MISSING` | 401 | No credential stored for service |
| `CREDENTIAL_EXPIRED` | 401 | Token expired, needs re-auth |
| `CREDENTIAL_INVALID` | 401 | Token rejected by provider |
| `EXTERNAL_API_ERROR` | 502 | Provider API returned error |
| `RATE_LIMIT` | 429 | Too many requests |
| `VALIDATION_ERROR` | 400 | Invalid request parameters |

---

## Implementation Status

| Endpoint | Status |
|----------|--------|
| `GET /health` | ✅ Implemented |
| `POST /api/v1/connectors/status` | ✅ Implemented |
| `GET /oauth/*/authorize` | ✅ Implemented (all providers) |
| `GET /oauth/*/callback` | ✅ Implemented (all providers) |
| `POST /api/v1/credentials/status` | ✅ Implemented |
| `GET /api/v1/credentials/metadata` | ✅ Implemented |
| `POST /api/v1/credentials/revoke` | ✅ Implemented |
| `GET /api/v1/capabilities` | ✅ Implemented |
| `POST /api/v1/execute` | ✅ Implemented |

---

## N3 Integration Checklist

### Environment Variables
```bash
# Add to Vercel
STARGATE_URL=https://stargate.up.railway.app
STARGATE_API_KEY=<get from Stargate team>
```

### Code Changes

1. **Settings Page - Fetch Integration Status**
```typescript
// pages/api/integrations/status.ts
const res = await fetch(`${process.env.STARGATE_URL}/api/v1/connectors/status`, {
  method: 'POST',
  headers: {
    'X-API-Key': process.env.STARGATE_API_KEY!,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    org_id: session.orgId,
    user_id: session.userId,
    services: ['quickbooks', 'xero', 'stripe', 'gmail', 'slack'],
  }),
});
```

2. **Connect Button**
```typescript
// components/IntegrationCard.tsx
const handleConnect = (provider: string) => {
  const url = `${process.env.NEXT_PUBLIC_STARGATE_URL}/oauth/${provider}/authorize`;
  const params = new URLSearchParams({
    org_id: session.orgId,
    user_id: session.userId,
  });
  window.location.href = `${url}?${params}`;
};
```

3. **Success Handler**
```typescript
// app/settings/integrations/page.tsx
const searchParams = useSearchParams();
const connected = searchParams.get('connected');
const error = searchParams.get('error');

useEffect(() => {
  if (connected) {
    toast.success(`${connected} connected successfully`);
    refetchIntegrations();
  }
  if (error) {
    toast.error(`Failed to connect: ${error}`);
  }
}, [connected, error]);
```

4. **Disconnect Button**
```typescript
// pages/api/integrations/disconnect.ts
const res = await fetch(`${process.env.STARGATE_URL}/api/v1/credentials/revoke`, {
  method: 'POST',
  headers: {
    'X-API-Key': process.env.STARGATE_API_KEY!,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    org_id: req.body.orgId,
    user_id: req.body.userId,
    service: req.body.service,
  }),
});
```

---

## Security Notes

1. **API Key is server-side only** - Never expose `STARGATE_API_KEY` to browser
2. **OAuth state parameter** - Encodes `org_id:user_id:credential_type`, validated on callback
3. **Credentials encrypted at rest** - Fernet symmetric encryption in Stargate DB
4. **No cross-org access** - Every request validated against org_id

---

## Questions?

Contact the Stargate team or see `/docs/DEPLOYMENT_GUIDE.md` for full deployment instructions.
