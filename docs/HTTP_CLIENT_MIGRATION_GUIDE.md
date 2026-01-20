# HTTP Client Migration Guide
**Date:** November 23, 2025
**Purpose:** Guide for migrating connectors to use centralized `StargateHTTPClient`

---

## Why Migrate?

The new centralized HTTP client provides:
- ✅ **Automatic timeouts** (5s connect, 30s read) - prevents hanging on slow APIs
- ✅ **Connection pooling** (20 pools × 100 connections) - TCP connection reuse
- ✅ **JSON parsing safety** - graceful handling of malformed responses
- ✅ **Retry logic** - automatic retries with exponential backoff
- ✅ **Error classification** - maps HTTP codes to StargateError taxonomy
- ✅ **Future-ready** - metrics instrumentation coming soon

**Impact:** Fixes 1,374 HTTP calls across 20+ connector files

---

## Migration Pattern

### BEFORE (Current Pattern)

```python
# app/connectors/quickbooks.py - OLD CODE

import requests
from typing import Dict, Any

def create_vendor(self, org_id: str, user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
    cred = self._get_access_token(org_id, user_id)
    realm_id = cred["realm_id"]

    vendor_data = {
        "DisplayName": args.get("vendor_name"),
        "PrimaryEmailAddr": {"Address": args.get("email")}
    }

    url = f"{self.base_url}/{realm_id}/vendor"

    # ❌ NO TIMEOUT - can hang forever
    # ❌ NO ERROR CLASSIFICATION - generic exception
    # ❌ NO JSON PARSING SAFETY - crashes on malformed response
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {cred['access_token']}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        json=vendor_data
    )

    # ❌ Generic error handling
    if response.status_code not in [200, 201]:
        raise Exception(f"QuickBooks API error: {response.status_code} - {response.text}")

    # ❌ Unsafe JSON parsing
    result = response.json()
    vendor = result.get("Vendor", {})

    return {
        "vendor_id": f"qb:{vendor.get('Id')}",
        "display_name": vendor.get("DisplayName")
    }
```

### AFTER (With Centralized Client)

```python
# app/connectors/quickbooks.py - NEW CODE

from app.http_client import http_client  # Import centralized client
from typing import Dict, Any

def create_vendor(self, org_id: str, user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
    cred = self._get_access_token(org_id, user_id)
    realm_id = cred["realm_id"]

    vendor_data = {
        "DisplayName": args.get("vendor_name"),
        "PrimaryEmailAddr": {"Address": args.get("email")}
    }

    url = f"{self.base_url}/{realm_id}/vendor"

    # ✅ AUTOMATIC TIMEOUTS (5s connect, 30s read)
    # ✅ ERROR CLASSIFICATION (401 → CredentialInvalidError, 429 → RateLimitError, etc.)
    # ✅ JSON PARSING SAFETY (graceful error on malformed response)
    # ✅ CONNECTION POOLING (TCP reuse)
    # ✅ RETRY LOGIC (exponential backoff on transient failures)
    result = http_client.post(
        url=url,
        service="quickbooks",  # Required for error reporting
        headers={
            "Authorization": f"Bearer {cred['access_token']}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        json=vendor_data,
        parse_json=True  # Automatically parse JSON (default: True)
    )

    # Result is already parsed JSON dict (or StargateError raised)
    vendor = result.get("Vendor", {})

    return {
        "vendor_id": f"qb:{vendor.get('Id')}",
        "display_name": vendor.get("DisplayName")
    }
```

**What Changed:**
1. ✅ Replace `import requests` with `from app.http_client import http_client`
2. ✅ Replace `requests.post(url, ...)` with `http_client.post(url, service="quickbooks", ...)`
3. ✅ Add `service` parameter (required for error classification)
4. ✅ Remove manual `response.status_code` checks (handled by client)
5. ✅ Remove manual `response.json()` calls (automatic if `parse_json=True`)

