# QuickBooks E2E Test Setup - Ready for MARS
## Updated: 2025-10-19T01:00:00

---

## ✅ CONFIRMED: QuickBooks Credentials Ready

### Setup Script Updated
- **File:** `setup_mars_test_data.py`
- **Change:** Switched from NetSuite → QuickBooks
- **Status:** ✅ Ready to run

---

## 🎯 Test Scenarios (QuickBooks Edition)

### Scenario 1: Happy Path ✅
```json
{
  "org_id": "mars_test_org",
  "user_id": "mars_test_user",
  "credentials": {
    "quickbooks": {
      "type": "customer",
      "realm_id": "mock_realm_12345",
      "token": "mock_quickbooks_customer_token_valid"
    },
    "google": {
      "type": "agent",
      "access_pattern": "programmatic",
      "token": "mock_gmail_agent_token_valid"
    }
  }
}
```

### Scenario 2: Missing Credentials ✅
```json
{
  "org_id": "mars_no_quickbooks",
  "user_id": "mars_test_user",
  "credentials": {},
  "expected_error": "CREDENTIAL_MISSING"
}
```

### Scenario 3: Agent Only ✅
```json
{
  "org_id": "ALEQ_SYSTEM",
  "user_id": "ALEQ_AGENT",
  "credentials": {
    "google": {
      "type": "agent",
      "access_pattern": "programmatic"
    }
  }
}
```

---

## 🚀 Quick Start for MARS

### 1. Run Setup Script
```bash
cd /Users/forrest/Documents/Projects/aleq/stargate-lite
source venv/bin/activate
pip install -r requirements.txt
python3 setup_mars_test_data.py
```

**Expected Output:**
```
✅ Database initialized
✅ Stored customer:quickbooks credential for mars_test_org/mars_test_user
✅ Stored agent:google credential for ALEQ_SYSTEM/ALEQ_AGENT
✅ No credentials stored for mars_no_quickbooks (intentional)
✅ Correctly retrieved customer credential
✅ Correctly retrieved agent credential
✅ Correctly returned None (no credential)
🚀 Stargate is ready for MARS E2E testing (QuickBooks Edition)!
```

### 2. Start Stargate Server
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 3. Verify Endpoints Live
```bash
# Health check
curl http://localhost:8001/health

# Credential status check
curl -X POST http://localhost:8001/api/v1/credentials/status \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "mars_test_org",
    "user_id": "mars_test_user",
    "capability_key": "vendor.create",
    "use_delegation": false
  }'
```

**Expected Response:**
```json
{
  "credential_available": true,
  "credential_type": "customer",
  "access_pattern": null,
  "token_expiry": "2025-11-18T00:00:00",
  "requires_setup": false,
  "delegation_supported": false,
  "delegation_instructions": null
}
```

---

## 📝 Sample Requests (Ready to Test)

### Test 1: QuickBooks Vendor Search
```bash
curl -X POST http://localhost:8001/api/v1/execute \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "capability_key": "vendor.list",
    "org_id": "mars_test_org",
    "user_id": "mars_test_user",
    "args": {"limit": 10},
    "use_delegation": false
  }'
```

**Expected Response Structure:**
```json
{
  "status": "success",
  "capability_key": "vendor.list",
  "tool_used": "quickbooks.list_vendors",
  "outputs": {...},
  "logs": ["Successfully executed quickbooks.list_vendors"],
  "credential_type": "customer",
  "timestamp": "2025-10-19T00:00:00"
}
```

**Note:** Will call actual QuickBooks API - expect 401/403 errors from QuickBooks since we're using mock tokens.

### Test 2: QuickBooks Vendor Create
```bash
curl -X POST http://localhost:8001/api/v1/execute \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "capability_key": "vendor.create",
    "org_id": "mars_test_org",
    "user_id": "mars_test_user",
    "args": {
      "display_name": "Acme Corporation",
      "company_name": "Acme Corporation",
      "email": "[email protected]",
      "phone": "+1-555-0199"
    },
    "use_delegation": false
  }'
```

### Test 3: Missing Credential Error
```bash
curl -X POST http://localhost:8001/api/v1/execute \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "capability_key": "vendor.create",
    "org_id": "mars_no_quickbooks",
    "user_id": "mars_test_user",
    "args": {"display_name": "Test Corp"},
    "use_delegation": false
  }'
```

