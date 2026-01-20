# Stargate Lite API Documentation

Base URL: `http://localhost:8001`

All endpoints (except health) require the `X-API-Key` header.

## Authentication

```
X-API-Key: your-super-secret-internal-api-key
```

---

## Endpoints

### GET /
Health check with service status

**Response:**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "timestamp": "2025-10-18T12:00:00.123456",
  "services": {
    "quickbooks": "configured",
    "stripe": "configured",
    "hubspot": "configured",
    "google": "configured",
    "slack": "configured"
  }
}
```

---

### GET /health
Simple health check

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-18T12:00:00.123456",
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

### GET /api/v1/capabilities
List all available capabilities

**Headers:**
```
X-API-Key: your-key
```

**Response:**
```json
{
  "capabilities": {
    "vendor.create": {
      "tool_name": "quickbooks.create_vendor",
      "description": "Create a vendor in QuickBooks",
      "service": "quickbooks",
      "requires_oauth": true
    },
    ...
  },
  "count": 25
}
```

---

### POST /api/v1/execute
Execute a capability

**Headers:**
```
X-API-Key: your-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "capability_key": "vendor.create",
  "org_id": "org_12345",
  "user_id": "user_67890",
  "args": {
    "vendor_name": "Acme Inc.",
    "email": "[email protected]",
    "phone": "555-1234",
    "website": "https://acme.com"
  }
}
```

**Success Response:**
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
    "Executing quickbooks.create_vendor for org_id=org_12345, user_id=user_67890",
    "Successfully executed quickbooks.create_vendor"
  ],
  "timestamp": "2025-10-18T12:00:00.123456"
}
```

**Error Response:**
```json
{
  "status": "error",
  "capability_key": "vendor.create",
  "tool_used": "quickbooks.create_vendor",
  "outputs": {},
  "logs": [
    "Resolved capability 'vendor.create' to tool 'quickbooks.create_vendor'",
    "Error: No QuickBooks credentials found for org_id=org_12345, user_id=user_67890"
  ],
  "error": "No QuickBooks credentials found for org_id=org_12345, user_id=user_67890",
  "timestamp": "2025-10-18T12:00:00.123456"
}
```

---

## Capability Reference

### Accounting & Finance

#### vendor.create
Create a vendor in QuickBooks

**Args:**
- `vendor_name` (string, required)
- `email` (string, required)
- `phone` (string, optional)
- `website` (string, optional)
- `billing_address` (object, optional)

**Returns:**
- `vendor_id` (string)
- `display_name` (string)
- `email` (string)
- `status` (string)
- `created_at` (datetime)

---

#### vendor.get
Get vendor details from QuickBooks

**Args:**
- `vendor_id` (string, required)

**Returns:**
- `vendor_id` (string)
- `display_name` (string)
- `email` (string)
- `phone` (string)
- `status` (string)

---

#### bill.create
Create a bill in QuickBooks

**Args:**
- `vendor_id` (string, required)
- `line_items` (array, required)
- `due_date` (string, required)
- `txn_date` (string, optional)

**Returns:**
- `bill_id` (string)
- `doc_number` (string)
- `total_amount` (number)
- `due_date` (string)
- `status` (string)

---

### Payments

#### payment.create
Create a payment intent in Stripe

**Args:**
- `amount` (integer, required) - Amount in cents
- `currency` (string, optional) - Default: "usd"
- `customer_id` (string, optional)
- `description` (string, optional)
- `metadata` (object, optional)

**Returns:**
- `payment_intent_id` (string)
- `client_secret` (string)
- `amount` (integer)
- `currency` (string)
- `status` (string)

---

#### customer.create
Create a customer in Stripe

**Args:**
- `email` (string, required)
- `name` (string, optional)
- `phone` (string, optional)
- `metadata` (object, optional)

**Returns:**
- `customer_id` (string)
- `email` (string)
- `name` (string)
- `created_at` (integer)

---

### CRM

#### crm.contact.create
Create a contact in HubSpot

**Args:**
- `email` (string, required)
- `first_name` (string, optional)
- `last_name` (string, optional)
- `phone` (string, optional)
- `company` (string, optional)

**Returns:**
- `contact_id` (string)
- `email` (string)
- `first_name` (string)
- `last_name` (string)
- `created_at` (datetime)

---

#### crm.deal.create
Create a deal in HubSpot

**Args:**
- `deal_name` (string, required)
- `amount` (number, optional)
- `deal_stage` (string, optional)
- `pipeline` (string, optional)

**Returns:**
- `deal_id` (string)
- `deal_name` (string)
- `amount` (number)
- `stage` (string)
- `created_at` (datetime)

---

### Email

#### email.send
Send an email via Gmail

**Args:**
- `to` (string, required)
- `subject` (string, required)
- `body` (string, required)
- `cc` (string, optional)
- `bcc` (string, optional)
- `is_html` (boolean, optional)
- `attachments` (array, optional)

**Returns:**
- `message_id` (string)
- `thread_id` (string)
- `status` (string)
- `to` (string)
- `subject` (string)

---

#### email.read
Read emails from Gmail

**Args:**
- `query` (string, optional) - Gmail search query
- `max_results` (integer, optional) - Default: 10

**Returns:**
- `emails` (array)
- `count` (integer)
- `next_page_token` (string)

---

### Messaging

#### message.send
Send a message to a Slack channel

**Args:**
- `channel` (string, required) - Channel ID or name
- `text` (string, required)
- `blocks` (array, optional) - Rich formatting
- `thread_ts` (string, optional) - Reply to thread

**Returns:**
- `message_id` (string)
- `channel` (string)
- `text` (string)
- `status` (string)

---

#### message.direct
Send a direct message on Slack

**Args:**
- `user_id` (string, required)
- `text` (string, required)

**Returns:**
- `message_id` (string)
- `channel` (string)
- `text` (string)
- `status` (string)

---

## Error Codes

- `400` - Bad Request (invalid payload)
- `403` - Forbidden (invalid API key)
- `404` - Not Found (capability doesn't exist)
- `500` - Internal Server Error (tool execution failed)

---

## Rate Limiting

No rate limiting currently implemented. Add as needed for production.

---

## Webhooks

OAuth callback endpoints:
- `/oauth/quickbooks/callback`
- `/oauth/hubspot/callback`
- `/oauth/google/callback`
- `/oauth/slack/callback`
