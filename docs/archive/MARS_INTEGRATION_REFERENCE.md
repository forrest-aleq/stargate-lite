# Stargate API Reference for MARS E2E Testing
## Quick Reference - Live Endpoints Ready

---

## 🚀 LIVE ENDPOINTS

**Base URL:** `http://localhost:8001`
**API Key Header:** `X-API-Key: your-super-secret-internal-api-key-change-this`

---

## 1. Execute Capability

**POST `/api/v1/execute`**

**Request:**
```json
{
  "capability_key": "netsuite.vendor.create",
  "org_id": "test_org",
  "user_id": "test_user",
  "args": {
    "companyName": "Lighthouse Marine",
    "email": "[email protected]"
  },
  "use_delegation": false
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "capability_key": "netsuite.vendor.create",
  "tool_used": "netsuite.create_vendor",
  "outputs": {
    "vendor_id": "ns:12345",
    "status": "active"
  },
  "logs": ["Successfully created vendor in NetSuite"],
  "credential_type": "customer",
  "timestamp": "2025-10-19T00:00:00"
}
```

**Error Response (200 with error details):**
```json
{
  "status": "error",
  "error_code": "CREDENTIAL_MISSING",
  "error_message": "No customer credentials found for NetSuite",
  "retry_strategy": "human_intervention",
  "details": {
    "service": "netsuite",
    "org_id": "test_org",
    "user_id": "test_user"
  },
  "capability_key": "netsuite.vendor.create",
  "tool_used": "netsuite.create_vendor",
  "credential_type": "customer",
  "logs": ["Credential lookup failed"],
  "timestamp": "2025-10-19T00:00:00"
}
```

---

## 2. Check Credential Status (NEW - LIVE)

**POST `/api/v1/credentials/status`**

**Request:**
```json
{
  "org_id": "test_org",
  "user_id": "test_user",
  "capability_key": "netsuite.vendor.create",
  "use_delegation": false
}
```

**Response - Credential Available:**
```json
{
  "credential_available": true,
  "credential_type": "customer",
  "access_pattern": null,
  "token_expiry": "2025-10-20T12:00:00",
  "requires_setup": false,
  "delegation_supported": false,
  "delegation_instructions": null
}
```

**Response - Credential Missing:**
```json
{
  "credential_available": false,
  "credential_type": "customer",
  "requires_setup": true,
  "delegation_supported": false,
  "delegation_instructions": null,
  "message": "Missing customer credential for netsuite"
}
```

**Response - No OAuth Required:**
```json
{
  "credential_available": true,
  "credential_type": null,
  "requires_setup": false,
  "message": "No credentials required for this capability"
}
```

---

## 3. Health Check

**GET `/health`**

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-19T00:00:00",
  "services": {
    "quickbooks": "ok",
    "stripe": "ok",
    "netsuite": "ok"
  }
}
```

---

## 4. Connector Health (Detailed)

**GET `/health/connectors`**

**Response:**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "total_connectors": 22,
  "total_connections": 5,
  "connectors": [
    {
      "service": "netsuite",
      "credential_status": "connected",
      "token_expiry": "2025-10-20T12:00:00",
      "last_updated": "2025-10-19T10:00:00",
      "requires_oauth": true,
      "connection_count": 2
    },
    {
      "service": "google",
      "credential_status": "missing",
      "token_expiry": null,
      "last_updated": null,
      "requires_oauth": true,
      "connection_count": 0
    }
  ],
  "timestamp": "2025-10-19T00:00:00"
}
```

---

## 5. List Capabilities

**GET `/api/v1/capabilities`**

**Response:**
```json
{
  "capabilities": {
    "vendor.create": {
      "tool_name": "quickbooks.create_vendor",
      "description": "Create a vendor in QuickBooks",
      "service": "quickbooks",
      "credential_type": "customer",
      "supports_delegation": false,
      "requires_oauth": true
    },
    "email.send": {
      "tool_name": "gmail.send_email",
      "description": "Send an email via Gmail",
      "service": "google",
      "credential_type": "agent",
      "supports_delegation": true,
      "requires_oauth": true
    }
  },
  "count": 294
}
```

---

## 📊 ERROR TAXONOMY

All Stargate errors include these fields:

| Field | Type | Description |
|-------|------|-------------|
| `error_code` | string | Standardized error code |
| `error_message` | string | Human-readable message |
| `retry_strategy` | string | "human_intervention", "backoff", or "none" |
| `details` | object | Additional context |
| `credential_type` | string | "agent", "customer", or null |

### Error Codes