---

## Migration Examples

### Example 1: GET Request

**Before:**
```python
response = requests.get(
    f"{BASE_URL}/api/endpoint",
    headers={"Authorization": f"Bearer {token}"}
)
if response.status_code != 200:
    raise Exception(f"Error: {response.text}")
data = response.json()
```

**After:**
```python
data = http_client.get(
    url=f"{BASE_URL}/api/endpoint",
    service="service_name",
    headers={"Authorization": f"Bearer {token}"}
)
# data is already parsed JSON dict
```

---

### Example 2: POST with Custom Timeout

**Before:**
```python
response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=60  # Custom timeout
)
data = response.json()
```

**After:**
```python
data = http_client.post(
    url=url,
    service="service_name",
    headers=headers,
    json=payload,
    timeout=(5, 60)  # Custom timeout: (connect=5s, read=60s)
)
```

---

### Example 3: Don't Parse JSON (Return Response Object)

**Before:**
```python
response = requests.get(url, headers=headers)
if response.status_code == 200:
    return response.content  # Raw bytes
```

**After:**
```python
response = http_client.get(
    url=url,
    service="service_name",
    headers=headers,
    parse_json=False  # Don't parse JSON, return Response object
)
return response.content  # Raw bytes
```

---

### Example 4: Token Refresh (OAuth)

**Before:**
```python
response = requests.post(
    TOKEN_URL,
    headers={"Accept": "application/json"},
    auth=(client_id, client_secret),
    data={"grant_type": "refresh_token", "refresh_token": refresh_token}
)

if response.status_code != 200:
    raise Exception(f"Failed to refresh token: {response.text}")

token_data = response.json()
```

**After:**
```python
token_data = http_client.post(
    url=TOKEN_URL,
    service="quickbooks",
    headers={"Accept": "application/json"},
    auth=(client_id, client_secret),
    data={"grant_type": "refresh_token", "refresh_token": refresh_token}
)
# If token refresh fails, raises CredentialInvalidError automatically
```

---

## Error Handling Changes

### Automatic Error Classification

The HTTP client automatically classifies errors:

| HTTP Status | Old Behavior | New Behavior |
|-------------|--------------|--------------|
| 401 | `Exception("API error: 401")` | `CredentialInvalidError` (DO_NOT_RETRY) |
| 403 | `Exception("API error: 403")` | `PermissionDeniedError` (DO_NOT_RETRY) |
| 404 | `Exception("API error: 404")` | `NotFoundError` (DO_NOT_RETRY) |
| 429 | `Exception("API error: 429")` | `RateLimitError` (RETRY_AFTER_DELAY) |
| 500-504 | `Exception("API error: 500")` | `NetworkError` (RETRY_WITH_BACKOFF) |
| Timeout | Hangs forever | `NetworkError` (RETRY_WITH_BACKOFF) |
| Connection error | `Exception("Connection failed")` | `NetworkError` (RETRY_WITH_BACKOFF) |
| JSON parse error | Crash | `ExecutionError` with raw response |

### Handling Errors in Connector

**You don't need to catch errors** - let them propagate:

```python
def create_vendor(self, org_id, user_id, args):
    cred = self._get_access_token(org_id, user_id)

    # This will raise StargateError on failure - let it propagate
    result = http_client.post(
        url=f"{self.base_url}/vendor",
        service="quickbooks",
        headers={"Authorization": f"Bearer {cred['access_token']}"},
        json=vendor_data
    )

    return {"vendor_id": result["Vendor"]["Id"]}
```

**Only catch errors if you need custom handling:**

```python
from app.errors import CredentialInvalidError

def create_vendor(self, org_id, user_id, args):
    try:
        cred = self._get_access_token(org_id, user_id)
        result = http_client.post(...)
        return {"vendor_id": result["Vendor"]["Id"]}
    except CredentialInvalidError:
        # Token invalid - try refreshing
        self._refresh_token(org_id, user_id)
        # Retry once with new token
        cred = self._get_access_token(org_id, user_id)
        result = http_client.post(...)
        return {"vendor_id": result["Vendor"]["Id"]}
```

