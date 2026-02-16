# Stargate Lite - Integration Status

**Last updated:** 2026-02-14
**Total capabilities registered:** 771
**Total active (with env keys set):** ~409
**Services:** 45

---

## Fully Complete Integrations

These have: real API implementations, OAuth/auth routes, credential storage, and are production-ready.

### Tier 1: Core Financial (274 capabilities)

| Service | Capabilities | Connector | OAuth | Credential Storage | Notes |
|---------|-------------|-----------|-------|--------------------|-------|
| QuickBooks Online | 79 | `connectors/quickbooks/` (11 files) | `oauth/quickbooks.py` | CredentialManager + realm_id | Full: vendors, customers, bills, invoices, journals, items, payments, accounting, reports, deep links |
| Stripe | 75 | `connectors/stripe/` (12 files) | `oauth/stripe.py` | CredentialManager + env key | Full: payments, payouts, balance, Connect, subscriptions, disputes, checkout, invoices, products, customers |
| Xero | 61 | `connectors/xero/` (9 files) | `oauth/xero.py` | CredentialManager | Full: invoices, bills, contacts, payments, bank, credit notes, reports, deep links |
| Sage Intacct | 44 | `connectors/sage_intacct/` (7 files) | **MISSING ROUTER** | CredentialManager | Full API impl but no OAuth route for customer connection |
| Bill.com | 22 | `connectors/billcom/` (5 files) | N/A (session auth) | CredentialManager + Redis session cache | Session-based auth, not OAuth. 35-min session expiry managed. |
| NetSuite | 20 | `connectors/netsuite/` (6 files) | `oauth/netsuite.py` | CredentialManager (OAuth2 + TBA) | Supports both OAuth 2.0 and Token-Based Auth with HMAC-SHA256 |

### Tier 2: CRM + Communication (76 capabilities)

| Service | Capabilities | Connector | OAuth | Credential Storage | Notes |
|---------|-------------|-----------|-------|--------------------|-------|
| HubSpot | 36 | `connectors/hubspot/` (10 files) | `oauth/hubspot.py` | CredentialManager | Contacts, companies, deals, tickets, notes, associations, pipelines, owners, properties |
| Slack | 22 | `connectors/slack/` (3 files) | `oauth/slack.py` | CredentialManager | Uses official `slack_sdk`. Channels, messaging, users, files, reactions |
| Gmail | 18 | `connectors/gmail/` (4 files) | `oauth/google.py` | CredentialManager | Google API Python Client. Send, draft, read, labels, threads, search, watch |

### Tier 3: Google Suite (23 capabilities)

| Service | Capabilities | Connector | OAuth | Credential Storage | Notes |
|---------|-------------|-----------|-------|--------------------|-------|
| Google Drive | 7 | `connectors/google_drive.py` | `oauth/google.py` (shared) | CredentialManager | Upload, download, list, create folder, search, metadata |
| Google Sheets | 9 | `connectors/google_sheets.py` | `oauth/google.py` (shared) | CredentialManager | Read, write, append, batch update, create spreadsheet |
| Google Calendar | 7 | `connectors/google_calendar.py` | `oauth/google.py` (shared) | CredentialManager | Events CRUD, free/busy, list calendars |

### Tier 4: HR, E-Commerce, E-Signatures (69 capabilities)

| Service | Capabilities | Connector | OAuth | Credential Storage | Notes |
|---------|-------------|-----------|-------|--------------------|-------|
| Gusto | 17 | `connectors/gusto/` (6 files) | `oauth/hr_payroll.py` | CredentialManager | Employees, payroll, tax forms, contractors, company. Demo mode supported |
| Shopify | 19 | `connectors/shopify/` (6 files) | `oauth/ecommerce.py` | CredentialManager | Orders, products, customers, fulfillment, payouts, shop info |
| Square | 19 | `connectors/square/` (6 files) | `oauth/ecommerce.py` | CredentialManager | Payments, orders, customers, invoices, payouts, locations. Sandbox supported |
| DocuSign | 14 | `connectors/docusign.py` | `oauth/esignature.py` | CredentialManager | Envelopes, recipients, templates, documents, tabs. Demo mode supported |

### Tier 5: Productivity + Project Management (81 capabilities)

| Service | Capabilities | Connector | OAuth | Credential Storage | Notes |
|---------|-------------|-----------|-------|--------------------|-------|
| Airtable | 13 | `connectors/airtable.py` | `oauth/productivity_db.py` | CredentialManager | PKCE flow. Bases, tables, records CRUD, search, meta API |
| Linear | 10 | `connectors/linear/` (3 files) | `oauth/notes_issues.py` | CredentialManager | GraphQL API. Issues CRUD, comments, teams |
| ClickUp | 12 | `connectors/clickup/` (3 files) | `oauth/task_managers.py` | CredentialManager | Tasks CRUD, lists, spaces |
| Monday | 13 | `connectors/monday/` (3 files) | `oauth/task_managers.py` | CredentialManager | GraphQL API. Items, boards, column values, users |
| Ramp | 29 | `connectors/ramp/` (5 files) | `oauth/fintech.py` | CredentialManager | Cards, transactions, expenses, accounting sync, treasury, HR |
| Microsoft Excel | ~7 | `connectors/microsoft_excel.py` | `oauth/microsoft.py` | CredentialManager | Graph API. Range get/update, sheet create, workbook ops |
| Microsoft OneDrive | ~7 | `connectors/microsoft_onedrive.py` | `oauth/microsoft.py` | CredentialManager | Graph API. Upload, download, list, folders, metadata |
| Microsoft Outlook Calendar | ~6 | `connectors/microsoft_outlook_calendar.py` | `oauth/microsoft.py` | CredentialManager | Graph API. Events CRUD, availability, calendars |
| PowerBI | 12 | `connectors/powerbi.py` | `oauth/microsoft.py` | **args.get (no CredentialManager)** | Datasets, reports, dashboards, workspaces, refresh |

