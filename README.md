# Stargate Lite 🚀

**The "Hands" of the Aleq MIND** - A lightweight execution layer for multi-tenant business automation.

## What is Stargate Lite?

Stargate Lite is the **execution layer** that sits between the Aleq MIND (the "Brain") and real-world business systems. While the Brain decides *what* to do, Stargate executes the *how* by connecting to:

- **QuickBooks Online** - Accounting, vendor management, journal entries, expense tracking
- **Stripe** - Payments, payouts, balance, transfers, Connect
- **Bill.com** - AP automation, vendor payments, bill approvals
- **NetSuite** - ERP, journal entries, vendor bills, SuiteQL
- **HubSpot** - CRM, contacts, deals, companies
- **Gmail** - Email automation
- **Slack** - Messaging, channels, notifications
- **Hyperbrowser** - Browser automation using Anthropic's Computer Use API

## Architecture

```
Aleq MIND (Brain)                    Stargate Lite (Hands)
     │                                      │
     │  POST /api/v1/execute                │
     │  {                                   │
     │    "capability_key": "vendor.create",│
     │    "org_id": "org_123",              │
     │    "user_id": "user_456",            │
     │    "args": {...}                     │
     │  }                                   │
     └──────────────────────────────────────>
                                             │
                                    ┌────────┴─────────┐
                                    │  Capability      │
                                    │  Registry        │
                                    │  Maps to Tool    │
                                    └────────┬─────────┘
                                             │
                        ┌────────────────────┴────────────────────┐
                        │                                          │
                  QuickBooks                                  Stripe
                  Create Vendor                          Create Customer
                        │                                          │
                   OAuth Token                                 API Key
                   from Database                           from Config
```

## Key Features

✅ **Capability Abstraction** - Brain sends `vendor.create`, not `quickbooks.create_vendor`
✅ **Multi-Tenant** - Isolated credentials per org/user
✅ **Secure Credential Storage** - Encrypted OAuth tokens with Fernet encryption
✅ **Token Refresh** - Automatic OAuth token management
✅ **Rich Responses** - Returns structured data for Brain to process
✅ **Comprehensive Coverage** - **288 capabilities** across 8 platforms
✅ **Production Ready** - Live OAuth flow, real data, tested with 4,288+ QuickBooks transactions

## Quick Start

### 1. Clone & Setup

```bash
# Clone the repo
cd stargate-lite

# Run setup script
chmod +x setup.sh
./setup.sh

# This will:
# - Create virtual environment
# - Install dependencies
# - Generate encryption key
# - Initialize database
```

### 2. Configure Environment

Edit `.env` file with your API credentials:

```bash
# QuickBooks
QUICKBOOKS_CLIENT_ID=your_client_id
QUICKBOOKS_CLIENT_SECRET=your_client_secret

# Stripe
STRIPE_SECRET_KEY=sk_test_...

# HubSpot
HUBSPOT_CLIENT_ID=your_client_id
HUBSPOT_CLIENT_SECRET=your_client_secret

# Gmail (Google)
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# Slack
SLACK_CLIENT_ID=your_client_id
SLACK_CLIENT_SECRET=your_client_secret

# Internal API Security
API_SECRET_KEY=your-super-secret-key-change-this
ENCRYPTION_KEY=<generated_by_setup_script>
```

### 3. Run

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server runs at: `http://localhost:8000`

### 4. Setup OAuth (Production)

For production QuickBooks OAuth, you'll need ngrok for HTTPS:

```bash
# Install ngrok
brew install ngrok  # or download from ngrok.com

# Start ngrok tunnel
ngrok http 8000 --domain=your-static-domain.ngrok-free.app

# Update .env with ngrok URL
QUICKBOOKS_REDIRECT_URI=https://your-static-domain.ngrok-free.app/oauth/quickbooks/callback
QUICKBOOKS_ENVIRONMENT=production
```

**Initiate OAuth:**
```
https://your-static-domain.ngrok-free.app/oauth/quickbooks/authorize?org_id=test_org&user_id=te
```

## API Usage

### Execute a Capability

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-super-secret-key" \
  -d '{
    "capability_key": "vendor.create",
    "org_id": "org_12345",
    "user_id": "user_67890",
    "args": {
      "vendor_name": "Acme Inc.",
      "email": "[email protected]"
    }
  }'
```

⚠️ **Important:** Use `"args"` not `"parameters"` for capability arguments!

**Response:**
```json
{
  "status": "success",
  "capability_key": "vendor.create",
  "tool_used": "quickbooks.create_vendor",
  "outputs": {
    "vendor_id": "qb:123-xyz",
    "display_name": "Acme Inc.",
    "email": "[email protected]",
    "status": "active",
    "created_at": "2025-10-18T12:00:00Z"
  },
  "logs": [
    "Resolved capability 'vendor.create' to tool 'quickbooks.create_vendor'",
    "Successfully executed quickbooks.create_vendor"
  ],
  "timestamp": "2025-10-18T12:00:00.123456"
}
```

### Query QuickBooks Data

```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-super-secret-key" \
  -d '{
    "capability_key": "qb.query",
    "org_id": "test_org",
    "user_id": "te",
    "args": {
      "query": "SELECT * FROM Purchase WHERE TxnDate >= '\''2024-01-01'\'' MAXRESULTS 10"
    }
  }'
