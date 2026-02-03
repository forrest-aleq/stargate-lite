# N3 ↔ Stargate Integration Contract

## Executive Summary

**Current State:** N3 handles integrations via Supabase directly. OAuth callbacks are NOT implemented. Stargate is not involved.

**Target State:** N3 calls Stargate directly for all integration operations. Stargate owns OAuth flows and credential storage. N3 is a thin UI layer.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         N3 Frontend                              │
│  Settings > Integrations Page                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│   Baby MARS     │                 │    Stargate     │
│   (Cognition)   │                 │ (Integrations)  │
│                 │                 │                 │
│ - /birth        │                 │ - /oauth/*      │
│ - /chat         │                 │ - /connectors   │
│ - /sessions     │                 │ - /credentials  │
│                 │                 │ - /capabilities │
└─────────────────┘                 └─────────────────┘
```

**Rule:** Settings page NEVER talks to Baby MARS. Chat NEVER talks to Stargate directly.

---

## Environment Variables

### N3 (Vercel)

```bash
# Cognitive (existing)
BABY_MARS_URL=https://baby-mars.up.railway.app
BABY_MARS_API_KEY=<key1>

# Integrations (NEW)
STARGATE_URL=https://stargate.up.railway.app
STARGATE_API_KEY=<key2>
```

### Stargate (Railway)

```bash
API_SECRET_KEY=<key2>  # Must match STARGATE_API_KEY
```

---

## Endpoints: N3 → Stargate

### 1. List Connected Integrations

**Purpose:** Show integration cards on Settings page

```
GET /api/v1/connectors/status
Headers:
  X-API-Key: <STARGATE_API_KEY>
  Content-Type: application/json

Body:
{
  "org_id": "org_xxx",
  "user_id": "user_xxx",
  "services": ["quickbooks", "xero", "stripe", "plaid", "mercury", "slack", "gmail", "gusto", "shopify", "square", "docusign", "airtable"]
}

Response:
{
  "connectors": [
    {
      "kind": "quickbooks",
      "status": "connected",
      "credential_status": "valid"
    },
    {
      "kind": "stripe",
      "status": "disconnected",
      "credential_status": "missing"
    }
  ],
  "all_connected": false,
  "missing_count": 5
}
```

### 2. Get OAuth URL

**Purpose:** User clicks "Connect" → redirect to OAuth provider

```
GET /oauth/{provider}/authorize?org_id={org_id}&user_id={user_id}
Headers:
  X-API-Key: <STARGATE_API_KEY>

Providers:
  - /oauth/quickbooks/authorize
  - /oauth/xero/authorize        # 61 capabilities, deep links v0.11.0+
  - /oauth/stripe/authorize
  - /oauth/plaid/authorize
  - /oauth/mercury/authorize
  - /oauth/slack/authorize
  - /oauth/google/authorize (Gmail)
  - /oauth/hubspot/authorize
  - /oauth/gusto/authorize
  - /oauth/shopify/authorize
  - /oauth/square/authorize
  - /oauth/docusign/authorize
  - /oauth/airtable/authorize

Response: 302 Redirect to OAuth provider
```

### 3. OAuth Callback

**Purpose:** OAuth provider redirects back after user authorizes

```
GET /oauth/{provider}/callback?code={code}&state={state}

Stargate:
  1. Exchanges code for tokens
  2. Stores credentials in Stargate DB
  3. Redirects to N3 success page

Redirect: {N3_URL}/settings/integrations?connected={provider}
```

### 4. Disconnect Integration

**Purpose:** User clicks "Disconnect"

```
POST /api/v1/credentials/revoke
Headers:
  X-API-Key: <STARGATE_API_KEY>
  Content-Type: application/json

Body:
{
  "org_id": "org_xxx",
  "user_id": "user_xxx",
  "service": "quickbooks"
}

Response:
{
  "status": "revoked",
  "service": "quickbooks"
}
```

### 5. Check Credential Health

**Purpose:** Show warning if token expired

```
POST /api/v1/credentials/status
Headers:
  X-API-Key: <STARGATE_API_KEY>
  Content-Type: application/json

Body:
{
  "org_id": "org_xxx",
  "user_id": "user_xxx",
  "capability_key": "qb.invoice.list"
}

Response:
{
  "credential_available": true,
  "credential_type": "customer",
  "requires_setup": false
}
```

### 6. List Available Capabilities

**Purpose:** Show what actions are possible per integration

```
GET /api/v1/capabilities
Headers:
  X-API-Key: <STARGATE_API_KEY>

Response:
[
  {
    "key": "qb.invoice.list",
    "service": "quickbooks",
    "description": "List invoices"
  },
  {
    "key": "qb.vendor.create",
    "service": "quickbooks",
    "description": "Create vendor"
  }
  // ... 614 total (v0.11.0)
]
```

---

## N3 Implementation Changes

### 1. New API Route: `/api/integrations/route.ts`

Replace Supabase calls with Stargate calls:

```typescript
// OLD: Direct Supabase
const { data } = await supabase.from('integrations').select('*')

// NEW: Call Stargate
const res = await fetch(`${STARGATE_URL}/api/v1/connectors/status`, {
  method: 'POST',
  headers: {
    'X-API-Key': STARGATE_API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    org_id: orgId,
    user_id: userId,
    services: ['quickbooks', 'xero', 'stripe', 'plaid', 'mercury']
  })
})
```

### 2. OAuth Flow

```typescript
// Connect button handler
async function handleConnect(provider: string) {
  // Redirect directly to Stargate OAuth
  const url = `${STARGATE_URL}/oauth/${provider}/authorize?org_id=${orgId}&user_id=${userId}`
  window.location.href = url
}
```

### 3. Remove OAuth Callbacks from N3

N3 does NOT need `/api/integrations/callback/*` routes. Stargate handles callbacks and redirects back to N3.

### 4. Success Page Handler

```typescript
// src/app/(dashboard)/settings/integrations/page.tsx
const searchParams = useSearchParams()
const connected = searchParams.get('connected')

useEffect(() => {
  if (connected) {
    toast.success(`${connected} connected successfully`)
    // Refresh integration list
    fetchIntegrations()
  }
}, [connected])
```

---

## Stargate Implementation Changes

### 1. Add Callback Redirect

After successful OAuth, redirect to N3:

```python
@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str):
    # Exchange code for tokens
    tokens = await exchange_oauth_code(provider, code)

    # Store credentials
    await store_credentials(org_id, user_id, provider, tokens)

    # Redirect to N3
    n3_url = os.getenv("N3_SUCCESS_URL", "https://console.aleq.com")
    return RedirectResponse(f"{n3_url}/settings/integrations?connected={provider}")
```

### 2. Add Revoke Endpoint

```python
@router.post("/api/v1/credentials/revoke")
async def revoke_credentials(request: RevokeRequest):
    await delete_credentials(request.org_id, request.user_id, request.service)
    return {"status": "revoked", "service": request.service}
```

### 3. Environment Variable

```bash
N3_SUCCESS_URL=https://console.aleq.com  # or staging.aleq.dev
```

---

## Migration Plan

### Phase 1: Wire Up (No Breaking Changes)
1. Add `STARGATE_URL` and `STARGATE_API_KEY` to N3 env
2. Create new `/api/stargate/integrations` route in N3 that calls Stargate
3. Test alongside existing Supabase flow

### Phase 2: Switch Over
1. Update Settings page to use new Stargate-backed route
2. Remove Supabase integration queries
3. Keep Supabase table for audit log only

### Phase 3: Cleanup
1. Remove dead code from N3
2. Drop `integrations` table from Supabase (or archive)
3. Document final architecture

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| API key exposure | `STARGATE_API_KEY` is server-side only, never exposed to browser |
| OAuth state tampering | Stargate validates state parameter matches session |
| Token storage | Credentials stored in Stargate DB, not N3/Supabase |
| Cross-org access | Every request includes org_id, validated by Stargate |

---

## Testing Checklist

- [ ] N3 can fetch connector status from Stargate
- [ ] OAuth redirect works for each provider
- [ ] OAuth callback stores credentials in Stargate
- [ ] Callback redirects to N3 with success param
- [ ] Disconnect removes credentials from Stargate
- [ ] Credential health check returns accurate status
- [ ] Error states handled (expired token, revoked access)

---

## Summary

| Component | Responsibility |
|-----------|---------------|
| N3 | UI only. Renders integration cards, initiates OAuth redirects |
| Stargate | OAuth flows, credential storage, capability registry |
| Baby MARS | Cognitive operations only. Never involved in Settings |
| Supabase | User auth, org membership. NOT integration credentials |

**Key Principle:** Stargate is the single source of truth for integrations. N3 is a thin client.
