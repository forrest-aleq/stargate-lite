# Capability Schema Response for TAMI Training Team

**From:** Integrations Team
**To:** TAMI Training Team
**Date:** 2026-01-19
**Re:** Capability Schema Request for Translator Training

---

## Executive Summary

We have **322+ capabilities** with a **production-ready schema system** that exceeds your requirements. QuickBooks and NetSuite schemas are comprehensive and ready for export. However, we have **gaps** in two requested systems:

| System | Status | Capabilities | Schema Coverage |
|--------|--------|--------------|-----------------|
| **QuickBooks Online** | READY | 60 | Full schemas |
| **NetSuite** | READY | 21 | Full schemas |
| **Xero** | NOT INTEGRATED | 0 | Needs work |
| **Sage Intacct** | NOT INTEGRATED | 0 | Needs work |

---

## Section 1: What We're Providing

### Our Schema System

We've built an **enhanced capability schema system** (`app/schemas/`) that provides exactly what you need:

```python
# app/schemas/base.py - Our schema structure

class CapabilitySchema:
    capability_key: str      # e.g., "bill.create"
    service: str             # e.g., "quickbooks"
    category: str            # e.g., "bills"
    description: str         # Short description
    description_detailed: str  # When/why to use
    parameters: dict[str, ParameterSchema]  # Input params
    returns: dict[str, ReturnFieldSchema]   # Output fields
    errors: list[ErrorHint]  # Possible errors + recovery
    workflow: WorkflowHints  # What pairs well
    examples: list[UsageExample]  # Concrete examples
    idempotent: bool         # Safe to retry?
    has_side_effects: bool   # Modifies state?
```

### How to Export Schemas

```python
from app.schemas import SCHEMA_REGISTRY, list_schemas, get_schema

# Get all QuickBooks schemas
qb_schemas = list_schemas(service="quickbooks")

# Get specific capability
bill_create = get_schema("bill.create")

# Export to JSON for training
import json
export = {key: schema.model_dump() for key, schema in qb_schemas.items()}
with open("quickbooks_schemas.json", "w") as f:
    json.dump(export, f, indent=2)
```

---

## Section 2: QuickBooks Online (READY)

### Capability List (60 total)

```yaml
quickbooks:
  # Vendor Operations (5)
  - vendor.create
  - vendor.get
  - vendor.list
  - vendor.search
  - vendor.update

  # Bill Operations (6)
  - bill.create
  - bill.get
  - bill.list
  - bill.payment.create
  - billpayment.list

  # Journal & Query (2)
  - journal.create
  - qb.query

  # Expense & Purchase Order (2)
  - purchaseorder.create
  - expense.create

  # Chart of Accounts (3)
  - chartofaccounts.get
  - account.list
  - account.get

  # Customer Operations (8)
  - qb.customer.create / customer.create
  - qb.customer.get / customer.get
  - qb.customer.update / customer.update
  - qb.customer.list / customer.list
  - qb.customer.search / customer.search

  # Invoice Operations (6)
  - qb.invoice.create / invoice.create
  - qb.invoice.get / invoice.get
  - qb.invoice.send / invoice.send
  - qb.invoice.void / invoice.void
  - qb.invoice.list / invoice.list
  - qb.invoice.list_outstanding

  # Item Operations (3)
  - item.create
  - item.get
  - item.list

  # Payment Operations (4)
  - qb.payment.create
  - qb.payment.get
  - payment.apply_to_invoice
  - payment.list

  # Sales, Estimates, Credits (6)
  - estimate.create
  - estimate.get
  - salesreceipt.create
  - creditmemo.create
  - timeactivity.create
  - refundreceipt.create

  # Deposits & Transfers (3)
  - deposit.create
  - qb.transfer.create
  - transaction.list

  # Reports (9)
  - report.profitloss
  - report.profitloss.detail
  - report.balancesheet
  - report.cashflow
  - report.generalledger
  - report.ar_aging
  - report.ap_aging
  - report.ar_aging_detail
  - report.ap_aging_detail

  # Budget & Documentation (2)
  - budget.get
  - document.upload

  # Organization Setup (8)
  - class.list
  - department.list
  - employee.list
  - employee.get
  - term.list
  - taxcode.list
  - company.info
```

