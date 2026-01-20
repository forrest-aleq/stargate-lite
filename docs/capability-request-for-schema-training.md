# Capability Schema Request for Translator Training

**From:** TAMI Training Team

**To:** Integrations Team

**Date:** 2026-01-19

**Priority:** High - Blocking model training

---

## What We're Building

We're training **Translator models** that convert semantic work units into actual API calls. Think of it as:

```

"Create a bill for Vendor ABC, $2,355.68, invoice #INV-123"

                          ↓

              Translator Model

                          ↓

{ "capability": "bill.create", "params": { ... } }

```

---

## What We Need

### 1. Complete Capability List

All capabilities Aleq can call, organized by system. Example format:

```yaml

quickbooks:

  - bill.create

  - bill.get

  - bill.list

  - bill.update

  - bill.delete

  - vendor.get

  - vendor.list

  - invoice.create

# ... etc


netsuite:

  - transaction.bill.create

  - transaction.bill.get

# ... etc

```

### 2. Schema for Each Capability

For each capability, we need:

```json

{

"capability": "bill.create",

"system": "quickbooks",

"description": "Creates a new bill (accounts payable)",

"params": {

"vendor_id": {

"type": "string",

"required": true,

"description": "QuickBooks vendor ID"

    },

"amount": {

"type": "number",

"required": true,

"description": "Total bill amount"

    },

"due_date": {

"type": "string",

"required": false,

"format": "YYYY-MM-DD",

"description": "Payment due date"

    },

"line_items": {

"type": "array",

"required": true,

"items": {

"account_id": "string",

"amount": "number",

"description": "string"

      }

    },

"memo": {

"type": "string",

"required": false

    }

  },

"example": {

"capability": "bill.create",

"params": {

"vendor_id": "VEN-1234",

"amount": 2355.68,

"due_date": "2026-02-15",

"line_items": [

        {

"account_id": "6000",

"amount": 2355.68,

"description": "Consulting services"

        }

      ]

    }

  }

}

```

### 3. System Coverage Needed

Priority order:

1.**QuickBooks Online** (primary test target)

2.**NetSuite**

3.**Xero**

4.**Sage Intacct**

---

## Ideal Deliverable

A JSON or YAML file with this structure:

```json

{

"systems": {

"quickbooks": {

"capabilities": [

        {

"name": "bill.create",

"description": "...",

"params": { ... },

"example": { ... }

        },

        {

"name": "bill.get",

"description": "...",

"params": { ... },

"example": { ... }

        }

      ]

    },

"netsuite": {

"capabilities": [ ... ]

    }

  }

}

```

---

## Why This Matters

We have **1.6M motor instances** showing what users do in these systems. But to train the Translator, we need to know:

1.**What capabilities exist** (the vocabulary)

2.**What params each takes** (the grammar)

3.**What valid output looks like** (the target)

Without this, the model learns UI actions ("clicked Enter Bills") instead of API calls (`bill.create`).

---

## Questions?

Slack: [your channel]

Or reply to this doc.

---

## Appendix: Capabilities We've Seen in Test Runs

From existing test data, these capabilities were called:

-`bill.get`

-`bill.list`

-`vendor.list`

-`chartofaccounts.get`

-`report.profitloss.detail`

-`workflow.request_information`

We need the full list + schemas for all of these.
