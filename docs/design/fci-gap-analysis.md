# FCI Gap Analysis: What's Missing for Full Support

## Executive Summary

**Current State:** 322 production endpoints across 20 platforms + utilities
**FCI Requirements:** ~95% of raw data available, missing orchestration layer
**Gap:** Need FCI-specific utilities (~8 new capabilities) + orchestration logic

---

## Part 1: FCI Primitive Mapping

### 1.1 Data Primitives - What We Have

| FCI Primitive | Required Data | Existing Endpoints | Status |
|---------------|---------------|-------------------|--------|
| `@cash` | All bank balances | `plaid.balance.get`, `mercury.transaction.get`, `brex.balance.get`, `chase.balance.get`, `sage_intacct.bank_accounts.balance`, `xero.bank.accounts.list` | **Data exists** - needs aggregation |
| `@ar` | Outstanding receivables | `report.ar_aging`, `qb.invoice.list_outstanding`, `xero.ar.aging`, `sage_intacct.reports.ar_aging` | **Data exists** - needs computation |
| `@ap` | Outstanding payables | `report.ap_aging`, `billcom.bill.list`, `xero.ap.aging`, `sage_intacct.reports.ap_aging` | **Data exists** - needs computation |
| `@burn` | Monthly expenses | `report.profitloss`, `xero.report.profit_loss`, `sage_intacct.reports.cash_flow` | **Data exists** - needs time-series calc |
| `@runway` | Cash / Burn | Derived from @cash / @burn | **Calculation** - needs both inputs |
| `@revenue` | Income totals | `report.profitloss`, P&L revenue section | **Data exists** |
| `@expenses` | Expense totals | `report.profitloss`, P&L expense section | **Data exists** |
| `@payroll` | Payroll totals | `gusto.payrolls.list`, `gusto.payroll.get` | **Data exists** |

### 1.2 Entity Primitives - What We Have

| FCI Primitive | Required Data | Existing Endpoints | Status |
|---------------|---------------|-------------------|--------|
| `@customer:name` | Customer lookup | `customer.search` (QB), `stripe.customer.search`, `shopify.customers.list`, `xero.contact.search`, `sage_intacct.customers.list` | **Data exists** - needs cross-service resolution |
| `@vendor:name` | Vendor lookup | `vendor.search` (QB), `billcom.vendor.list`, `netsuite.vendor.search`, `xero.contact.list`, `sage_intacct.vendors.list` | **Data exists** - needs cross-service resolution |
| `@invoice:id` | Invoice lookup | `invoice.get` (QB), `stripe.invoice.retrieve`, `xero.invoice.get`, `sage_intacct.invoices.get` | **Data exists** - needs service detection |
| `@payment:id` | Payment lookup | `payment.get` (QB), `charge.retrieve` (Stripe), `xero.payment.get`, `sage_intacct.ar_payments.list` | **Data exists** - needs service detection |
| `@person:name` | Contact lookup | `employee.list` (QB), `gusto.employees.list` | **Partial** - needs contact aggregation |

---

## Part 2: Missing Utilities

### 2.1 FCI Metric Engine (NEW)

**Purpose:** Compute FCI data primitives from raw endpoints

```python
# Capability: fci.metric.cash
# Returns: { value, currency, trend, sparkline_data, breakdown_by_account }

# Capability: fci.metric.ar
# Returns: { total, current, 30_day, 60_day, 90_day, over_90, count }

# Capability: fci.metric.ap
# Returns: { total, current, 30_day, 60_day, 90_day, over_90, count }

# Capability: fci.metric.burn
# Returns: { monthly_avg, last_month, trend, projected_next }

# Capability: fci.metric.runway
# Returns: { months, cash_out_date, confidence }

# Capability: fci.metric.revenue
# Returns: { mtd, ytd, last_month, trend, mrr_if_applicable }

# Capability: fci.metric.expenses
# Returns: { mtd, ytd, last_month, trend, by_category }

# Capability: fci.metric.payroll
# Returns: { last_run, next_run, monthly_total, headcount }
```

**Implementation:** Orchestrates calls to existing endpoints + computes derived values

### 2.2 FCI Entity Resolver (NEW)

**Purpose:** Cross-service entity lookup with fuzzy matching

