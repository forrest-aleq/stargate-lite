# Capability Schema Request for Translator Training

**From:** TAMI Training Team
**To:** Integrations Team
**Date:** 2026-01-19
**Priority:** High - Blocking model training

---

## What We're Building

Translator models that convert work units → API calls:

```
"Create a bill for Vendor ABC, $2,355.68"  →  { "capability": "bill.create", "params": {...} }
```

---

## What We Need Per System

1. Complete capability list
2. Schema for each capability (params, types, required/optional)
3. Example of a valid call

---

## DEFINITIVE INTEGRATION LIST

Extracted from 1.6M motor instances. This is what finance professionals actually use.

### Tier 1: Critical (40K+ instances)

| System | Instances | Category |
|--------|-----------|----------|
| Excel | 442,862 | Productivity |
| SAP | 109,696 | ERP |
| Slack | 85,580 | Communication |
| Outlook | 75,891 | Communication |
| QuickBooks | 68,800 | Accounting |
| Oracle | 47,830 | ERP |
| NetSuite | 44,618 | ERP |

### Tier 2: High Priority (10K-40K instances)

| System | Instances | Category |
|--------|-----------|----------|
| Sage Intacct | 24,350 | Accounting |
| ADP | 15,788 | Payroll |
| Tyler Munis | 12,738 | Government |
| Yardi | 11,961 | Real Estate |
| SharePoint | 11,643 | Productivity |
| Deltek | 10,703 | Gov Contractors |

### Tier 3: Medium Priority (5K-10K instances)

| System | Instances | Category |
|--------|-----------|----------|
| Microsoft Teams | 9,324 | Communication |
| Workday | 8,435 | HR/Finance |
| Sage 300 CRE | 8,119 | Construction |
| Epic | 7,618 | Healthcare |
| Workiva | 7,542 | Compliance |
| Elite 3E | 7,398 | Legal |
| Adobe Acrobat | 7,137 | Document |
| FASB ASC | 6,895 | Reference |
| Wells Fargo | 5,847 | Banking |

### Tier 4: Medium (2K-5K instances)

| System | Instances | Category |
|--------|-----------|----------|
| Bloomberg | 4,980 | Finance |
| Salesforce | 4,844 | CRM |
| Chase | 4,766 | Banking |
| SQL Server | 4,719 | Database |
| Adaptive Insights | 4,625 | FP&A |
| Viewpoint | 4,605 | Construction |
| FIS | 4,559 | Banking Tech |
| Aderant | 3,712 | Legal |
| AppFolio | 3,658 | Real Estate |
| Bank of America | 3,604 | Banking |
| Epicor | 3,452 | ERP |
| Concur | 3,438 | Expense |
| Blackbaud | 3,420 | Nonprofit |
| Procore | 3,380 | Construction |
| Toast | 3,193 | Hospitality |
| QAD | 3,165 | Manufacturing |
| Clio | 2,997 | Legal |
| NISC | 2,984 | Utilities |
| CCH | 2,904 | Tax |
| JPMorgan | 2,903 | Banking |
| Jack Henry | 2,900 | Banking Core |
| Symitar | 2,792 | Credit Unions |
| Zoom | 2,753 | Communication |
| Tableau | 2,630 | Analytics |
| WolfePak | 2,442 | Oil & Gas |
| Infor | 2,334 | ERP |
| ServiceNow | 2,329 | ITSM |
| Coupa | 2,284 | Procurement |
| Google Sheets | 2,269 | Productivity |
| Thomson Reuters | 2,177 | Tax |
| Kyriba | 2,037 | Treasury |

### Tier 5: Lower Priority (1K-2K instances)

