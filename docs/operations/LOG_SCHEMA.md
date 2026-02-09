# Stargate Lite Log Schema

Reference for building monitoring dashboards from structured logs.

## Log Format

All logs use structured JSON with consistent base fields:

```json
{
  "timestamp": "2025-12-26T10:30:00.000Z",
  "level": "info",
  "message": "Human readable message",
  "service": "netsuite",
  "log_event": "netsuite_je_created",
  "...": "additional context fields"
}
```

## Base Fields (All Logs)

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO8601 | Event timestamp |
| `level` | string | `debug`, `info`, `warning`, `error` |
| `message` | string | Human-readable description |
| `service` | string | Service/connector name |
| `log_event` | string | Machine-readable event type |

---

## Connectors

### NetSuite (`service: "netsuite"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `netsuite_api_request` | debug | `method`, `endpoint` | API call started |
| `netsuite_je_create` | info | `subsidiary_id` | Creating journal entry |
| `netsuite_je_created` | info | `journal_entry_id`, `tran_id` | Journal entry created |
| `netsuite_bill_create` | info | `vendor_id` | Creating vendor bill |
| `netsuite_bill_created` | info | `bill_id`, `amount` | Vendor bill created |
| `netsuite_bill_approve` | info | `bill_id` | Approving vendor bill |
| `netsuite_bill_approved` | info | `bill_id` | Vendor bill approved |
| `netsuite_po_create` | info | `vendor_id` | Creating purchase order |
| `netsuite_po_created` | info | `po_id`, `total` | Purchase order created |
| `netsuite_vendor_get` | info | `vendor_id` | Getting vendor |
| `netsuite_vendor_create` | info | `company_name` | Creating vendor |
| `netsuite_vendor_created` | info | `vendor_id` | Vendor created |
| `netsuite_suiteql_query` | info | `limit` | Executing SuiteQL |
| `netsuite_suiteql_complete` | info | `result_count` | Query completed |
| `netsuite_payment_create` | info | `vendor_id` | Creating payment |
| `netsuite_payment_created` | info | `payment_id`, `total` | Payment created |
| `netsuite_batch_payment_start` | info | `payment_count` | Batch started |
| `netsuite_batch_payment_complete` | info | `processed`, `failed` | Batch completed |
| `netsuite_batch_payment_error` | error | `vendor_id`, `error` | Batch item failed |
| `netsuite_doc_upload` | info | `vendor_id`, `file_name` | Uploading document |
| `netsuite_doc_uploaded` | info | `file_id`, `vendor_id` | Document attached |

### Plaid (`service: "plaid"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `plaid_api_request` | debug | `endpoint` | API call started |
| `plaid_link_token_create` | info | `products` | Creating link token |
| `plaid_link_token_created` | info | - | Link token created |
| `plaid_token_exchange` | info | - | Exchanging public token |
| `plaid_token_exchanged` | info | `item_id` | Token exchanged |
| `plaid_transactions_sync` | info | `has_cursor` | Syncing transactions |
| `plaid_transactions_synced` | info | `added_count`, `modified_count`, `removed_count` | Sync complete |
| `plaid_auth_get` | info | - | Getting auth data |
| `plaid_auth_retrieved` | info | `account_count` | Auth data retrieved |
| `plaid_transfer_create` | info | `transfer_type`, `amount`, `network` | Creating transfer |
| `plaid_transfer_created` | info | `transfer_id`, `status` | Transfer created |
| `plaid_transfer_get` | info | `transfer_id` | Getting transfer status |
| `plaid_identity_get` | info | - | Getting identity |
| `plaid_identity_retrieved` | info | `account_count` | Identity retrieved |
| `plaid_balance_get` | info | `account_count` | Getting balances |
| `plaid_balance_retrieved` | info | `account_count` | Balances retrieved |
| `plaid_accounts_get` | info | - | Getting accounts |
| `plaid_accounts_retrieved` | info | `account_count` | Accounts retrieved |
| `plaid_processor_token_create` | info | `processor` | Creating processor token |
| `plaid_processor_token_created` | info | `processor` | Processor token created |