---

## Connector Migration Checklist

For each connector file (`app/connectors/*.py`):

### 1. Update Imports
```python
# Add at top of file:
from app.http_client import http_client
```

### 2. Replace All `requests.*` Calls

**Find all:**
- `requests.get(`
- `requests.post(`
- `requests.put(`
- `requests.patch(`
- `requests.delete(`

**Replace with:**
- `http_client.get(url, service="service_name", ...)`
- `http_client.post(url, service="service_name", ...)`
- etc.

**CRITICAL:** Always add `service` parameter with the service name

### 3. Remove Manual Error Checks

**Delete these patterns:**
```python
# DELETE THIS:
if response.status_code != 200:
    raise Exception(f"Error: {response.text}")

# DELETE THIS:
if response.status_code not in [200, 201]:
    raise Exception(...)
```

**HTTP client handles this automatically**

### 4. Remove Manual JSON Parsing

**Delete these patterns:**
```python
# DELETE THIS:
result = response.json()

# DELETE THIS:
try:
    data = response.json()
except json.JSONDecodeError:
    raise Exception("Invalid JSON")
```

**HTTP client parses JSON automatically (unless `parse_json=False`)**

### 5. Update Exception Handling

**Replace generic exceptions with StargateError types:**

```python
# OLD:
from app.errors import CredentialMissingError
if not cred:
    raise ValueError(f"No credentials found...")

# NEW:
from app.errors import CredentialMissingError
if not cred:
    raise CredentialMissingError("service_name", org_id, user_id)
```

### 6. Test Connector

After migration, test:
- ✅ Happy path (successful API call)
- ✅ 401 error (token expired)
- ✅ 429 error (rate limit)
- ✅ Network timeout
- ✅ Malformed JSON response

---

## Connector Priority

Migrate connectors in this order (based on usage frequency):

**High Priority (Most Used):**
1. ✅ quickbooks.py - 39 HTTP calls
2. ✅ hubspot.py - 5 HTTP calls
3. ✅ stripe_connector.py - Uses Stripe SDK (defer)
4. ✅ netsuite.py - 5 HTTP calls
5. ✅ gmail.py - Uses Google SDK (defer)

**Medium Priority:**
6. linear.py
7. monday.py
8. clickup.py
9. plaid.py
10. asana.py

**Low Priority:**
11-20. Remaining connectors

**SDK-Based (Defer):**
- stripe_connector.py - Uses Stripe SDK (investigate SDK timeout config)
- gmail.py - Uses Google API client (investigate SDK timeout config)
- slack.py - Uses Slack SDK

---

## SDK-Based Connectors

Some connectors use third-party SDKs instead of raw `requests`:

**Examples:**
- Stripe SDK: `stripe.Charge.create(...)`
- Google API Client: `service.users().messages().list(...)`
- Slack SDK: `slack_client.chat_postMessage(...)`

**For SDK-based connectors:**
1. Check if SDK supports timeout configuration
2. If yes, configure timeout in SDK initialization
3. If no, consider switching to raw HTTP client

**Example (Stripe):**
```python
import stripe
stripe.max_network_retries = 3
stripe.default_timeout = 30  # Check if Stripe SDK supports this
```

---

## Testing Migration

### Unit Test Example