```

### List Available Capabilities

```bash
curl -X GET http://localhost:8000/api/v1/capabilities \
  -H "X-API-Key: your-super-secret-key"
```

## Available Capabilities (288 Total)

### QuickBooks (60+ capabilities)
- `qb.query` - Execute QuickBooks SQL-like queries (Purchase, Bill, Vendor, etc.)
- `vendor.create` - Create vendor
- `vendor.get` - Get vendor details
- `vendor.list` - List all vendors
- `bill.create` - Create a bill
- `journal.create` - Create journal entry
- And 50+ more accounting capabilities...

### Stripe (40+ capabilities)
- `payment.create` - Create Stripe payment intent
- `payment.refund` - Refund a payment
- `customer.create` - Create Stripe customer
- `invoice.create` - Create Stripe invoice
- `subscription.create` - Create subscription
- `payout.list` - List payouts
- `balance.get` - Get account balance
- And 30+ more payment capabilities...

### Bill.com (30+ capabilities)
- `billcom.vendor.create` - Create vendor in Bill.com
- `billcom.bill.create` - Create bill
- `billcom.payment.send` - Send vendor payment
- And 25+ more AP automation capabilities...

### NetSuite (50+ capabilities)
- `netsuite.query` - Execute SuiteQL queries
- `netsuite.journal.create` - Create journal entry
- `netsuite.vendor.create` - Create vendor
- And 45+ more ERP capabilities...

### HubSpot (40+ capabilities)
- `crm.contact.create` - Create HubSpot contact
- `crm.contact.get` - Get contact details
- `crm.deal.create` - Create deal
- `crm.company.create` - Create company
- And 35+ more CRM capabilities...

### Gmail (20+ capabilities)
- `email.send` - Send Gmail email
- `email.read` - Read Gmail messages
- `email.draft` - Create draft email
- And 15+ more email capabilities...

### Slack (30+ capabilities)
- `message.send` - Send Slack message to channel
- `message.direct` - Send Slack DM
- `file.upload` - Upload file to Slack
- `channel.create` - Create Slack channel
- `channel.invite` - Invite users to channel
- `channel.history` - Get channel message history
- And 20+ more messaging capabilities...

### Hyperbrowser (9 capabilities)
- `browser.navigate` - Navigate to URL
- `browser.click` - Click element
- `browser.fill_form` - Fill form fields
- `browser.extract_data` - Extract data from page
- `browser.extract_table` - Extract table data
- `browser.login_with_credentials` - Auto-login to portals
- `browser.collect_bank_balances` - Multi-bank balance collection
- And 2+ more browser automation capabilities...

## Credential Management

Credentials are stored encrypted in the database. To store credentials:

```python
from app.database import CredentialManager

CredentialManager.store_credential(
    org_id="org_12345",
    user_id="user_67890",
    service="quickbooks",
    access_token="eyJ...",
    refresh_token="1//...",
    token_expiry=datetime(2025, 10, 19),
    realm_id="9130123456789"  # QuickBooks specific
)
```

## Pattern Detector Integration Example

For MARS Pattern Detector integration, use the capability-based API:

```python
import requests

class PatternDetectorStargateClient:
    def __init__(self, stargate_base_url: str, api_key: str):
        self.stargate_base_url = stargate_base_url
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}

    def fetch_expenses(self, org_id: str, user_id: str, days: int = 180):
        """Fetch expenses from QuickBooks via Stargate"""
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

        # QuickBooks uses "Purchase" entity for expenses
        query = f"SELECT * FROM Purchase WHERE TxnDate >= '{start_date}'"

        response = requests.post(
            f"{self.stargate_base_url}/api/v1/execute",
            json={
                "capability_key": "qb.query",
                "org_id": org_id,
                "user_id": user_id,
                "args": {"query": query}  # Use "args" not "parameters"!
            },
            headers=self.headers
        )

        result = response.json()
        if result.get("status") == "success":
            return result.get("outputs", {}).get("results", {}).get("Purchase", [])
        else:
            raise Exception(f"Stargate error: {result}")

# Usage
client = PatternDetectorStargateClient(
    stargate_base_url="http://localhost:8000",
    api_key="your-super-secret-internal-api-key-change-this"
)

expenses = client.fetch_expenses(
    org_id="test_org",
    user_id="te",
    days=180
)