### Stripe (`service: "stripe"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `stripe_payment_intent_create` | info | `amount`, `currency` | Creating payment intent |
| `stripe_payment_intent_created` | info | `payment_intent_id`, `status` | Payment intent created |
| `stripe_customer_create` | info | `email` | Creating customer |
| `stripe_customer_created` | info | `customer_id` | Customer created |
| `stripe_refund_create` | info | `payment_intent_id`, `amount` | Creating refund |
| `stripe_refund_created` | info | `refund_id`, `status` | Refund created |
| `stripe_balance_get` | info | - | Getting balance |
| `stripe_balance_retrieved` | info | `available`, `pending` | Balance retrieved |
| `stripe_transfer_create` | info | `amount`, `destination` | Creating transfer |
| `stripe_transfer_created` | info | `transfer_id` | Transfer created |
| `stripe_invoice_create` | info | `customer_id` | Creating invoice |
| `stripe_invoice_created` | info | `invoice_id`, `total` | Invoice created |
| `stripe_subscription_create` | info | `customer_id`, `price_id` | Creating subscription |
| `stripe_subscription_created` | info | `subscription_id`, `status` | Subscription created |

### QuickBooks (`service: "quickbooks"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `qbo_api_request` | debug | `method`, `endpoint` | API call |
| `qbo_token_refresh` | info | `realm_id` | Refreshing OAuth token |
| `qbo_token_refreshed` | info | `realm_id` | Token refreshed |

### Gmail (`service: "gmail"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `gmail_send` | info | `to`, `subject` | Sending email |
| `gmail_sent` | info | `message_id` | Email sent |
| `gmail_list` | info | `query`, `max_results` | Listing messages |
| `gmail_listed` | info | `count` | Messages listed |
| `gmail_get` | info | `message_id` | Getting message |
| `gmail_attachment_download` | info | `message_id`, `attachment_id` | Downloading attachment |

### Bill.com (`service: "billcom"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `billcom_bill_create` | info | `vendor_id`, `amount` | Creating bill |
| `billcom_bill_created` | info | `bill_id` | Bill created |
| `billcom_payment_create` | info | `vendor_id`, `amount` | Creating payment |
| `billcom_payment_created` | info | `payment_id` | Payment created |

---

## Utilities

### Financial Calculator (`service: "financial_calculator"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `calc_npv_success` | info | `num_periods`, `npv` | NPV calculated |
| `calc_irr_success` | info | `num_periods`, `irr`, `converged`, `iterations` | IRR calculated |
| `calc_amortization_success` | info | `principal`, `term_months`, `actual_months`, `total_interest` | Amortization schedule |
| `calc_depreciation_success` | info | `method`, `cost`, `useful_life`, `total_depreciation` | Depreciation schedule |
| `calc_compound_interest_success` | info | `principal`, `years`, `final_value` | Compound interest |
| `calc_payback_period_success` | info | `initial_investment`, `num_periods`, `payback_period`, `recovers` | Payback period |

### Web Search (`service: "web_search"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `tavily_search_start` | info | `query`, `search_depth`, `topic` | Search started |
| `tavily_search_success` | info | `result_count`, `has_answer` | Search completed |
| `tavily_search_timeout` | error | `query` | Search timed out |
| `tavily_search_error` | error | `error_type` | Search failed |
| `tavily_extract_start` | info | `url_count` | Extraction started |
| `tavily_extract_success` | info | `success_count`, `failed_count` | Extraction completed |
| `tavily_extract_timeout` | error | `url_count` | Extraction timed out |
| `tavily_extract_error` | error | `error_type` | Extraction failed |

### Summarizer (`service: "summarizer"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `claude_{op}_start` | info | `model`, `prompt_length` | Claude call started |
| `claude_{op}_success` | info | `model`, `input_tokens`, `output_tokens`, `cost_usd` | Claude call completed |
| `claude_{op}_rate_limited` | error | `model` | Rate limited |
| `claude_{op}_network_error` | error | `error_type` | Network error |
| `claude_{op}_error` | error | `error_type` | API error |

