# Changelog

All notable changes to Stargate Lite are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