| Code | Retry Strategy | Use Case |
|------|---------------|----------|
| `CREDENTIAL_MISSING` | `human_intervention` | User needs to connect service |
| `CREDENTIAL_INVALID` | `human_intervention` | OAuth token expired/revoked |
| `RATE_LIMIT` | `backoff` | API rate limit hit |
| `API_DOWN` | `backoff` | Service temporarily unavailable |
| `MISSING_PERMISSION` | `human_intervention` | Need additional OAuth scopes |
| `VALIDATION_ERROR` | `none` | Invalid input from MARS |
| `NOT_FOUND` | `none` | Resource doesn't exist |
| `INTERNAL_STARGATE_ERROR` | `backoff` | Stargate bug/config issue |
| `EXTERNAL_API_ERROR` | `backoff` | Generic external API error |

---

## 🧪 TESTING SCENARIOS FOR MARS

### Scenario 1: Successful Vendor Creation (Happy Path)

**Prerequisites:**
- Valid NetSuite customer credential stored for test_org/test_user

**Steps:**
1. POST `/api/v1/credentials/status` with `capability_key: "netsuite.vendor.create"`
   - Expect: `credential_available: true`
2. POST `/api/v1/execute` with `capability_key: "netsuite.vendor.create"`
   - Expect: `status: "success"`, `credential_type: "customer"`

---

### Scenario 2: Missing Customer Credential

**Prerequisites:**
- No NetSuite credential stored

**Steps:**
1. POST `/api/v1/credentials/status`
   - Expect: `credential_available: false`, `requires_setup: true`
2. POST `/api/v1/execute`
   - Expect: `error_code: "CREDENTIAL_MISSING"`, `retry_strategy: "human_intervention"`
   - Expect: `credential_type: "customer"`
3. Subgraph should pause with checkpoint and prompt user to connect NetSuite

---

### Scenario 3: Agent Credential (Email)

**Prerequisites:**
- Aleq system Gmail credential stored at ALEQ_SYSTEM/ALEQ_AGENT

**Steps:**
1. POST `/api/v1/credentials/status` with `capability_key: "email.send"`
   - Expect: `credential_available: true`, `credential_type: "agent"`
2. POST `/api/v1/execute` with `capability_key: "email.send"`
   - Expect: `status: "success"`, `credential_type: "agent"`

---

### Scenario 4: Validation Error

**Prerequisites:**
- Valid credential

**Steps:**
1. POST `/api/v1/execute` with invalid args (e.g., missing required field)
   - Expect: `error_code: "VALIDATION_ERROR"`, `retry_strategy: "none"`
2. Subgraph should not retry, should report error to MIND

---

### Scenario 5: OCR (No Credentials)

**Prerequisites:**
- None (OCR doesn't need credentials)

**Steps:**
1. POST `/api/v1/credentials/status` with `capability_key: "ocr.text.extract"`
   - Expect: `credential_available: true`, `credential_type: null`
2. POST `/api/v1/execute` with `capability_key: "ocr.text.extract"`
   - Expect: `status: "success"`, `credential_type: null`

---

## 🔧 DEBUGGING TIPS

### Check Stargate Logs
```bash
# Start server with debug logging
python -m uvicorn app.main:app --reload --log-level debug
```

### Verify Credentials Exist
```bash
curl -X GET "http://localhost:8001/api/v1/credentials/metadata?org_id=test_org&user_id=test_user&service=netsuite&credential_type=customer" \
  -H "X-API-Key: your-key"
```

### Check Connector Health
```bash
curl http://localhost:8001/health/connectors \
  -H "X-API-Key: your-key"
```

---

## 📞 COMMON ISSUES & RESOLUTIONS

### Issue: "No module named 'sqlalchemy'"
**Resolution:** Install dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: 404 on `/api/v1/credentials/status`
**Resolution:** Ensure you're running the latest code with dual credential implementation

### Issue: credential_type not in response
**Resolution:** Check that you're using updated models.py and main.py

### Issue: CREDENTIAL_MISSING but credential exists
**Resolution:**
- Check credential_type matches capability (customer vs agent)
- Verify composite key: {org_id}:{user_id}:{service}:{credential_type}
- Use `/credentials/metadata` endpoint to inspect stored credential

---

## 🎯 MARS INTEGRATION CHECKLIST

- [ ] Remove 404 fallback logic in `check_credentials` node
- [ ] Update error handling to use `credential_type` field
- [ ] Test successful path with valid customer credential
- [ ] Test CREDENTIAL_MISSING error path
- [ ] Test CREDENTIAL_INVALID error path (expired token)
- [ ] Test VALIDATION_ERROR path (bad input)
- [ ] Test agent credential path (email.send)
- [ ] Test no-credential path (ocr.text.extract)
- [ ] Test human-in-the-loop checkpoint/resume
- [ ] Verify retry strategies are honored
- [ ] Test full MIND -> Subgraph -> Stargate -> Subgraph -> MIND flow

---

## 💡 STARGATE TEAM COMMITMENT

**Response Time SLA for MARS Testing:**
- Critical bugs blocking testing: < 30 minutes
- API clarification questions: < 15 minutes
- Non-blocking issues: < 2 hours

**Contact:** This conversation thread

**Status:** 🟢 ONLINE AND MONITORING

**Last Updated:** 2025-10-19T00:44:00