*`{op}` = `summary`, `executive_summary`, `extract_bullets`, `extract_key_facts`*

---

## Infrastructure

### HTTP Client (`service: varies`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `http_request` | debug | `method`, `url`, `service` | Request started |
| `http_response` | debug | `status_code`, `duration_ms` | Response received |
| `http_error` | error | `status_code`, `error` | Request failed |
| `http_retry` | warning | `attempt`, `max_retries` | Retrying request |

### Database (`service: "database"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `credential_stored` | info | `org_id`, `service` | Credential stored |
| `credential_retrieved` | debug | `org_id`, `service` | Credential retrieved |
| `credential_deleted` | info | `org_id`, `service` | Credential deleted |
| `token_refreshed` | info | `org_id`, `service` | OAuth token refreshed |

### Main API (`service: "stargate"`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `execute_start` | info | `capability_key`, `org_id` | Capability execution started |
| `execute_success` | info | `capability_key`, `duration_ms` | Execution completed |
| `execute_error` | error | `capability_key`, `error_type`, `error` | Execution failed |
| `auth_failed` | warning | `reason` | Authentication failed |

### Utility Base (`service: varies`)

| Event | Level | Fields | Description |
|-------|-------|--------|-------------|
| `utility_init_success` | info | `service` | Utility initialized |
| `utility_init_error` | error | `service`, `missing_vars` | Initialization failed |
| `utility_usage` | info | `tokens_in`, `tokens_out`, `cost_usd`, `total_calls`, `total_cost` | Usage tracked |
| `provider_rate_limited` | warning | `provider` | Provider rate limited |
| `provider_network_error` | warning | `provider`, `error` | Provider network error |
| `all_providers_failed` | error | `errors` | All providers failed |

---

## Dashboard Queries

### Total API Calls by Service (Last 24h)
```sql
SELECT service, COUNT(*) as calls
FROM logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
  AND log_event LIKE '%_created' OR log_event LIKE '%_success'
GROUP BY service
ORDER BY calls DESC
```

### Error Rate by Service
```sql
SELECT
  service,
  COUNT(*) FILTER (WHERE level = 'error') as errors,
  COUNT(*) as total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE level = 'error') / COUNT(*), 2) as error_rate
FROM logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY service
```

### Cost Tracking (Summarizer/Search)
```sql
SELECT
  DATE_TRUNC('hour', timestamp) as hour,
  service,
  SUM(cost_usd) as total_cost,
  SUM(tokens_in) as total_tokens_in,
  SUM(tokens_out) as total_tokens_out
FROM logs
WHERE log_event = 'utility_usage'
  AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour, service
ORDER BY hour DESC
```

### Transaction Volume (Financial)
```sql
SELECT
  DATE_TRUNC('hour', timestamp) as hour,
  SUM(CASE WHEN log_event = 'netsuite_je_created' THEN 1 ELSE 0 END) as journal_entries,
  SUM(CASE WHEN log_event = 'netsuite_bill_created' THEN 1 ELSE 0 END) as vendor_bills,
  SUM(CASE WHEN log_event = 'netsuite_payment_created' THEN 1 ELSE 0 END) as payments,
  SUM(CASE WHEN log_event = 'plaid_transfer_created' THEN 1 ELSE 0 END) as transfers
FROM logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC
```

### Slow Operations (P95 Latency)
```sql
SELECT
  capability_key,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_ms,
  AVG(duration_ms) as avg_ms,
  COUNT(*) as calls
FROM logs
WHERE log_event = 'execute_success'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY capability_key
ORDER BY p95_ms DESC
LIMIT 10
```

---

## Recommended Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | error_rate > 5% over 5 min | Critical |
| Provider Down | `all_providers_failed` count > 0 | Critical |
| Rate Limited | `*_rate_limited` count > 10/min | Warning |
| Slow Execution | p95 latency > 10s | Warning |
| Cost Spike | hourly cost > 2x average | Warning |
| Auth Failures | `auth_failed` count > 5/min | Warning |