### Example Schema (bill.create)

```json
{
  "capability_key": "bill.create",
  "service": "quickbooks",
  "category": "bills",
  "description": "Create a bill in QuickBooks",
  "description_detailed": "Creates a new bill (accounts payable) in QuickBooks. A bill represents money owed to a vendor for goods or services received. You must have a valid vendor_id (use vendor.search or vendor.create first). Line items specify what was purchased and can be linked to expense accounts or items.",
  "parameters": {
    "vendor_id": {
      "type": "string",
      "required": true,
      "description": "QuickBooks vendor ID (with 'qb:' prefix)",
      "example": "qb:123"
    },
    "line_items": {
      "type": "array",
      "required": true,
      "description": "Array of line items with Amount and detail (AccountRef or ItemRef)",
      "items_type": "object",
      "example": [
        {
          "Amount": 500.00,
          "DetailType": "AccountBasedExpenseLineDetail",
          "AccountBasedExpenseLineDetail": {
            "AccountRef": {"value": "7"},
            "Description": "Office supplies"
          }
        }
      ]
    },
    "due_date": {
      "type": "string",
      "required": false,
      "description": "Payment due date in YYYY-MM-DD format",
      "example": "2025-02-15"
    },
    "txn_date": {
      "type": "string",
      "required": false,
      "description": "Transaction date in YYYY-MM-DD format (defaults to today)",
      "example": "2025-01-15"
    }
  },
  "returns": {
    "bill_id": {
      "type": "string",
      "description": "QuickBooks bill ID with 'qb:' prefix",
      "example": "qb:456"
    },
    "doc_number": {
      "type": "string",
      "description": "QuickBooks document/reference number",
      "example": "1001"
    },
    "total_amount": {
      "type": "number",
      "description": "Total bill amount",
      "example": 500.00
    },
    "due_date": {
      "type": "string",
      "description": "Payment due date",
      "example": "2025-02-15"
    },
    "status": {
      "type": "string",
      "description": "Bill status ('open' for new bills)",
      "example": "open"
    }
  },
  "errors": [
    {
      "error_code": "CREDENTIALS_MISSING",
      "description": "QuickBooks not connected for this user/org",
      "recovery_hint": "User must complete QuickBooks OAuth flow"
    },
    {
      "error_code": "VALIDATION_ERROR",
      "description": "Invalid vendor_id, missing line items, or invalid account reference",
      "recovery_hint": "Verify vendor exists with vendor.get, and account references are valid using chartofaccounts.get"
    }
  ],
  "workflow": {
    "typically_preceded_by": ["vendor.search", "vendor.create", "chartofaccounts.get"],
    "typically_followed_by": ["bill.get", "bill.payment.create"],
    "related_capabilities": ["bill.list", "bill.get", "vendor.get"]
  },
  "examples": [
    {
      "description": "Create a bill for office supplies",
      "args": {
        "vendor_id": "qb:123",
        "line_items": [
          {
            "Amount": 250.00,
            "DetailType": "AccountBasedExpenseLineDetail",
            "AccountBasedExpenseLineDetail": {
              "AccountRef": {"value": "7"},
              "Description": "Printer paper and ink"
            }
          }
        ],
        "due_date": "2025-02-01"
      },
      "expected_output": {
        "bill_id": "qb:789",
        "doc_number": "1002",
        "total_amount": 250.00,
        "due_date": "2025-02-01",
        "status": "open"
      }
    }
  ],
  "idempotent": false,
  "has_side_effects": true
}
```

---

## Section 3: NetSuite (READY)

### Capability List (21 total)

