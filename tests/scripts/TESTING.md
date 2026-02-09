# Stargate Lite - Testing Guide

## Quick Validation

Run the registry validation script to ensure all 180 capabilities are properly mapped:

```bash
python validate_registry.py
```

This will verify:
- ✅ Total capability count (180 endpoints)
- ✅ Per-service counts match expectations
- ✅ All required fields present
- ✅ All handlers are callable
- ✅ No duplicate keys
- ✅ Helper functions work correctly

## Running Test Suite

If you have pytest installed:

```bash
pytest tests/test_registry.py -v
```

## Manual Testing Per Platform

### 1. Setup Environment

Copy `.env.example` to `.env` and fill in credentials for platforms you want to test:

```bash
cp .env.example .env
# Edit .env with your API credentials
```

### 2. Test Individual Platforms

#### Financial/Accounting (53 endpoints)
- **QuickBooks** (11): Requires OAuth 2.0 sandbox
- **Stripe** (15): Use test mode secret key `sk_test_...`
- **Bill.com** (9): Requires OAuth 2.0 sandbox
- **NetSuite** (9): Requires OAuth 1.0a setup
- **Recurly** (9): Use test/sandbox API key

#### Banking/Payments (38 endpoints)
- **Plaid** (11): Use sandbox environment
- **Ramp** (5): Requires OAuth 2.0
- **Mercury** (6): API key from Mercury dashboard
- **Brex** (8): OAuth 2.0 sandbox
- **Chase** (8): OAuth 2.0 business account required

#### Productivity/BI (37 endpoints)
- **HubSpot** (4): OAuth 2.0 developer account
- **Notion** (11): Integration token
- **Asana** (12): Personal access token
- **Power BI** (10): Azure AD app + tenant ID

#### Communication (25 endpoints)
- **Gmail** (3): Google OAuth 2.0
- **Slack** (6): Bot token + OAuth
- **Bland.ai** (8): API key
- **Twilio** (8): Account SID + Auth Token

#### Trading/Brokerage (27 endpoints)
- **IBKR** (15): Local Gateway on localhost:5000
- **Schwab** (12): OAuth 2.0 approved app

### 3. Test Capability Execution

```python
import requests

# Example: Test vendor creation in QuickBooks
response = requests.post(
    "http://localhost:8001/api/v1/execute",
    headers={
        "X-API-Key": "your-api-key",
        "Content-Type": "application/json"
    },
    json={
        "capability_key": "vendor.create",
        "org_id": "test_org",
        "user_id": "test_user",
        "args": {
            "vendor_name": "Test Vendor",
            "email": "test@example.com"
        }
    }
)

print(response.json())
```

## Platform-Specific Testing Notes

### QuickBooks
- Use sandbox company for testing
- Realm ID required for all operations
- OAuth tokens expire after 1 hour

### Stripe
- Use test mode for all operations
- Test cards: `4242 4242 4242 4242`
- Customer IDs start with `cus_`

### Plaid
- Sandbox environment credentials:
  - Username: `user_good`
  - Password: `pass_good`
- Use sandbox institutions only

### Interactive Brokers
- Requires local Gateway running
- Must authenticate daily
- Gateway runs on https://localhost:5000
- Cannot use Lite accounts

### Charles Schwab
- Access token expires after 30 minutes
- Refresh token expires after 7 days
- Must use hashed account numbers

## Checklist for Production

Before deploying to production:

- [ ] All .env credentials configured
- [ ] `python validate_registry.py` passes
- [ ] OAuth flows tested for each OAuth service
- [ ] API key services respond correctly
- [ ] Multi-tenant credential isolation works
- [ ] Encryption key generated and secure
- [ ] Database migrations run
- [ ] Rate limiting configured
- [ ] Error handling tested
- [ ] Logging configured

## Troubleshooting

### Import Errors
```bash
pip install -r requirements.txt
```

### OAuth Token Expired
Check credential store and refresh tokens automatically.

### API Rate Limits
Each service has different rate limits:
- Stripe: 100 req/sec
- QuickBooks: 500 req/min
- Plaid: Varies by plan
- Power BI: 200 calls/hour

### Gateway Not Running (IBKR)
```bash
# Start IBKR Gateway manually
java -jar clientportal.gw.jar
```

## Test Coverage

Current test coverage:
- Registry validation: ✅ 100%
- Connector imports: ✅ All 20
- Capability mapping: ✅ 180/180
- Integration tests: ⚠️ Requires credentials

## Next Steps

1. Run `python validate_registry.py` to verify setup
2. Configure credentials in `.env`
3. Start server: `python -m uvicorn app.main:app --reload`
4. Test individual endpoints with sandbox credentials
5. Deploy to production with real credentials
