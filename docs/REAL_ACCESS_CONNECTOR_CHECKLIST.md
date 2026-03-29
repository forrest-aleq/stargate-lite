# Real Access Connector Checklist

Last verified against `stargate-lite` Railway `staging` on `2026-03-28`.

This is the actual readiness sheet for making connectors live in Aleq.

- Connector envs belong on `stargate-lite`, not `baby-mars`.
- A connector also needs to be present in `ENABLED_SERVICES` to show up in Aleq.
- Status meanings:
  - `Ready now`: staged and connectable today
  - `Partial`: surfaced, but missing envs or OAuth pieces
  - `Missing`: not ready in staging

## Runtime and Research

- `Ready now` `E2B`
  Env: `E2B_API_KEY`
- `Ready now` `Hyperbrowser`
  Env: `HYPERBROWSER_API_KEY`
- `Ready now` `Tavily`
  Env: `TAVILY_API_KEY`
- `Missing` `Google AI`
  Needed: `GOOGLE_AI_API_KEY`

## Ready Now on Staging

- `QuickBooks`
  Present: `QUICKBOOKS_CLIENT_ID`, `QUICKBOOKS_CLIENT_SECRET`, `QUICKBOOKS_REDIRECT_URI`
- `Xero`
  Present: `XERO_CLIENT_ID`, `XERO_CLIENT_SECRET`, `XERO_REDIRECT_URI`
- `HubSpot`
  Present: `HUBSPOT_CLIENT_ID`, `HUBSPOT_CLIENT_SECRET`, `HUBSPOT_REDIRECT_URI`
- `Google`
  Present: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `Slack`
  Present: `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_REDIRECT_URI`
- `Plaid`
  Present: `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENVIRONMENT`
- `Ramp`
  Present: `RAMP_CLIENT_ID`, `RAMP_CLIENT_SECRET`, `RAMP_REDIRECT_URI`

## Partial on Staging

- `Stripe`
  Present: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`
  Missing: `STRIPE_CLIENT_ID`, `STRIPE_REDIRECT_URI`
  Note: backend access works; customer self-serve connect does not.

## Missing on Staging

- `Zoho Books`
  Missing: `ZOHO_BOOKS_CLIENT_ID`, `ZOHO_BOOKS_CLIENT_SECRET`, `ZOHO_BOOKS_REDIRECT_URI`, `ZOHO_BOOKS_ACCOUNTS_SERVER`
  Note: implemented in code, but no staging envs yet.
- `Microsoft`
  Missing: `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_REDIRECT_URI`
- `Power BI`
  Missing: `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_REDIRECT_URI`
- `NetSuite`
  Missing: `NETSUITE_ACCOUNT_ID`, `NETSUITE_CONSUMER_KEY`, `NETSUITE_CONSUMER_SECRET`, `NETSUITE_REDIRECT_URI`
- `Brex`
  Missing: `BREX_CLIENT_ID`, `BREX_CLIENT_SECRET`, `BREX_REDIRECT_URI`
- `Chase`
  Missing: `CHASE_CLIENT_ID`, `CHASE_CLIENT_SECRET`, `CHASE_REDIRECT_URI`
- `Schwab`
  Missing: `SCHWAB_CLIENT_ID`, `SCHWAB_CLIENT_SECRET`, `SCHWAB_REDIRECT_URI`
- `Notion`
  Missing: `NOTION_CLIENT_ID`, `NOTION_CLIENT_SECRET`, `NOTION_REDIRECT_URI`
- `Asana`
  Missing: `ASANA_CLIENT_ID`, `ASANA_CLIENT_SECRET`, `ASANA_REDIRECT_URI`
- `ClickUp`
  Missing: `CLICKUP_CLIENT_ID`, `CLICKUP_CLIENT_SECRET`, `CLICKUP_REDIRECT_URI`
- `Monday`
  Missing: `MONDAY_CLIENT_ID`, `MONDAY_CLIENT_SECRET`, `MONDAY_REDIRECT_URI`
- `Linear`
  Missing: `LINEAR_CLIENT_ID`, `LINEAR_CLIENT_SECRET`, `LINEAR_REDIRECT_URI`
- `Airtable`
  Missing: `AIRTABLE_CLIENT_ID`, `AIRTABLE_CLIENT_SECRET`, `AIRTABLE_REDIRECT_URI`
- `Gusto`
  Missing: `GUSTO_CLIENT_ID`, `GUSTO_CLIENT_SECRET`, `GUSTO_REDIRECT_URI`
- `Shopify`
  Missing: `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `SHOPIFY_REDIRECT_URI`
- `Square`
  Missing: `SQUARE_APPLICATION_ID`, `SQUARE_APPLICATION_SECRET`, `SQUARE_REDIRECT_URI`
- `DocuSign`
  Missing: `DOCUSIGN_INTEGRATION_KEY`, `DOCUSIGN_SECRET_KEY`, `DOCUSIGN_REDIRECT_URI`

## Key-Only or Backend-Only Lanes Not Yet Surfaced

- `Mercury`
  Missing: `MERCURY_API_KEY`
- `Recurly`
  Missing: `RECURLY_API_KEY`

## Highest-Leverage Next Adds

1. `Stripe` customer OAuth
   Add `STRIPE_CLIENT_ID` and `STRIPE_REDIRECT_URI`
2. `Microsoft`
   Unlocks Microsoft Graph, Excel, OneDrive, Outlook, and Power BI together
3. `Zoho Books`
   Already implemented; just needs the provider app env set
4. `Brex` and `Chase`
   Best next spend and banking cross-reference lanes after QBO, Plaid, and Ramp

## Notes

- `stargate-lite` staging currently exposes the full connector catalog in Aleq because `ENABLED_SERVICES` already includes the broad set.
- Some connectors are visible but intentionally fail cleanly until the missing envs above are added.
- Stripe is the most obvious example of a connector that is partly ready today.