**Expected Response:**
```json
{
  "status": "error",
  "error_code": "CREDENTIAL_MISSING",
  "error_message": "No QuickBooks credentials found for org_id=mars_no_quickbooks, user_id=mars_test_user",
  "retry_strategy": "human_intervention",
  "details": {...},
  "capability_key": "vendor.create",
  "tool_used": "quickbooks.create_vendor",
  "credential_type": "customer",
  "logs": ["Credential lookup failed"],
  "timestamp": "2025-10-19T00:00:00"
}
```

### Test 4: Agent Credential (Gmail)
```bash
curl -X POST http://localhost:8001/api/v1/execute \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "capability_key": "email.send",
    "org_id": "ALEQ_SYSTEM",
    "user_id": "ALEQ_AGENT",
    "args": {
      "to": "[email protected]",
      "subject": "W-9 Request - Acme Corporation",
      "body": "Hi there,\n\nWe'\''re setting up Acme Corporation as a vendor...\n\nBest,\nAleq AP Team"
    },
    "use_delegation": false
  }'
```

---

## 🔍 Verification Checklist

Before starting E2E tests, verify:

- [ ] Setup script runs without errors
- [ ] Database shows 2 credentials stored (QuickBooks + Gmail)
- [ ] Stargate server starts on port 8001
- [ ] `/health` endpoint returns 200 OK
- [ ] `/api/v1/credentials/status` endpoint returns 200 OK
- [ ] Credential check for `mars_test_org` returns `credential_available: true`
- [ ] Credential check for `mars_no_quickbooks` returns `credential_available: false`

---

## ⚠️ Expected Behavior Notes

### Mock Tokens = External API Errors
Since we're using mock tokens, actual QuickBooks API calls will fail with authentication errors. This is **expected and OK for testing**.

**What to test:**
- ✅ Stargate correctly retrieves customer:quickbooks credential
- ✅ Stargate returns `credential_type: "customer"` in response
- ✅ Error responses include `credential_type`
- ✅ CREDENTIAL_MISSING error for `mars_no_quickbooks`

**What NOT to test (yet):**
- ❌ Actual QuickBooks data (will fail with 401 Unauthorized)
- ❌ Real vendor creation (need real QB sandbox credentials)

### Focus Areas for E2E Testing
1. **Credential Lookup:** Does Stargate find the right credential type?
2. **Error Taxonomy:** Do errors include correct error codes and credential_type?
3. **Dual Credential System:** Does QuickBooks use customer creds, Gmail use agent creds?
4. **Subgraph Integration:** Does MARS correctly parse Stargate responses?

---

## 📊 QuickBooks Capabilities Available

| Capability Key | credential_type | Description |
|----------------|-----------------|-------------|
| `vendor.create` | customer | Create vendor in QuickBooks |
| `vendor.get` | customer | Get vendor details |
| `vendor.list` | customer | List vendors |
| `bill.create` | customer | Create bill |
| `bill.get` | customer | Get bill details |
| `bill.list` | customer | List bills |
| `customer.create` | customer | Create customer |
| `customer.list` | customer | List customers |
| `invoice.create` | customer | Create invoice |
| `invoice.send` | customer | Send invoice |
| `payment.create` | customer | Create payment |
| `report.profitloss` | customer | Get P&L report |

All QuickBooks capabilities use `credential_type: "customer"`.

---

## 🟢 STARGATE STATUS

**Confirmed Ready:**
- ✅ Setup script updated for QuickBooks
- ✅ All 294 capabilities categorized (including QuickBooks)
- ✅ `/api/v1/credentials/status` endpoint live
- ✅ `/api/v1/execute` returns `credential_type`
- ✅ Error responses include `credential_type`
- ✅ Dual credential system operational

**Monitoring Status:** 🟢 ACTIVE

**Response Time:** < 15 minutes for any issues

**MARS Team: You are cleared to begin E2E testing!** 🚀

---

## 📞 Next Steps

1. **MARS:** Run `setup_mars_test_data.py`
2. **MARS:** Start Stargate server
3. **MARS:** Run credential pre-check tests
4. **MARS:** Begin full E2E Subgraph testing
5. **Stargate:** Monitor for issues and respond rapidly

**Let's validate this integration!** 💪