### Tier 6: Banking + FinTech (51 capabilities)

| Service | Capabilities | Connector | OAuth | Credential Storage | Notes |
|---------|-------------|-----------|-------|--------------------|-------|
| Plaid | 17 | `connectors/plaid.py` | N/A (Link flow) | env keys + args | Link tokens, transactions sync, auth, transfers, identity, balance, investments |
| Recurly | 12 | `connectors/recurly.py` | N/A (API key) | `RECURLY_API_KEY` env | Accounts, subscriptions, invoices, add-ons, coupons, usage |
| Mercury | 6 | `connectors/mercury.py` | N/A (API key) | `MERCURY_API_KEY` env | Accounts, transactions, payments, recipients, wires |
| Brex | 8 | `connectors/brex.py` | `oauth/fintech.py` | **args.get (no CredentialManager)** | Transactions, expenses, virtual cards, payments, balances |
| Chase | 8 | `connectors/chase.py` | `oauth/fintech.py` | **args.get (no CredentialManager)** | ACH, wires, accounts, transactions, payment status |

### Tier 7: Cognitive Utilities (53 capabilities, no auth needed)

| Service | Capabilities | Connector | Auth | Notes |
|---------|-------------|-----------|------|-------|
| Financial Calculator | 6 | `utilities/financial_calculator/` | None | Pure math. NPV, IRR, amortization, depreciation, compound interest, payback |
| Financial Ops | 12 | `utilities/financial_ops/` | None | Reconciliation, matching, covenants, waterfall, tiered fees, forecasting |
| FCI (Financial Context) | 16 | `utilities/fci/` | Via connected services | Cross-service aggregation: AP/AR aging, burn rate, runway, payroll, expenses |
| Web Search | 4 | `utilities/web_search.py` | `TAVILY_API_KEY` | Tavily API. Web search, news, content extraction |
| Summarizer | 5 | `utilities/summarizer.py` | `ANTHROPIC_API_KEY` | Claude API. Text, executive, bullets, key facts |
| OCR | 6 | `connectors/ocr_utility/` | `GEMINI_API_KEY` | Gemini vision + optional deepdoctection |
| Workflow | 4 | inline lambdas | None | Orchestration signals (request info, notify, approve, schedule) |

### Tier 8: Automation + Vault (25 capabilities, key-gated)

| Service | Capabilities | Connector | Auth | Notes |
|---------|-------------|-----------|------|-------|
| Hyperbrowser | 12 | `connectors/hyperbrowser_v2/` | `HYPERBROWSER_API_KEY` | Claude Computer Use via Hyperbrowser cloud. Sessions, screenshots, browser automation |
| BlandAI | 7 | `connectors/blandai.py` | `BLANDAI_API_KEY` | Voice calls. Send, batch, transcripts, recordings, phone numbers |
| Twilio | 7 | `connectors/twilio_sms.py` | `TWILIO_ACCOUNT_SID` | SMS/MMS. Send, status, list, incoming, scheduled |
| Bitwarden | 6 | `connectors/bitwarden.py` | `BWS_ACCESS_TOKEN` | Secrets Manager. Get, list, create secrets |

---

## Disabled (Always Off)

| Service | Capabilities | Connector | Why Disabled |
|---------|-------------|-----------|--------------|
| Interactive Brokers | 15 | `connectors/ibkr.py` | HIGH RISK - live trading. Requires explicit approval |
| Charles Schwab | 12 | `connectors/schwab.py` | HIGH RISK - live trading. Requires explicit approval |

---

## Known Gaps

### Missing OAuth Routers
| Service | Has Connector | Has Registry | Missing |
|---------|--------------|-------------|---------|
| Sage Intacct | Yes (44 caps) | Yes | No OAuth authorize/callback route. Customers can't connect. |
| Dropbox | Yes (8 caps) | Yes | No OAuth authorize/callback route. Customers can't connect. |

### No CredentialManager (tokens not stored per org/user)
These connectors take `access_token` from `args` at call time instead of storing in the encrypted credential DB. Multi-tenant isolation gap.

| Service | Current Pattern | Impact |
|---------|----------------|--------|
| Asana | `args.get("access_token")` or `ASANA_API_KEY` env | Caller must pass token every request |
| Notion | `args.get("access_token")` or `NOTION_API_KEY` env | Caller must pass token every request |
| PowerBI | `args.get("access_token")` or env vars | Caller must pass token every request |
| Brex | `args.get("access_token")` | Caller must pass token every request |
| Chase | `args.get("access_token")` | Caller must pass token every request |
| Plaid | Comment says "In production, this would go to CredentialManager" | Link exchange token not persisted |

### Other Issues
- **OCR Gemini model:** References `gemini-3-flash-preview` which is not a valid model name. Will fail at runtime.

---

## Score Card

| Category | Count | Status |
|----------|-------|--------|
| Fully complete (connector + OAuth + CredentialManager) | **28 services, 600 capabilities** | Production-ready |
| Real implementation but missing CredentialManager | **5 services, 52 capabilities** | Works but multi-tenant gap |
| Real implementation but missing OAuth router | **2 services, 52 capabilities** | Can't onboard customers |
| Always disabled (trading) | **2 services, 27 capabilities** | Intentionally locked |
| Cognitive utilities (no auth needed) | **7 services, 53 capabilities** | Production-ready |
| Key-gated automation | **4 services, 32 capabilities** | Production-ready when keys set |

**Bottom line: 771 capabilities registered, 653 fully wired end-to-end, 52 missing credential storage, 52 missing OAuth routes, 27 intentionally disabled.**