| System | Instances | Category |
|--------|-----------|----------|
| Carta | 1,846 | Equity |
| Meditech | 1,844 | Healthcare |
| Bill.com | 1,819 | Payments |
| athenahealth | 1,791 | Healthcare |
| ServiceTitan | 1,742 | Field Service |
| Square | 1,691 | Payments |
| Guidewire | 1,657 | Insurance |
| SS&C Geneva | 1,607 | Investment |
| DocuSign | 1,593 | E-Signature |
| Hyperion | 1,483 | Consolidation |
| Shopify | 1,446 | E-commerce |
| Lease (LeaseQuery etc) | 1,377 | Lease Accounting |
| Google Drive | 1,367 | Storage |
| Veeva | 1,336 | Life Sciences |
| SEC EDGAR | 1,330 | Compliance |
| PointClickCare | 1,272 | Healthcare |
| OpenLink Endur | 1,259 | ETRM |
| Stripe | 1,232 | Payments |
| Kronos | 1,176 | Workforce |
| Airtable | 1,161 | Productivity |
| Avalara | 1,116 | Tax |
| LinkedIn | 1,102 | Social |
| EFTPS | 1,095 | Tax Filing |
| Expensify | 1,057 | Expense |
| LoanPro | 1,032 | Lending |

### Tier 6: Specialized (500-1K instances)

| System | Instances | Category |
|--------|-----------|----------|
| Drake | 977 | Tax |
| Anaplan | 975 | Planning |
| Power BI | 940 | Analytics |
| OneSource | 917 | Tax |
| Buildertrend | 879 | Construction |
| PNC | 853 | Banking |
| Harvest | 849 | Time Tracking |
| Gusto | 723 | Payroll |
| Duck Creek | 718 | Insurance |
| Monday.com | 687 | Project Mgmt |
| Zuora | 661 | Subscription |
| MarketMan | 624 | Hospitality |
| BambooHR | 614 | HR |
| HSBC | 613 | Banking |
| BlackLine | 606 | Close Mgmt |
| Dropbox | 588 | Storage |
| Fiserv | 570 | Banking Tech |
| Snowflake | 545 | Data |
| Citi | 538 | Banking |

### Tier 7: Emerging/Niche (100-500 instances)

| System | Instances | Category |
|--------|-----------|----------|
| Notion | 476 | Productivity |
| Vertex | 446 | Tax |
| Wave | 397 | Accounting |
| Jira | 392 | Project Mgmt |
| Confluence | 364 | Wiki |
| gTreasury | 303 | Treasury |
| Costar | 254 | Real Estate |
| SVB | 247 | Banking |
| Brex | 241 | Corporate Card |
| Paychex | 237 | Payroll |
| OneStream | 205 | Consolidation |
| Xero | 182 | Accounting |
| Paylocity | 174 | Payroll |
| Asana | 174 | Project Mgmt |
| Looker | 143 | Analytics |
| Mercury | 141 | Banking |
| Ramp | 137 | Corporate Card |
| Buildium | 119 | Real Estate |
| Rippling | 78 | HR/Payroll |
| UltiPro | 74 | HR |
| Paycom | 67 | Payroll |
| PayPal | 64 | Payments |
| Sovos | 60 | Tax |
| Ceridian | 55 | HR |
| Vena | 48 | FP&A |
| HubSpot | 43 | CRM |
| CorpTax | 40 | Tax |
| TaxJar | 31 | Tax |
| Chargebee | 22 | Subscription |
| Planful | 12 | FP&A |

### Tier 8: Long Tail (<100 instances)

Zoho, Magento, dbt, Melio, Stampli, Tipalti, WooCommerce, Mosaic, etc.

---

## Schema Format

```json
{
  "capability": "bill.create",
  "system": "quickbooks",
  "description": "Creates a new bill",
  "params": {
    "vendor_id": { "type": "string", "required": true },
    "amount": { "type": "number", "required": true },
    "line_items": { "type": "array", "required": true }
  },
  "example": {
    "capability": "bill.create",
    "params": { "vendor_id": "VEN-1234", "amount": 2355.68, "line_items": [...] }
  }
}
```

---

## Priority Recommendation

**Start with Tier 1-2** (13 systems) = covers 70%+ of training data.

Then Tier 3-4 (30 systems) = covers 90%+.

---

## Questions?

Slack or reply to this doc.
