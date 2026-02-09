# Changelog

All notable changes to Stargate Lite are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 35+ new capabilities across Google, Microsoft, Dropbox, DocuSign, and PowerBI platforms
- Alembic database migrations for schema versioning
- OpenAPI contract tests for `/execute` response validation
- `retry_strategy` field in error responses for client-side retry guidance
- Dynamic `ENABLED_SERVICES` configuration (replaces hardcoded list)
- `connect_url` in `CREDENTIALS_MISSING` error responses for OAuth onboarding
- Expanded HubSpot capabilities
- Ramp and Plaid connector stubs
- Staging demo script for QBO sandbox testing
- Locked schema system for N3 API contracts
- Xero OAuth 2.0 flow and deep links for all entity responses

### Changed
- Hyperbrowser v2 mixin architecture (base -> actions -> workflows -> connector)
- Slack, Stripe, and QuickBooks connectors reorganized into modular packages
- Registry reorganized by service category under `app/registry/`
- Docs directory restructured into `contracts/`, `operations/`, `architecture/`, `design/`, `analysis/`, `schemas/`, `archive/`
- Consolidated `.env.template` into `.env.example` (single canonical template)
- Removed stale test fixtures from project root

### Fixed
- Slack type annotations for mypy strict compliance
- SQL query construction sanitized to address bandit security warnings
- QuickBooks token exchange logging (log Intuit response body on failure)
- QuickBooks env guard preventing staging from hitting production QBO

### Security
- PKCE-based stateless OAuth flow for all OAuth connectors
- HMAC-signed OAuth state parameter for Stripe Connect

## [0.11.0] - 2026-02-02

### Added
- **Xero deep links**: All Xero entity responses now include a `deep_link` field
  with a direct URL to open the record in the Xero web interface (go.xero.com).
  - Supports 9 entity types: invoices (AR), bills (AP), contacts, credit notes
    (AR/AP routing), bank transactions, bank accounts, bank transfers, manual
    journals, and payments (links to parent invoice/bill)
  - Chart of accounts entries link to the CoA list page (no per-account page in Xero)
  - URL patterns follow official Xero deep linking documentation
    (https://developer.xero.com/documentation/guides/how-to-guides/deep-link-xero)
  - Links require the user to be logged into the correct Xero organisation
  - New module: `app/connectors/xero/deep_links.py`

### Changed
- All 7 Xero connector modules updated: contacts, invoices, bills, credit_notes,
  payments, bank, reports

## [0.10.0] - 2026-01-29

### Added
- **QuickBooks deep links**: All QBO entity responses now include a `deep_link` field
  with a direct URL to open the record in the QuickBooks Online web interface.
  - Supports 17 entity types: invoices, bills, bill payments, customer payments,
    journal entries, estimates, purchase orders, expenses, credit memos, refund
    receipts, sales receipts, deposits, transfers, vendors, customers, employees,
    accounts, and items
  - Transaction URLs use `?txnId=` parameter; name-based entities use `?nameId=`;
    accounts use `?accountId=`; items use `?itemId=`
  - Links require the user to be logged into the correct QBO company
  - New module: `app/connectors/quickbooks/deep_links.py`
- **Schema updates**: All QuickBooks capability schemas now document the `deep_link`
  return field, ensuring Aleq discovers and surfaces these URLs to users

### Changed
- All 7 QuickBooks connector modules updated: invoices, vendors, customers, bills,
  payments, accounting, items

## [0.9.0] - 2025-01-24

Initial pre-release with production hardening.

### Added
- **Rate limiting**: Redis-based sliding window rate limiter (100 req/min per org)
  - `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers
  - Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`
- **PostHog analytics**: Server-side event tracking
  - Events: `capability_called`, `connector_error`, `token_refreshed`, `fci_aggregation`
  - Session ID correlation via `X-Session-ID` header
- **Sentry integration**: Error tracking with full context
- **FCI (Financial Command Interface)**: Multi-source financial data aggregation
- **Bill.com connector**: AP automation with Redis session caching
- **Recurly connector**: 12 subscription billing capabilities
- **Cognitive utilities**: Web search, summarization, financial calculations
- **Financial operations**: Reconciliation, matching, covenants, waterfall
- **NetSuite connector**: Journal entries, vendor bills, SuiteQL
- **Sage Intacct connector**: GL, AP, AR, cash management
- **Shopify connector**: Orders, products, fulfillment
- **Square connector**: Payments, orders, customers
- **Core connectors**: QuickBooks, Stripe, HubSpot, Gmail, Slack
- **Multi-tenant credentials**: `{org_id}:{user_id}:{service}` isolation
- **Encrypted token storage**: Fernet symmetric encryption
- **Automatic token refresh**: Transparent expiry handling
- **Release engineering**: Pre-commit hooks, RELEASE_GUIDE.md, CHANGELOG.md
- **Version in health endpoint**: `/health` returns `version` and `capabilities_count`

### Security
- Production safety filter: Disabled high-risk services (ibkr, schwab, blandai, twilio, hyperbrowser)
- Rate limiting protects against abuse
- All OAuth tokens encrypted at rest

---

## Roadmap to 1.0

Before releasing v1.0.0:
- [ ] Production deployment validated (real traffic)
- [ ] All connectors tested end-to-end with real credentials
- [ ] Monitoring (Sentry, PostHog) verified in production
- [ ] Rate limiting tuned based on actual usage
- [ ] API stable (no breaking changes planned)
- [ ] Documentation complete