print(f"Found {len(expenses)} expenses")
# Output: Found 4288 expenses (2019-2024 data available)
```

**Production Data Available:**
- 4,288 Purchase records from 2019-2024
- Categories: Hangar Rent, Crew Salaries, Navigation Services, Marketing, Insurance, etc.
- Perfect for testing escalating costs, recurring patterns, seasonal analysis

## OAuth Setup Guides

### QuickBooks (Production)
1. Go to https://developer.intuit.com
2. Create a production app
3. Set up ngrok: `ngrok http 8000 --domain=your-static-domain.ngrok-free.app`
4. Add OAuth redirect URI: `https://your-static-domain.ngrok-free.app/oauth/quickbooks/callback`
5. Add scopes: `com.intuit.quickbooks.accounting`
6. Copy Client ID & Secret to `.env`
7. Set `QUICKBOOKS_ENVIRONMENT=production`
8. Initiate OAuth: Visit `https://your-static-domain.ngrok-free.app/oauth/quickbooks/authorize?org_id=test_org&user_id=te`

### HubSpot
1. Go to https://developers.hubspot.com
2. Create app
3. Add redirect URI: `http://localhost:8000/oauth/hubspot/callback`
4. Add scopes: `crm.objects.contacts.read`, `crm.objects.contacts.write`, etc.
5. Copy Client ID & Secret to `.env`

### Gmail (Google)
1. Go to https://console.cloud.google.com
2. Create project and enable Gmail API
3. Create OAuth 2.0 credentials
4. Add redirect URI: `http://localhost:8000/oauth/google/callback`
5. Add scopes: `https://www.googleapis.com/auth/gmail.send`
6. Copy Client ID & Secret to `.env`

### Slack
1. Go to https://api.slack.com/apps
2. Create app
3. Add redirect URI: `http://localhost:8000/oauth/slack/callback`
4. Add scopes: `chat:write`, `channels:read`, `files:write`
5. Copy Client ID & Secret to `.env`

## Development

### Project Structure
```
stargate-lite/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── database.py          # Encrypted credential storage
│   ├── registry.py          # Capability→Tool mapping (288 capabilities)
│   └── connectors/
│       ├── quickbooks.py    # QuickBooks connector (60+ capabilities)
│       ├── stripe_connector.py  # Stripe connector (40+ capabilities)
│       ├── billcom.py       # Bill.com connector (30+ capabilities)
│       ├── netsuite.py      # NetSuite connector (50+ capabilities)
│       ├── hubspot.py       # HubSpot connector (40+ capabilities)
│       ├── gmail.py         # Gmail connector (20+ capabilities)
│       ├── slack.py         # Slack connector (30+ capabilities)
│       └── hyperbrowser_v2.py  # Browser automation (9 capabilities)
├── requirements.txt
├── setup.sh
├── .env.example
└── README.md
```

### Adding New Capabilities

1. **Create Connector** (if needed):
```python
# app/connectors/newservice.py
class NewServiceConnector:
    def do_thing(self, org_id, user_id, args):
        # Implementation
        return {"result": "data"}
```

2. **Register Capability**:
```python
# app/registry.py
"capability.key": {
    "handler": new_service_connector.do_thing,
    "tool_name": "newservice.do_thing",
    "description": "Does a thing",
    "requires_oauth": True,
    "service": "newservice"
}
```

3. **Done!** Brain can now use `capability.key`

## Testing

```bash
# Health check
curl http://localhost:8000/health

# List capabilities (288 total)
curl http://localhost:8000/api/v1/capabilities \
  -H "X-API-Key: your-key"

# Test with real production data (after OAuth)
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "capability_key": "qb.query",
    "org_id": "test_org",
    "user_id": "te",
    "args": {
      "query": "SELECT * FROM Purchase WHERE TxnDate >= '\''2024-01-01'\'' MAXRESULTS 5"
    }
  }'
# Returns real expense data from production QuickBooks (4,288 transactions available)
```

## Production Deployment

1. **Use PostgreSQL** instead of SQLite
2. **Set strong API_SECRET_KEY** and **ENCRYPTION_KEY**
3. **Configure CORS** properly
4. **Use HTTPS** for OAuth callbacks
5. **Implement OAuth flows** in callback endpoints
6. **Add logging** and monitoring
7. **Rate limiting** per org/user
8. **Backup credential database** regularly

## Troubleshooting

**Q: Getting "No credentials found" error?**
A: Complete OAuth flow by visiting the authorize endpoint: `https://your-domain.ngrok-free.app/oauth/quickbooks/authorize?org_id=test_org&user_id=te`

**Q: Token refresh failing?**
A: Check that refresh token is valid and hasn't been revoked in the service's dashboard. QuickBooks tokens expire after 100 days.

**Q: Getting "redirect_uri validation error"?**
A: Ensure your `.env` redirect URI exactly matches what's configured in Intuit developer portal (no trailing slash, correct https://).

**Q: QuickBooks receiving "None" for query?**
A: Use `"args"` not `"parameters"` in your API request. Common mistake!

**Q: Stripe not working?**
A: Stripe uses API keys, not OAuth. Just set `STRIPE_SECRET_KEY` in `.env`

**Q: Need to test with real data?**
A: Production QuickBooks has 4,288 Purchase records from 2019-2024 available after OAuth setup.

## License

MIT

## Support

For issues, questions, or contributions, please open an issue or PR.

---

Built with ❤️ for the Aleq MIND ecosystem