```yaml
netsuite:
  # Journal Entries (2)
  - netsuite.journal.create
  - netsuite.journal.get

  # Vendor Bills (3)
  - netsuite.vendorbill.create
  - netsuite.vendorbill.get
  - netsuite.vendorbill.list

  # Purchase Orders (1)
  - netsuite.purchaseorder.create

  # Vendors (4)
  - netsuite.vendor.get
  - netsuite.vendor.create
  - netsuite.vendor.update
  - netsuite.vendor.search

  # Query & Reference (3)
  - netsuite.query  # SuiteQL
  - netsuite.subsidiary.list
  - netsuite.account.list

  # Bank Reconciliation & GL (2)
  - netsuite.gl.transactions
  - netsuite.reconcile.bank

  # Custom Records & Payments (6)
  - netsuite.customrecord.create
  - netsuite.vendorbill.approve
  - netsuite.payment.create
  - netsuite.payment.batch
  - netsuite.vendor.upload_document
```

### Example Schema (netsuite.vendorbill.create)

```json
{
  "capability_key": "netsuite.vendorbill.create",
  "service": "netsuite",
  "category": "vendor_bills",
  "description": "Create a vendor bill in NetSuite",
  "parameters": {
    "entity": {
      "type": "string",
      "required": true,
      "description": "Vendor internal ID",
      "example": "123"
    },
    "subsidiary": {
      "type": "string",
      "required": true,
      "description": "Subsidiary internal ID",
      "example": "1"
    },
    "trandate": {
      "type": "string",
      "required": false,
      "description": "Transaction date (MM/DD/YYYY)",
      "example": "01/15/2025"
    },
    "duedate": {
      "type": "string",
      "required": false,
      "description": "Payment due date (MM/DD/YYYY)",
      "example": "02/15/2025"
    },
    "tranid": {
      "type": "string",
      "required": false,
      "description": "Vendor invoice/reference number",
      "example": "INV-2025-001"
    },
    "item": {
      "type": "array",
      "required": true,
      "description": "Line items with item, quantity, rate",
      "items_type": "object"
    },
    "expense": {
      "type": "array",
      "required": false,
      "description": "Expense lines with account, amount, memo",
      "items_type": "object"
    }
  },
  "returns": {
    "internalid": {
      "type": "string",
      "description": "NetSuite internal ID of created bill"
    },
    "tranid": {
      "type": "string",
      "description": "Transaction ID/reference number"
    }
  },
  "workflow": {
    "typically_preceded_by": ["netsuite.vendor.search", "netsuite.account.list"],
    "typically_followed_by": ["netsuite.vendorbill.approve", "netsuite.payment.create"]
  }
}
```

---

## Section 4: GAP ANALYSIS - Missing Systems

### Xero (NOT INTEGRATED)

**Status:** No connector exists. Needs full integration.

**Estimated Work:**
- OAuth 2.0 integration (PKCE flow)
- Connector implementation (~40 capabilities)
- Schema definitions

**Recommended Capabilities for Xero:**
```yaml
xero:
  # Contacts (like vendors/customers)
  - xero.contact.create
  - xero.contact.get
  - xero.contact.list
  - xero.contact.update

  # Invoices (AR)
  - xero.invoice.create
  - xero.invoice.get
  - xero.invoice.list
  - xero.invoice.send
  - xero.invoice.void

  # Bills (AP)
  - xero.bill.create
  - xero.bill.get
  - xero.bill.list
  - xero.bill.payment.create

  # Payments
  - xero.payment.create
  - xero.payment.get
  - xero.payment.list

  # Bank Transactions
  - xero.banktransaction.create
  - xero.banktransaction.list
  - xero.bankreconciliation.create

  # Accounts & Journals
  - xero.account.list
  - xero.journal.create
  - xero.journal.list

  # Reports
  - xero.report.profitloss
  - xero.report.balancesheet
  - xero.report.trialbalance
  - xero.report.agedpayables
  - xero.report.agedreceivables
```

### Sage Intacct (NOT INTEGRATED)

**Status:** No connector exists. Needs full integration.

**Estimated Work:**
- Web Services API integration (XML/SOAP-based)
- Connector implementation (~50 capabilities)
- Schema definitions