```python
# Capability: fci.entity.customer
# Input: { name: "acme" }
# Returns: {
#   matches: [{ service, id, name, confidence }],
#   primary: { service, id, name, email, balance, last_activity }
# }

# Capability: fci.entity.vendor
# Input: { name: "aws" }
# Returns: {
#   matches: [{ service, id, name, confidence }],
#   primary: { service, id, name, balance, last_payment }
# }
```

**Implementation:**
1. Query all connected services in parallel
2. Use `match.fuzzy` to score results
3. Return deduplicated, ranked matches

### 2.3 FCI Math Parser (NEW)

**Purpose:** Parse and evaluate FCI expressions

```python
# Capability: fci.parse.expression
# Input: { expression: "@cash + @ar" }
# Returns: {
#   result: 1589000,
#   formatted: "$1.589M",
#   breakdown: { "@cash": 1247000, "@ar": 342000 },
#   formula: "1,247,000 + 342,000"
# }

# Supported expressions:
# - number op number: "50k + 30k"
# - @ref op @ref: "@cash + @ar"
# - percentage: "20% of @revenue"
# - ratio: "@cash / @burn"
# - comparison: "@cash vs @ar"
```

**Implementation:**
1. Tokenize expression
2. Resolve @refs via fci.metric.*
3. Parse numbers (50k, $1.2M, etc.)
4. Evaluate with Decimal precision

### 2.4 FCI Scenario Engine (NEW)

**Purpose:** Project financial scenarios

```python
# Capability: fci.scenario.project
# Input: {
#   condition: "burn +20%",
#   base_metrics: { cash, burn, revenue }  # or auto-fetch
# }
# Returns: {
#   impact: {
#     runway: { before: 14.2, after: 11.4, delta: -2.8 },
#     cash_out_date: { before: "2027-03", after: "2026-08" }
#   },
#   assumptions: [...],
#   confidence: "medium"
# }

# Supported conditions:
# - "burn +20%" / "burn -10%"
# - "revenue flat"
# - "churn = 5%"
# - "hire 3 eng" (needs avg salary assumption)
# - "raise $2m"
# - "@customer:acme churns"
```

**Implementation:**
1. Parse condition into structured change
2. Fetch current metrics via fci.metric.*
3. Apply change to build projection
4. Compute runway/cash-out impact
5. Use `forecast.cashflow` for detailed projection

---

## Part 3: Workflow Primitive Mapping

### 3.1 Already Supported (Direct Mapping)

| FCI Command | Stargate Capability | Notes |
|-------------|---------------------|-------|
| `@aleq ap quick [vendor] [amount]` | `billcom.bill.create` | Direct |
| `@aleq vendor status [name]` | `vendor.search` + `bill.list` | Orchestration |
| `@aleq pay run` | `billcom.payment.bulk` | Direct |
| `@aleq inv create [customer]` | `invoice.create` (QB/Stripe) | Direct |
| `@aleq cash apply [amount]` | `payment.create` + `recurly.payment.apply` | Direct |
| `@aleq collect list` | `report.ar_aging` filtered | Computation |
| `@aleq gl post` | `journal.create` (QB/NetSuite) | Direct |
| `@aleq cash pos` | `fci.metric.cash` (new) | Uses new utility |

### 3.2 Needs New Orchestration

| FCI Command | Required | Gap |
|-------------|----------|-----|
| `@aleq ap match [PO]` | PO + Invoice + Receipt | **No PO system** - need to add or integrate |
| `@aleq credit check [customer]` | Payment history + AR aging | Orchestration logic |
| `@aleq recon dashboard` | GL + Bank + `calc.reconcile` | Orchestration logic |
| `@aleq close checklist` | Period status across systems | New utility |
| `@aleq wire [amount] to [dest]` | Bank wire APIs | `mercury.wire.create`, `chase.wire.create` exist |
| `@aleq cash cast` | `forecast.cashflow` | Exists - needs FCI wrapper |

---

## Part 4: Implementation Roadmap

### Phase 1: Core Metrics (1-2 weeks)

**New file:** `app/utilities/fci/__init__.py`

```
app/utilities/fci/
├── __init__.py          # FCIUtility class
├── metrics.py           # fci.metric.* capabilities
├── entity_resolver.py   # fci.entity.* capabilities
├── math_parser.py       # fci.parse.expression
└── scenario.py          # fci.scenario.project
```