```python
import pytest
from unittest.mock import patch, MagicMock
from app.connectors.quickbooks import QuickBooksConnector
from app.errors import CredentialInvalidError, NetworkError

def test_create_vendor_success():
    """Test successful vendor creation"""
    connector = QuickBooksConnector()

    with patch('app.http_client.http_client.post') as mock_post:
        mock_post.return_value = {
            "Vendor": {"Id": "123", "DisplayName": "Acme Corp"}
        }

        result = connector.create_vendor(
            org_id="org_123",
            user_id="user_456",
            args={"vendor_name": "Acme Corp", "email": "vendor@acme.com"}
        )

        assert result["vendor_id"] == "qb:123"
        assert result["display_name"] == "Acme Corp"

def test_create_vendor_credential_invalid():
    """Test 401 error handling"""
    connector = QuickBooksConnector()

    with patch('app.http_client.http_client.post') as mock_post:
        mock_post.side_effect = CredentialInvalidError("quickbooks", "Token expired")

        with pytest.raises(CredentialInvalidError):
            connector.create_vendor(
                org_id="org_123",
                user_id="user_456",
                args={"vendor_name": "Acme Corp"}
            )

def test_create_vendor_timeout():
    """Test network timeout handling"""
    connector = QuickBooksConnector()

    with patch('app.http_client.http_client.post') as mock_post:
        mock_post.side_effect = NetworkError("quickbooks", details={"error": "timeout"})

        with pytest.raises(NetworkError):
            connector.create_vendor(
                org_id="org_123",
                user_id="user_456",
                args={"vendor_name": "Acme Corp"}
            )
```

---

## Rollback Plan

If migration causes issues:

1. **Identify problem connector** - Check logs for errors
2. **Revert specific connector** - Replace `http_client.*` with `requests.*`
3. **File bug report** - Document issue for HTTP client fix
4. **Continue with other connectors** - Don't block entire migration

**Rollback is easy** - just reverse the changes:
```python
# Revert to old code:
response = requests.post(url, headers=headers, json=payload, timeout=30)
result = response.json()
```

---

## Common Pitfalls

### ❌ Forgetting `service` Parameter

**Wrong:**
```python
result = http_client.post(url=url, headers=headers)
# Error: missing required 'service' parameter
```

**Correct:**
```python
result = http_client.post(url=url, service="quickbooks", headers=headers)
```

### ❌ Still Checking `response.status_code`

**Wrong (unnecessary):**
```python
result = http_client.post(url, service="quickbooks", headers=headers)
if result.status_code != 200:  # result is already parsed JSON, not Response object
    raise Exception(...)
```

**Correct:**
```python
result = http_client.post(url, service="quickbooks", headers=headers)
# result is parsed JSON dict - errors already raised if status code was bad
vendor_id = result["Vendor"]["Id"]
```

### ❌ Catching Generic `Exception`

**Wrong:**
```python
try:
    result = http_client.post(...)
except Exception as e:  # Too broad
    print("Error:", e)
```

**Correct:**
```python
from app.errors import NetworkError, CredentialInvalidError

try:
    result = http_client.post(...)
except CredentialInvalidError:
    # Handle auth error specifically
    raise
except NetworkError as e:
    # Handle network error specifically
    logger.error(f"Network error: {e}")
    raise
```

---

## Questions?

**Q: What if I need a custom timeout?**
A: Pass `timeout=(connect, read)` parameter:
```python
http_client.post(url, service="quickbooks", timeout=(10, 60))
```

**Q: What if I need the raw Response object?**
A: Set `parse_json=False`:
```python
response = http_client.get(url, service="quickbooks", parse_json=False)
raw_content = response.content
```

**Q: What if the SDK doesn't support timeouts?**
A: File an issue - we'll investigate switching to raw HTTP client or wrapping SDK calls.

**Q: What if migration breaks existing functionality?**
A: Revert the connector and file a bug report. Don't block the entire migration.

---

## Success Criteria

Migration is complete when:
- [ ] All 20+ connector files use `http_client` instead of `requests`
- [ ] All HTTP calls have automatic timeout protection
- [ ] All errors properly classified to StargateError taxonomy
- [ ] Integration tests pass for all connectors
- [ ] No production incidents related to HTTP timeouts

**Estimated effort:** 6-8 hours for all 20+ connectors