**Recommended Capabilities for Sage Intacct:**
```yaml
sage_intacct:
  # Vendors
  - intacct.vendor.create
  - intacct.vendor.get
  - intacct.vendor.list
  - intacct.vendor.update

  # Bills (AP)
  - intacct.apbill.create
  - intacct.apbill.get
  - intacct.apbill.list
  - intacct.apbill.reverse

  # Payments
  - intacct.appayment.create
  - intacct.appayment.list

  # Invoices (AR)
  - intacct.arinvoice.create
  - intacct.arinvoice.get
  - intacct.arinvoice.list

  # Journal Entries
  - intacct.glentry.create
  - intacct.glentry.get
  - intacct.glentry.list

  # Accounts
  - intacct.glaccount.list
  - intacct.glaccount.get

  # Dimensions (Classes, Departments, Locations)
  - intacct.class.list
  - intacct.department.list
  - intacct.location.list

  # Reports
  - intacct.report.trialbalance
  - intacct.report.financials

  # Cash Management
  - intacct.cashreceipt.create
  - intacct.bankreconciliation.create
```

---

## Section 5: Recommended Action Plan

### Phase 1: Immediate (This Week)
1. **Export existing schemas** - We'll provide JSON/YAML files for QuickBooks and NetSuite
2. **Schema validation** - Run through test cases to ensure accuracy

### Phase 2: Xero Integration (Priority 1)
1. OAuth 2.0 connector setup
2. Core capabilities (contacts, invoices, bills, payments)
3. Reports and bank reconciliation
4. Schema definitions

### Phase 3: Sage Intacct Integration (Priority 2)
1. Web Services API connector
2. Core AP/AR capabilities
3. GL and journal entries
4. Dimension support (multi-entity)

---

## Section 6: Export Command

Run this to generate the training data:

```bash
cd /Users/forrest/Documents/2026/stargate-lite
source venv/bin/activate
python -c "
import json
from app.schemas import SCHEMA_REGISTRY, list_schemas

# Export format matching your request
output = {'systems': {}}

for service in ['quickbooks', 'netsuite', 'stripe', 'plaid']:
    schemas = list_schemas(service=service)
    if schemas:
        output['systems'][service] = {
            'capabilities': [
                {
                    'name': schema.capability_key,
                    'description': schema.description,
                    'description_detailed': schema.description_detailed,
                    'params': {
                        k: {
                            'type': v.type,
                            'required': v.required,
                            'description': v.description,
                            'default': v.default,
                            'example': v.example,
                            'enum': v.enum,
                        }
                        for k, v in schema.parameters.items()
                    },
                    'returns': {
                        k: {
                            'type': v.type,
                            'description': v.description,
                            'example': v.example,
                        }
                        for k, v in schema.returns.items()
                    },
                    'examples': [
                        {
                            'description': ex.description,
                            'args': ex.args,
                            'expected_output': ex.expected_output,
                        }
                        for ex in schema.examples
                    ],
                    'workflow': {
                        'typically_preceded_by': schema.workflow.typically_preceded_by if schema.workflow else [],
                        'typically_followed_by': schema.workflow.typically_followed_by if schema.workflow else [],
                        'related_capabilities': schema.workflow.related_capabilities if schema.workflow else [],
                    } if schema.workflow else None,
                    'idempotent': schema.idempotent,
                    'has_side_effects': schema.has_side_effects,
                }
                for schema in schemas.values()
            ]
        }

with open('docs/capability-schemas-for-training.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f'Exported {sum(len(s[\"capabilities\"]) for s in output[\"systems\"].values())} capabilities')
"
```

---

## Section 7: Questions for TAMI Team

1. **Priority:** Should we prioritize Xero or Sage Intacct first? Xero has simpler REST API.

2. **Training data format:** Is the JSON structure above sufficient, or do you need additional fields?

3. **Coverage depth:** For Xero/Intacct, do you need full coverage or just core AP/AR/GL?

4. **Timeline:** When do you need Xero/Intacct schemas by?

---

## Contact

Slack: #integrations-team
Or reply to this doc.

---

**Attachments:**
- `docs/capability-schemas-for-training.json` (generated via export command above)
- Schema files: `app/schemas/quickbooks/`, `app/schemas/netsuite/`