**Capabilities to add:**
1. `fci.metric.cash` - Aggregate bank balances
2. `fci.metric.ar` - Compute AR totals from aging
3. `fci.metric.ap` - Compute AP totals from aging
4. `fci.metric.burn` - Calculate burn rate from P&L
5. `fci.metric.runway` - Cash / Burn calculation
6. `fci.metric.revenue` - Extract revenue from P&L
7. `fci.metric.expenses` - Extract expenses from P&L
8. `fci.metric.payroll` - Aggregate Gusto payroll

### Phase 2: Entity Resolution (1 week)

**Capabilities to add:**
1. `fci.entity.customer` - Cross-service customer lookup
2. `fci.entity.vendor` - Cross-service vendor lookup
3. `fci.entity.invoice` - Cross-service invoice lookup
4. `fci.entity.payment` - Cross-service payment lookup

### Phase 3: Math & Scenarios (1-2 weeks)

**Capabilities to add:**
1. `fci.parse.expression` - Math expression parser
2. `fci.scenario.project` - Scenario projection engine
3. `fci.scenario.compound` - Multi-condition scenarios

### Phase 4: Workflow Orchestration (1 week)

**Capabilities to add:**
1. `fci.workflow.credit_check` - Customer credit analysis
2. `fci.workflow.collections` - Collections worklist
3. `fci.workflow.recon_status` - Reconciliation dashboard
4. `fci.workflow.close_checklist` - Month-end checklist

---

## Part 5: Data Dependencies

### What Each FCI Primitive Needs

```
@cash
├── plaid.balance.get (all linked accounts)
├── mercury.transaction.get (balance)
├── brex.balance.get
├── chase.balance.get
├── sage_intacct.bank_accounts.balance
└── xero.bank.accounts.list
    └── Aggregate with bank.aggregate utility

@ar
├── report.ar_aging (QB)
├── OR xero.ar.aging
├── OR sage_intacct.reports.ar_aging
└── Extract: total, current, 30/60/90+ buckets

@ap
├── report.ap_aging (QB)
├── OR xero.ap.aging
├── OR sage_intacct.reports.ap_aging
├── billcom.bill.list (pending)
└── Extract: total, current, 30/60/90+ buckets

@burn
├── report.profitloss (last 3-6 months)
├── Extract: total expenses
├── Calculate: monthly average
└── Trend: month-over-month change

@runway
├── @cash (from above)
├── @burn (from above)
└── Calculate: cash / burn

@revenue
├── report.profitloss
├── Extract: income section
└── Optional: stripe.balance.get for recurring

@expenses
├── report.profitloss
├── Extract: expense section
└── Categorize by type

@payroll
├── gusto.payrolls.list
├── gusto.payroll.get (latest)
└── Summarize: total, headcount, next run
```

---

## Part 6: Existing Utilities That Help

| Utility | FCI Use Case |
|---------|--------------|
| `bank.aggregate` | `@cash` aggregation |
| `match.fuzzy` | `@customer:name`, `@vendor:name` resolution |
| `match.transactions` | Lockbox matching for `cash apply` |
| `forecast.cashflow` | `if` scenarios, `cash cast` |
| `calc.reconcile` | `recon dashboard` |
| `calc.covenant.*` | Financial health metrics |

---

## Part 7: What's NOT Needed (Already Covered)

1. **Raw data access** - 322 endpoints exist
2. **Bank reconciliation** - `calc.reconcile` exists
3. **Fuzzy matching** - `match.fuzzy` exists
4. **Cash forecasting** - `forecast.cashflow` exists
5. **Financial calculations** - `calc.*` utilities exist
6. **OCR/document parsing** - `ocr.*` exists
7. **Web search/summarization** - cognitive utilities exist

---

## Summary

| Component | Status | Effort |
|-----------|--------|--------|
| Raw data endpoints | ✅ Complete | - |
| Bank reconciliation | ✅ Complete | - |
| Fuzzy matching | ✅ Complete | - |
| Cash forecasting | ✅ Complete | - |
| **FCI Metric Engine** | ❌ Missing | 1-2 weeks |
| **FCI Entity Resolver** | ❌ Missing | 1 week |
| **FCI Math Parser** | ❌ Missing | 3-5 days |
| **FCI Scenario Engine** | ❌ Missing | 1 week |
| **Workflow Orchestration** | ❌ Missing | 1 week |

**Total estimated effort: 4-6 weeks** for complete FCI backend support

The hardest part is the **orchestration layer** that calls multiple services and computes derived metrics. The raw data is there.
