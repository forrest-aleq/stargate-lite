# STARGATE LITE - Capability Schema Response for TAMI Training

**Generated:** 2026-01-20 22:16:56
**Total Capabilities:** 581 with full schemas
**API Endpoint:** `GET /api/v1/schemas` or `GET /api/v1/schemas?service=<name>`

---

## Coverage Summary

| System | Tier | Your Instances | Our Capabilities | Status |
|--------|------|----------------|------------------|--------|
| QuickBooks | 1 | 68,800 | 71 | ✅ Full |
| Slack | 1 | 85,580 | 14 | ✅ Full |
| NetSuite | 1 | 44,618 | 20 | ✅ Full |
| Sage Intacct | 2 | 24,350 | 25 | ✅ Full |
| Microsoft (Excel/Outlook) | 1-3 | 442,862 | 16 | ✅ Partial |
| Google (Sheets/Drive) | 4-5 | 2,269 | 23 | ✅ Full |
| Stripe | 5 | 1,232 | 224 | ✅ Complete |
| Bill.com | 5 | 1,819 | 9 | ✅ Full |
| DocuSign | 5 | 1,593 | 11 | ✅ Full |
| Shopify | 5 | 1,446 | 13 | ✅ Full |
| Square | 5 | 1,691 | 19 | ✅ Full |
| Airtable | 5 | 1,161 | 13 | ✅ Full |
| Gusto | 6 | 723 | 14 | ✅ Full |
| Monday.com | 6 | 687 | 13 | ✅ Full |
| Brex | 7 | 241 | 8 | ✅ Full |
| Mercury | 7 | 141 | 6 | ✅ Full |
| Notion | 7 | 476 | 10 | ✅ Full |
| Asana | 7 | 174 | 12 | ✅ Full |
| HubSpot | 7 | 43 | 18 | ✅ Full |
| Xero | 7 | 182 | 61 | ✅ Complete |
| Plaid (Banking) | - | - | 11 | ✅ Full |

**Not Yet Implemented:** SAP, Oracle, ADP, Tyler Munis, Yardi, Workday, Epic, Salesforce, Concur

---

## QUICKBOOKS (71 capabilities)

### `account.get`

**Description:** Get single account details with balance

> Retrieves detailed information about a specific account including current balance.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Account ID with 'qb:' prefix |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `account_id` | string | Account ID |
| `name` | string | Account name |
| `type` | string | Account type |
| `sub_type` | string | Account sub-type |
| `number` | string | Account number |
| `balance` | number | Current balance |
| `active` | boolean | Is active |

---

### `account.list`

**Description:** List all accounts (chart of accounts)

> Alias for chartofaccounts.get - retrieves all accounts.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_type` | string |  | Filter by account type |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | List of account objects |
| `count` | integer | Number of accounts |

---

### `bill.create`

**Description:** Create a bill in QuickBooks

> Creates a new bill (accounts payable) in QuickBooks. A bill represents money owed to a vendor for goods or services received. You must have a valid vendor_id (use vendor.search or vendor.create first). Line items specify what was purchased and can be linked to expense accounts or items.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | QuickBooks vendor ID (with 'qb:' prefix) |
| `line_items` | array | ✓ | Array of line items with Amount and detail (AccountRef or It |
| `due_date` | string |  | Payment due date in YYYY-MM-DD format |
| `txn_date` | string |  | Transaction date in YYYY-MM-DD format (defaults to today) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bill_id` | string | QuickBooks bill ID with 'qb:' prefix |
| `doc_number` | string | QuickBooks document/reference number |
| `total_amount` | number | Total bill amount |
| `due_date` | string | Payment due date |
| `status` | string | Bill status ('open' for new bills) |

**Example:**
```json
{
  "capability": "bill.create",
  "params": {
    "vendor_id": "qb:123",
    "line_items": [
      {
        "Amount": 250.0,
        "DetailType": "AccountBasedExpenseLineDetail",
        "AccountBasedExpenseLineDetail": {
          "AccountRef": {
            "value": "7"
          },
          "Description": "Printer paper and ink"
        }
      }
    ],
    "due_date": "2025-02-01"
  }
}
```

---

### `bill.get`

**Description:** Get bill details including line items

> Retrieves detailed information about a specific bill including its line items, current balance, and payment status. Use this to check if a bill has been partially or fully paid.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bill_id` | string | ✓ | QuickBooks bill ID (with 'qb:' prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bill_id` | string | QuickBooks bill ID with 'qb:' prefix |
| `doc_number` | string | QuickBooks document/reference number |
| `total_amount` | number | Original total bill amount |
| `balance` | number | Remaining unpaid balance (0 if fully paid) |
| `due_date` | string | Payment due date |
| `vendor_id` | string | Vendor ID this bill is from |

---

### `bill.list`

**Description:** List bills with optional vendor/date filters

> Returns a list of bills from QuickBooks with optional filtering. Use this to find bills for a specific vendor or to get a list of unpaid bills. Results are paginated.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string |  | Filter bills by vendor ID (with 'qb:' prefix) |
| `unpaid_only` | boolean |  | If true, only return bills with balance > 0 |
| `limit` | integer |  | Maximum number of bills to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bills` | array | List of bill objects |
| `count` | integer | Number of bills returned |

**Example:**
```json
{
  "capability": "bill.list",
  "params": {
    "vendor_id": "qb:123",
    "unpaid_only": true,
    "limit": 25
  }
}
```

---

### `bill.payment.create`

**Description:** Create a bill payment in QuickBooks

> Records a payment made to a vendor for one or more bills. This creates a BillPayment transaction in QuickBooks and reduces the balance on the linked bills. You can pay multiple bills at once by providing multiple bill_ids.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | QuickBooks vendor ID receiving the payment (with 'qb:' prefi |
| `amount` | number | ✓ | Total payment amount |
| `bill_ids` | array |  | Array of bill IDs to apply payment to (with 'qb:' prefix) |
| `payment_type` | string |  | Payment method type |
| `check_num` | string |  | Check number if payment_type is Check |
| `txn_date` | string |  | Payment date in YYYY-MM-DD format (defaults to today) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | QuickBooks bill payment ID with 'qb:' prefix |
| `amount` | number | Payment amount |
| `pay_type` | string | Payment type used |
| `txn_date` | string | Transaction date |

**Example:**
```json
{
  "capability": "bill.payment.create",
  "params": {
    "vendor_id": "qb:123",
    "amount": 500.0,
    "bill_ids": [
      "qb:456"
    ],
    "payment_type": "Check",
    "check_num": "5001"
  }
}
```

---

### `billpayment.list`

**Description:** List vendor bill payments with optional filters

> Returns a list of bill payments (money paid to vendors) from QuickBooks. Can be filtered by vendor to see payment history for a specific supplier.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string |  | Filter payments by vendor ID (with 'qb:' prefix) |
| `limit` | integer |  | Maximum number of payments to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payments` | array | List of bill payment objects |
| `count` | integer | Number of payments returned |

**Example:**
```json
{
  "capability": "billpayment.list",
  "params": {
    "vendor_id": "qb:123",
    "limit": 10
  }
}
```

---

### `budget.get`

**Description:** Get budget data for variance analysis (actual vs budget comparison)

> Retrieves budget data from QuickBooks for comparison against actual performance. Use for variance analysis and financial planning.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `fiscal_year` | string |  | Fiscal year to retrieve budget for |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `budgets` | array | List of budget objects |
| `count` | integer | Number of budgets |

---

### `chartofaccounts.get`

**Description:** Get chart of accounts from QuickBooks

> Retrieves the full chart of accounts with optional filtering by account type. Use to get account IDs needed for journal entries, bills, and other transactions.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_type` | string |  | Filter by account type |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | List of account objects |
| `count` | integer | Number of accounts |

---

### `class.list`

**Description:** List classes for class tracking/filtering

> Retrieves all classes defined in QuickBooks. Classes are used for categorization and tracking (e.g., by project, product line, or business segment).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `active_only` | boolean |  | Only return active classes |
| `limit` | integer |  | Maximum results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `classes` | array | List of class objects |
| `count` | integer | Number of classes |

---

### `company.info`

**Description:** Get company information

> Retrieves company profile information including name, address, contact details, and fiscal year settings.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `company_name` | string | Company name |
| `legal_name` | string | Legal business name |
| `company_addr` | object | Company address |
| `email` | string | Company email |
| `phone` | string | Company phone |
| `fiscal_year_start` | string | Fiscal year start month |
| `country` | string | Country code |

---

### `creditmemo.create`

**Description:** Create a credit memo in QuickBooks

> Creates a credit memo to reduce a customer's balance. Can be applied to outstanding invoices or remain as available credit.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `line_items` | array | ✓ | Credit line items |
| `txn_date` | string |  | Date |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `credit_memo_id` | string | Credit memo ID |
| `doc_number` | string | Number |
| `total_amount` | number | Credit amount |
| `customer_id` | string | Customer |
| `balance` | number | Unapplied balance |

---

### `customer.create`

**Description:** Create a customer in QuickBooks (MARS alias)

> Creates a new customer record in QuickBooks Online. Customers are individuals or businesses who purchase goods or services from you. The customer_id returned can be used in invoice.create and payment.create. Customer names should be unique.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_name` | string | ✓ | Display name for the customer (should be unique) |
| `email` | string |  | Primary contact email address |
| `phone` | string |  | Primary phone number |
| `company_name` | string |  | Company/business name (if different from display name) |
| `billing_address` | object |  | Billing address with Line1, City, CountrySubDivisionCode, Po |
| `shipping_address` | object |  | Shipping address (same structure as billing_address) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | string | QuickBooks customer ID with 'qb:' prefix |
| `display_name` | string | Customer display name as stored |
| `email` | string | Email address if provided |
| `balance` | number | Current balance (0 for new customers) |
| `created_at` | string | ISO timestamp when customer was created |

---

### `customer.get`

**Description:** Get customer details from QuickBooks (MARS alias)

> Retrieves detailed information about a specific customer including contact info, current balance, and status. Use this to verify customer details before creating invoices or to check outstanding balances.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | QuickBooks customer ID (with 'qb:' prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | string | Customer ID |
| `display_name` | string | Display name |
| `email` | string | Email address |
| `phone` | string | Phone number |
| `balance` | number | Current outstanding balance |
| `status` | string | 'active' or 'inactive' |

---

### `customer.list`

**Description:** List customers from QuickBooks (MARS alias)

> Returns a paginated list of customers. Use for bulk retrieval or browsing. For finding a specific customer by name, use qb.customer.search instead.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `active_only` | boolean |  | Only return active customers |
| `limit` | integer |  | Maximum results (1-1000) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customers` | array | List of customer objects |
| `count` | integer | Number returned |

---

### `customer.update`

**Description:** Update a customer in QuickBooks (MARS alias)

> Updates an existing customer's information. Only provided fields are updated; omitted fields retain current values. Automatically handles SyncToken.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID to update |
| `customer_name` | string |  | New display name |
| `email` | string |  | New email address |
| `phone` | string |  | New phone number |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | string | Customer ID |
| `display_name` | string | Updated name |
| `updated` | boolean | True if successful |

---

### `department.list`

**Description:** List departments/locations

> Retrieves all departments (locations) defined in QuickBooks. Departments are used for location tracking and reporting.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `active_only` | boolean |  | Only return active departments |
| `limit` | integer |  | Maximum results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `departments` | array | List of department objects |
| `count` | integer | Number of departments |

---

### `deposit.create`

**Description:** Create a bank deposit

> Creates a deposit to record money received into a bank account. Can include multiple line items from different sources.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deposit_account_id` | string | ✓ | Bank account ID to deposit into |
| `line_items` | array | ✓ | Deposit line items with amounts and sources |
| `txn_date` | string |  | Deposit date |
| `memo` | string |  | Private note |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `deposit_id` | string | Deposit ID |
| `total_amount` | number | Total deposited |
| `txn_date` | string | Date |

---

### `document.upload`

**Description:** Upload document (W-9, invoice, receipt) and attach to entity

> Uploads a document file and attaches it to a QuickBooks entity like a vendor, customer, bill, or invoice. Useful for storing W-9s, receipts, and source documents.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_path` | string | ✓ | Local path to the file to upload |
| `entity_type` | string | ✓ | Type of entity to attach to |
| `entity_id` | string | ✓ | ID of the entity (with 'qb:' prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `attachment_id` | string | Attachment ID |
| `file_name` | string | Uploaded file name |
| `size` | integer | File size in bytes |
| `entity_type` | string | Entity type |
| `entity_id` | string | Entity ID |

---

### `employee.get`

**Description:** Get employee details

> Retrieves detailed information about a specific employee.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `employee_id` | string | ✓ | Employee ID with 'qb:' prefix |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `employee_id` | string | Employee ID |
| `display_name` | string | Display name |
| `given_name` | string | First name |
| `family_name` | string | Last name |
| `email` | string | Email address |
| `phone` | string | Phone number |
| `hired_date` | string | Hire date |
| `active` | boolean | Is active |

---

### `employee.list`

**Description:** List employees

> Retrieves all employees defined in QuickBooks. Employees can be assigned to time activities and used for tracking billable work.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `active_only` | boolean |  | Only return active employees |
| `limit` | integer |  | Maximum results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `employees` | array | List of employee objects |
| `count` | integer | Number of employees |

---

### `estimate.create`

**Description:** Create an estimate in QuickBooks

> Creates a quote/estimate for a customer. Estimates can be converted to invoices and are useful for quoting before work begins.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `line_items` | array | ✓ | Line items |
| `txn_date` | string |  | Estimate date |
| `expiration_date` | string |  | Quote expiration date |
| `customer_memo` | string |  | Message |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `estimate_id` | string | Estimate ID |
| `doc_number` | string | Estimate number |
| `total_amount` | number | Total |
| `customer_id` | string | Customer |
| `status` | string | Status |

---

### `estimate.get`

**Description:** Get estimate details from QuickBooks

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `estimate_id` | string | ✓ | Estimate ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `estimate_id` | string | Estimate ID |
| `doc_number` | string | Number |
| `customer_id` | string | Customer |
| `total_amount` | number | Total |
| `expiration_date` | string | Expires |
| `status` | string | Status |

---

### `expense.create`

**Description:** Create an expense in QuickBooks

> Creates a purchase/expense transaction. Unlike bills, expenses are paid immediately (cash, credit card, etc.) rather than on account.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `line_items` | array | ✓ | Expense line items |
| `payment_type` | string |  | Payment type used |
| `txn_date` | string |  | Expense date |
| `vendor_id` | string |  | Vendor (optional) |
| `account_ref` | string |  | Payment account ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `expense_id` | string | Expense ID |
| `total_amount` | number | Total |
| `payment_type` | string | Payment type |

---

### `invoice.create`

**Description:** Create an invoice in QuickBooks (MARS alias)

> Creates a new invoice (accounts receivable) for a customer. An invoice represents money owed to you for goods or services. Requires a valid customer_id and line items. The invoice can be sent via email using invoice.send after creation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | QuickBooks customer ID (with 'qb:' prefix) |
| `line_items` | array | ✓ | Array of line items with Amount, Description, and detail typ |
| `due_date` | string |  | Payment due date (YYYY-MM-DD) |
| `txn_date` | string |  | Invoice date (defaults to today) |
| `customer_memo` | string |  | Message displayed on invoice to customer |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | QuickBooks invoice ID with 'qb:' prefix |
| `doc_number` | string | Invoice number |
| `total_amount` | number | Total invoice amount |
| `balance` | number | Outstanding balance |
| `status` | string | Invoice status |

---

### `invoice.get`

**Description:** Get invoice details (MARS alias)

> Retrieves complete invoice details including line items, balance, and email status. Use to check payment status or get invoice details before sending.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID with 'qb:' prefix |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Invoice ID |
| `doc_number` | string | Invoice number |
| `customer_id` | string | Customer ID |
| `total_amount` | number | Total amount |
| `balance` | number | Outstanding balance |
| `due_date` | string | Due date |
| `email_status` | string | Email delivery status |

---

### `invoice.list`

**Description:** List invoices (MARS alias)

> Returns a list of invoices with optional filtering by customer or payment status. For outstanding invoices specifically, use qb.invoice.list_outstanding.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string |  | Filter by customer ID |
| `unpaid_only` | boolean |  | Only return invoices with balance > 0 |
| `limit` | integer |  | Maximum results |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoices` | array | List of invoices |
| `count` | integer | Number returned |

---

### `invoice.send`

**Description:** Send invoice via email (MARS alias)

> Sends an invoice to the customer via email using QuickBooks' email service. The email will be sent from your QuickBooks account and include a link for online payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to send |
| `email` | string |  | Override email address (uses customer's email if not provide |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Invoice ID |
| `email_sent` | boolean | True if sent |
| `sent_to` | string | Recipient email |
| `email_status` | string | Delivery status |

---

### `invoice.void`

**Description:** Void an invoice (MARS alias)

> Voids an existing invoice, setting its balance to zero. Use this instead of deleting to maintain audit trail. Cannot void invoices with payments applied.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to void |
| `void_reason` | string |  | Reason for voiding (stored in private note) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Invoice ID |
| `voided` | boolean | True if voided |
| `balance` | number | Balance (should be 0) |

---

### `item.create`

**Description:** Create an item/product in QuickBooks

> Creates a new item (product or service) that can be used on invoices and sales. Items can be Services, Inventory, or NonInventory types.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_name` | string | ✓ | Item name (must be unique) |
| `item_type` | string |  | Type of item |
| `unit_price` | number |  | Default unit price |
| `description` | string |  | Item description |
| `income_account_id` | string |  | Income account for sales |
| `expense_account_id` | string |  | Expense account for purchases |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `item_id` | string | Item ID |
| `name` | string | Item name |
| `type` | string | Item type |
| `unit_price` | number | Unit price |

---

### `item.get`

**Description:** Get item details from QuickBooks

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_id` | string | ✓ | Item ID with 'qb:' prefix |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `item_id` | string | Item ID |
| `name` | string | Item name |
| `type` | string | Item type |
| `unit_price` | number | Unit price |
| `description` | string | Description |
| `active` | boolean | Is active |

---

### `item.list`

**Description:** List items from QuickBooks

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_type` | string |  | Filter by item type |
| `active_only` | boolean |  | Only return active items |
| `limit` | integer |  | Maximum results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `items` | array | List of items |
| `count` | integer | Number returned |

---

### `journal.create`

**Description:** Create a journal entry in QuickBooks

> Creates a manual journal entry with debit and credit lines. Journal entries must balance (total debits = total credits). Use for adjustments, corrections, or transactions not captured by other transaction types.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `lines` | array | ✓ | Journal lines with PostingType, Amount, and AccountRef |
| `txn_date` | string |  | Journal entry date (YYYY-MM-DD) |
| `memo` | string |  | Private memo/description |
| `doc_number` | string |  | Reference number |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `journal_entry_id` | string | Journal entry ID |
| `doc_number` | string | Reference number |
| `txn_date` | string | Entry date |
| `total_amount` | number | Total amount |
| `memo` | string | Memo |

**Example:**
```json
{
  "capability": "journal.create",
  "params": {
    "lines": [
      {
        "DetailType": "JournalEntryLineDetail",
        "Amount": 500,
        "JournalEntryLineDetail": {
          "PostingType": "Debit",
          "AccountRef": {
            "value": "66"
          },
          "Description": "Accrued utilities expense"
        }
      },
      {
        "DetailType": "JournalEntryLineDetail",
        "Amount": 500,
        "JournalEntryLineDetail": {
          "PostingType": "Credit",
          "AccountRef": {
            "value": "92"
          },
          "Description": "Accrued liabilities"
        }
      }
    ],
    "memo": "Month-end accrual for utilities"
  }
}
```

---

### `payment.apply_to_invoice`

**Description:** Apply payment to specific invoice(s) with multi-invoice allocation

> Creates a payment and applies it to one or more invoices with specific amounts. Enables complex payment allocation scenarios where a single payment covers multiple invoices.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `invoice_allocations` | array | ✓ | Array of {invoice_id, amount} for each invoice |
| `payment_method` | string |  | Payment method |
| `reference` | string |  | Reference number or note |
| `txn_date` | string |  | Payment date |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | Payment ID |
| `customer_id` | string | Customer |
| `total_amount` | number | Total paid |
| `invoice_allocations` | array | How payment was allocated |
| `status` | string | 'applied' |

---

### `payment.list`

**Description:** List customer payments with optional filters

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string |  | Filter by customer |
| `limit` | integer |  | Maximum results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payments` | array | List of payments |
| `count` | integer | Number returned |

---

### `purchaseorder.create`

**Description:** Create a purchase order in QuickBooks

> Creates a purchase order for a vendor. Purchase orders are used to order goods before receiving them and can be converted to bills upon receipt.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Vendor ID |
| `line_items` | array | ✓ | Items being ordered |
| `txn_date` | string |  | Order date |
| `ship_address` | object |  | Shipping address |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `purchase_order_id` | string | PO ID |
| `doc_number` | string | PO number |
| `total_amount` | number | Total |
| `vendor_id` | string | Vendor |

---

### `qb.customer.create`

**Description:** Create a customer in QuickBooks

> Creates a new customer record in QuickBooks Online. Customers are individuals or businesses who purchase goods or services from you. The customer_id returned can be used in invoice.create and payment.create. Customer names should be unique.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_name` | string | ✓ | Display name for the customer (should be unique) |
| `email` | string |  | Primary contact email address |
| `phone` | string |  | Primary phone number |
| `company_name` | string |  | Company/business name (if different from display name) |
| `billing_address` | object |  | Billing address with Line1, City, CountrySubDivisionCode, Po |
| `shipping_address` | object |  | Shipping address (same structure as billing_address) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | string | QuickBooks customer ID with 'qb:' prefix |
| `display_name` | string | Customer display name as stored |
| `email` | string | Email address if provided |
| `balance` | number | Current balance (0 for new customers) |
| `created_at` | string | ISO timestamp when customer was created |

**Example:**
```json
{
  "capability": "qb.customer.create",
  "params": {
    "customer_name": "Tech Startup LLC",
    "email": "accounts@techstartup.io",
    "phone": "(415) 555-0100"
  }
}
```

---

### `qb.customer.get`

**Description:** Get customer details from QuickBooks

> Retrieves detailed information about a specific customer including contact info, current balance, and status. Use this to verify customer details before creating invoices or to check outstanding balances.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | QuickBooks customer ID (with 'qb:' prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | string | Customer ID |
| `display_name` | string | Display name |
| `email` | string | Email address |
| `phone` | string | Phone number |
| `balance` | number | Current outstanding balance |
| `status` | string | 'active' or 'inactive' |

---

### `qb.customer.list`

**Description:** List customers from QuickBooks

> Returns a paginated list of customers. Use for bulk retrieval or browsing. For finding a specific customer by name, use qb.customer.search instead.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `active_only` | boolean |  | Only return active customers |
| `limit` | integer |  | Maximum results (1-1000) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customers` | array | List of customer objects |
| `count` | integer | Number returned |

---

### `qb.customer.search`

**Description:** Search customers by name with fuzzy matching

> Searches for customers using LIKE matching on display name. Use before qb.customer.create to check for duplicates or to find customers by partial name.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `search_term` | string | ✓ | Search term to match against customer names |
| `max_results` | integer |  | Maximum results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customers` | array | Matching customers |
| `count` | integer | Number of matches |
| `search_term` | string | Term used |

---

### `qb.customer.update`

**Description:** Update a customer in QuickBooks

> Updates an existing customer's information. Only provided fields are updated; omitted fields retain current values. Automatically handles SyncToken.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID to update |
| `customer_name` | string |  | New display name |
| `email` | string |  | New email address |
| `phone` | string |  | New phone number |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | string | Customer ID |
| `display_name` | string | Updated name |
| `updated` | boolean | True if successful |

---

### `qb.invoice.create`

**Description:** Create an invoice in QuickBooks

> Creates a new invoice (accounts receivable) for a customer. An invoice represents money owed to you for goods or services. Requires a valid customer_id and line items. The invoice can be sent via email using invoice.send after creation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | QuickBooks customer ID (with 'qb:' prefix) |
| `line_items` | array | ✓ | Array of line items with Amount, Description, and detail typ |
| `due_date` | string |  | Payment due date (YYYY-MM-DD) |
| `txn_date` | string |  | Invoice date (defaults to today) |
| `customer_memo` | string |  | Message displayed on invoice to customer |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | QuickBooks invoice ID with 'qb:' prefix |
| `doc_number` | string | Invoice number |
| `total_amount` | number | Total invoice amount |
| `balance` | number | Outstanding balance |
| `status` | string | Invoice status |

**Example:**
```json
{
  "capability": "qb.invoice.create",
  "params": {
    "customer_id": "qb:123",
    "line_items": [
      {
        "Amount": 500.0,
        "DetailType": "SalesItemLineDetail",
        "Description": "Consulting services - January 2026",
        "SalesItemLineDetail": {
          "ItemRef": {
            "value": "1"
          },
          "Qty": 5,
          "UnitPrice": 100
        }
      }
    ],
    "due_date": "2026-02-15"
  }
}
```

---

### `qb.invoice.get`

**Description:** Get invoice details from QuickBooks

> Retrieves complete invoice details including line items, balance, and email status. Use to check payment status or get invoice details before sending.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID with 'qb:' prefix |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Invoice ID |
| `doc_number` | string | Invoice number |
| `customer_id` | string | Customer ID |
| `total_amount` | number | Total amount |
| `balance` | number | Outstanding balance |
| `due_date` | string | Due date |
| `email_status` | string | Email delivery status |

---

### `qb.invoice.list`

**Description:** List invoices from QuickBooks

> Returns a list of invoices with optional filtering by customer or payment status. For outstanding invoices specifically, use qb.invoice.list_outstanding.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string |  | Filter by customer ID |
| `unpaid_only` | boolean |  | Only return invoices with balance > 0 |
| `limit` | integer |  | Maximum results |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoices` | array | List of invoices |
| `count` | integer | Number returned |

---

### `qb.invoice.list_outstanding`

**Description:** List outstanding invoices (Balance > 0) - CRITICAL for payment allocation

> Returns only invoices with outstanding balances. Essential for MARS payment allocation workflows - identifies which invoices need payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string |  | Filter by customer ID |
| `limit` | integer |  | Maximum results |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoices` | array | Outstanding invoices |
| `total_outstanding` | number | Sum of all outstanding balances |
| `count` | integer | Number of invoices |

---

### `qb.invoice.send`

**Description:** Send invoice via email through QuickBooks

> Sends an invoice to the customer via email using QuickBooks' email service. The email will be sent from your QuickBooks account and include a link for online payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to send |
| `email` | string |  | Override email address (uses customer's email if not provide |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Invoice ID |
| `email_sent` | boolean | True if sent |
| `sent_to` | string | Recipient email |
| `email_status` | string | Delivery status |

---

### `qb.invoice.void`

**Description:** Void an invoice in QuickBooks

> Voids an existing invoice, setting its balance to zero. Use this instead of deleting to maintain audit trail. Cannot void invoices with payments applied.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to void |
| `void_reason` | string |  | Reason for voiding (stored in private note) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Invoice ID |
| `voided` | boolean | True if voided |
| `balance` | number | Balance (should be 0) |

---

### `qb.payment.create`

**Description:** Create a payment (customer payment) in QuickBooks

> Records a payment received from a customer. Can be applied to specific invoices using invoice_ids, or recorded as unapplied payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `amount` | number | ✓ | Payment amount |
| `invoice_ids` | array |  | Invoice IDs to apply payment to |
| `txn_date` | string |  | Payment date (YYYY-MM-DD) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | Payment ID |
| `amount` | number | Amount |
| `customer_id` | string | Customer ID |
| `txn_date` | string | Transaction date |

---

### `qb.payment.get`

**Description:** Get payment details from QuickBooks

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_id` | string | ✓ | Payment ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | Payment ID |
| `amount` | number | Amount |
| `customer_id` | string | Customer ID |
| `txn_date` | string | Date |

---

### `qb.query`

**Description:** Query QuickBooks entities using SQL-like syntax

> Execute SQL-like queries against QuickBooks entities. Supports SELECT with WHERE, ORDERBY, STARTPOSITION, and MAXRESULTS. Useful for complex queries not covered by other endpoints.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ | SQL-like query string |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `results` | object | QueryResponse object with entity data |
| `count` | integer | Number of results |

---

### `qb.transfer.create`

**Description:** Create account-to-account transfer

> Creates a transfer between two accounts (typically bank accounts). Records money moving from one account to another.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `from_account_id` | string | ✓ | Source account ID |
| `to_account_id` | string | ✓ | Destination account ID |
| `amount` | number | ✓ | Transfer amount |
| `txn_date` | string |  | Transfer date |
| `memo` | string |  | Private note |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `transfer_id` | string | Transfer ID |
| `amount` | number | Amount transferred |
| `from_account` | string | Source account name |
| `to_account` | string | Destination account name |
| `txn_date` | string | Date |

---

### `refundreceipt.create`

**Description:** Create a refund receipt

> Creates a refund receipt to record money returned to a customer. Typically used after a sales receipt for returns.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `line_items` | array |  | Items refunded |
| `txn_date` | string |  | Refund date |
| `deposit_account_id` | string |  | Account refund comes from |
| `payment_method_id` | string |  | Payment method reference ID |
| `memo` | string |  | Private note |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `refund_receipt_id` | string | Refund ID |
| `customer_id` | string | Customer |
| `total_amount` | number | Refund amount |
| `txn_date` | string | Date |

---

### `report.ap_aging`

**Description:** Get AP Aging Summary report

> Generates an Accounts Payable Aging Summary showing vendor balances grouped by aging buckets. Helps prioritize vendor payments.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | AP aging summary by vendor and bucket |

---

### `report.ap_aging_detail`

**Description:** Get detailed AP Aging with individual bills

> Generates a detailed Accounts Payable Aging report showing each individual bill and its age. Useful for payment prioritization.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | Detailed AP aging with bill-level detail |

---

### `report.ar_aging`

**Description:** Get AR Aging Summary report

> Generates an Accounts Receivable Aging Summary showing customer balances grouped by aging buckets (Current, 1-30, 31-60, 61-90, 90+ days).

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | AR aging summary by customer and bucket |

---

### `report.ar_aging_detail`

**Description:** Get detailed AR Aging with individual invoices

> Generates a detailed Accounts Receivable Aging report showing each individual invoice and its age. More granular than summary.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | Detailed AR aging with invoice-level detail |

---

### `report.balancesheet`

**Description:** Get Balance Sheet report from QuickBooks

> Generates a Balance Sheet showing assets, liabilities, and equity as of a specific date. Provides a snapshot of financial position.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `as_of_date` | string |  | Report as-of date (YYYY-MM-DD, defaults to today) |
| `end_date` | string |  | Alias for as_of_date |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | Balance sheet with assets, liabilities, equity sections |

---

### `report.cashflow`

**Description:** Get Cash Flow Statement report from QuickBooks

> Generates a Cash Flow Statement showing cash from operating, investing, and financing activities. Shows how cash position changed over period.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `start_date` | string |  | Report start date |
| `end_date` | string |  | Report end date |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | Cash flow statement with operating/investing/financing secti |

---

### `report.generalledger`

**Description:** Get General Ledger report

> Generates a General Ledger report showing all transactions by account. The most detailed transaction report available.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `start_date` | string |  | Report start date |
| `end_date` | string |  | Report end date |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | General ledger with all account transactions |

---

### `report.profitloss`

**Description:** Get P&L report from QuickBooks

> Generates a Profit & Loss (Income Statement) report showing revenue, expenses, and net income for a specified period. Can be filtered by class or location.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `start_date` | string |  | Report start date (YYYY-MM-DD) |
| `end_date` | string |  | Report end date (YYYY-MM-DD) |
| `class_id` | string |  | Filter by class ID |
| `location` | string |  | Filter by location/department |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | Full P&L report with rows, columns, and summary |

---

### `report.profitloss.detail`

**Description:** Get detailed P&L report with individual transactions

> Generates a detailed Profit & Loss report showing individual transactions that make up each account balance. More granular than standard P&L.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `start_date` | string |  | Report start date |
| `end_date` | string |  | Report end date |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | Detailed P&L with transaction-level detail |

---

### `salesreceipt.create`

**Description:** Create a sales receipt in QuickBooks

> Creates a sales receipt for immediate payment transactions. Unlike invoices, sales receipts are used when payment is received at time of sale.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `line_items` | array | ✓ | Line items |
| `txn_date` | string |  | Sale date |
| `payment_method` | string |  | Payment method name |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `sales_receipt_id` | string | Receipt ID |
| `doc_number` | string | Receipt number |
| `total_amount` | number | Total |
| `customer_id` | string | Customer |

---

### `taxcode.list`

**Description:** List tax codes

> Retrieves all tax codes defined in QuickBooks. Tax codes determine how sales tax is calculated on transactions.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `active_only` | boolean |  | Only return active tax codes |
| `limit` | integer |  | Maximum results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `tax_codes` | array | List of tax code objects |
| `count` | integer | Number of tax codes |

---

### `term.list`

**Description:** List payment terms

> Retrieves all payment terms defined in QuickBooks (e.g., Net 30, Due on Receipt). Terms define when payment is due and any early payment discounts.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `active_only` | boolean |  | Only return active terms |
| `limit` | integer |  | Maximum results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `terms` | array | List of term objects |
| `count` | integer | Number of terms |

---

### `timeactivity.create`

**Description:** Create a time activity in QuickBooks

> Records time worked by an employee or vendor. Can be marked billable and linked to a customer for invoicing.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `hours` | integer | ✓ | Hours worked |
| `minutes` | integer |  | Minutes worked |
| `txn_date` | string |  | Date |
| `employee_id` | string |  | Employee |
| `customer_id` | string |  | Customer |
| `item_id` | string |  | Service item |
| `description` | string |  | Work done |
| `billable` | boolean |  | Is billable |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `time_activity_id` | string | Activity ID |
| `hours` | integer | Hours |
| `minutes` | integer | Minutes |
| `txn_date` | string | Date |

---

### `transaction.list`

**Description:** List GL transactions for reconciliation

> Returns a transaction list report showing all transactions within a date range. Useful for reconciliation and audit purposes.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `start_date` | string |  | Start date (YYYY-MM-DD) |
| `end_date` | string |  | End date (YYYY-MM-DD) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `report` | object | Transaction list report data |

---

### `vendor.create`

**Description:** Create a vendor in QuickBooks

> Creates a new vendor record in QuickBooks Online. Vendors are companies or individuals you pay (suppliers, contractors, service providers). The vendor_id returned can be used in bill.create to record money owed. Vendor names must be unique within QuickBooks - use vendor.search first to check for duplicates.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_name` | string | ✓ | Display name for the vendor (must be unique in QuickBooks) |
| `email` | string |  | Primary contact email address |
| `phone` | string |  | Primary phone number (free-form format) |
| `website` | string |  | Vendor website URL |
| `billing_address` | object |  | Billing address with Line1, City, State, PostalCode |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendor_id` | string | QuickBooks vendor ID prefixed with 'qb:' |
| `display_name` | string | Confirmed display name as stored in QuickBooks |
| `email` | string | Email address if provided |
| `status` | string | Vendor status ('active' or 'inactive') |
| `created_at` | string | ISO timestamp when vendor was created |

**Example:**
```json
{
  "capability": "vendor.create",
  "params": {
    "vendor_name": "Office Depot",
    "email": "orders@officedepot.com"
  }
}
```

---

### `vendor.get`

**Description:** Get vendor details from QuickBooks

> Retrieves detailed information about a specific vendor by ID. Use this to get current contact information, status, and other vendor details. The vendor_id should include the 'qb:' prefix (e.g., 'qb:123').

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | QuickBooks vendor ID (with 'qb:' prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendor_id` | string | QuickBooks vendor ID with 'qb:' prefix |
| `display_name` | string | Vendor display name |
| `email` | string | Primary email address |
| `phone` | string | Primary phone number |
| `status` | string | Vendor status ('active' or 'inactive') |

---

### `vendor.list`

**Description:** List vendors from QuickBooks

> Returns a paginated list of vendors from QuickBooks. By default returns only active vendors. Use this for bulk retrieval or when you need to see all vendors. For finding a specific vendor by name, use vendor.search instead.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `max_results` | integer |  | Maximum number of vendors to return (1-1000) |
| `start_position` | integer |  | Starting position for pagination (1-based) |
| `active_only` | boolean |  | If true, only return active vendors |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendors` | array | List of vendor objects |
| `count` | integer | Number of vendors returned in this response |

---

### `vendor.search`

**Description:** Search vendors by name with fuzzy matching

> Searches for vendors by name using fuzzy (LIKE) matching. Use this before vendor.create to check if a vendor already exists and avoid duplicates. Also useful for finding vendors when you only have a partial name.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `search_term` | string | ✓ | Search term to match against vendor display names |
| `max_results` | integer |  | Maximum number of results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendors` | array | List of matching vendor objects |
| `count` | integer | Number of vendors matching the search |
| `search_term` | string | The search term that was used |

**Example:**
```json
{
  "capability": "vendor.search",
  "params": {
    "search_term": "Office",
    "max_results": 10
  }
}
```

---

### `vendor.update`

**Description:** Update vendor details

> Updates an existing vendor's information in QuickBooks. Only the fields provided will be updated - omitted fields retain their current values. QuickBooks requires the current SyncToken which is fetched automatically.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | QuickBooks vendor ID (with 'qb:' prefix) |
| `vendor_name` | string |  | New display name (must be unique if changed) |
| `email` | string |  | New email address |
| `phone` | string |  | New phone number |
| `website` | string |  | New website URL |
| `billing_address` | object |  | New billing address object |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendor_id` | string | QuickBooks vendor ID |
| `display_name` | string | Updated display name |
| `updated` | boolean | True if update was successful |

---

## SLACK (14 capabilities)

### `channel.archive`

**Description:** Archive a Slack channel

> Archives a Slack channel. Archived channels are hidden from the channel list but can be unarchived later. Requires appropriate permissions.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | ✓ | Channel ID to archive |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | string | Channel ID |
| `status` | string | Should be 'archived' |

---

### `channel.create`

**Description:** Create a Slack channel

> Creates a new public or private Slack channel. Channel names must be lowercase, without spaces.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | ✓ | Channel name (lowercase, no spaces) |
| `is_private` | boolean |  | Create as private channel |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | string | Channel ID |
| `channel_name` | string | Channel name |
| `is_private` | boolean | Private status |
| `status` | string | Should be 'created' |

---

### `channel.history`

**Description:** Get message history from a Slack channel

> Retrieves recent messages from a Slack channel. Returns messages in reverse chronological order.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | ✓ | Channel ID to get history from |
| `limit` | integer |  | Maximum number of messages to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | string | Channel ID |
| `messages` | array | List of messages |
| `count` | integer | Number of messages |

---

### `channel.invite`

**Description:** Invite users to a Slack channel

> Invites one or more users to a Slack channel. Users must be part of the workspace.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | ✓ | Channel ID to invite to |
| `user_ids` | string | ✓ | Comma-separated user IDs to invite |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | string | Channel ID |
| `invited_users` | string | Invited users |
| `status` | string | Should be 'invited' |

---

### `channel.list`

**Description:** List all channels in the workspace

> Lists all channels in the Slack workspace that the bot has access to. Can filter by public/private channels.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `types` | string |  | Comma-separated channel types: public_channel, private_chann |
| `limit` | integer |  | Maximum number of channels to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `channels` | array | List of channel objects with id, name, is_private, is_archiv |
| `count` | integer | Number of channels |

---

### `channel.topic`

**Description:** Set the topic for a Slack channel

> Sets or updates the topic for a Slack channel. The topic is displayed at the top of the channel.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | ✓ | Channel ID to update |
| `topic` | string | ✓ | New topic text |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | string | Channel ID |
| `topic` | string | New topic |
| `status` | string | Should be 'updated' |

---

### `file.upload`

**Description:** Upload a file to Slack

> Uploads a file to one or more Slack channels. Can include an initial comment with the file.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channels` | string | ✓ | Comma-separated channel IDs to share to |
| `content` | string | ✓ | File content (base64 encoded or raw text) |
| `filename` | string | ✓ | Name for the file |
| `title` | string |  | Title for the file (defaults to filename) |
| `initial_comment` | string |  | Message to post with the file |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | File ID |
| `filename` | string | File name |
| `url` | string | Private file URL |
| `status` | string | Should be 'uploaded' |

---

### `message.direct`

**Description:** Send a direct message on Slack

> Opens a DM conversation with a user and sends a message. Creates the DM channel if it doesn't exist.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | string | ✓ | Slack user ID to message |
| `text` | string | ✓ | Message text content |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message timestamp |
| `channel` | string | DM channel ID |
| `text` | string | Message text |
| `status` | string | Should be 'sent' |

---

### `message.send`

**Description:** Send a message to a Slack channel

> Posts a message to a Slack channel. Supports rich formatting with Block Kit and threaded replies.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel` | string | ✓ | Channel ID or name (e.g., C1234567890 or #general) |
| `text` | string | ✓ | Message text content |
| `blocks` | array |  | Block Kit blocks for rich formatting |
| `thread_ts` | string |  | Thread timestamp to reply to |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message timestamp (ts) |
| `channel` | string | Channel ID |
| `text` | string | Message text |
| `status` | string | Should be 'sent' |

---

### `reaction.add`

**Description:** Add a reaction to a message

> Adds an emoji reaction to a message. The emoji name should be specified without colons (e.g., 'thumbsup' not ':thumbsup:').

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | ✓ | Channel ID where the message is |
| `timestamp` | string | ✓ | Message timestamp (ts) |
| `name` | string | ✓ | Emoji name without colons |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | string | Channel ID |
| `timestamp` | string | Message timestamp |
| `reaction` | string | Emoji name |
| `status` | string | Should be 'added' |

---

### `reaction.remove`

**Description:** Remove a reaction from a message

> Removes an emoji reaction that was previously added to a message.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `channel_id` | string | ✓ | Channel ID where the message is |
| `timestamp` | string | ✓ | Message timestamp (ts) |
| `name` | string | ✓ | Emoji name without colons |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | string | Channel ID |
| `timestamp` | string | Message timestamp |
| `reaction` | string | Emoji name |
| `status` | string | Should be 'removed' |

---

### `search.messages`

**Description:** Search for messages in the workspace

> Searches for messages across the workspace using Slack's search syntax. Supports operators like 'from:', 'in:', 'has:', etc.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ | Search query (supports Slack search operators) |
| `count` | integer |  | Number of results to return |
| `sort` | string |  | Sort field: timestamp or score |
| `sort_dir` | string |  | Sort direction: asc or desc |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Search query used |
| `messages` | array | List of matching messages with text, user, channel, permalin |
| `count` | integer | Results returned |
| `total` | integer | Total matches found |

---

### `user.info`

**Description:** Get detailed information about a user

> Retrieves detailed profile information for a specific Slack user including name, email, title, phone, and timezone.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | string | ✓ | Slack user ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | User ID |
| `name` | string | Username |
| `real_name` | string | Full name |
| `display_name` | string | Display name |
| `email` | string | Email address |
| `title` | string | Job title |
| `phone` | string | Phone number |
| `is_bot` | boolean | Is a bot |
| `is_admin` | boolean | Is workspace admin |
| `timezone` | string | User timezone |

---

### `user.list`

**Description:** List all users in the workspace

> Lists all active users in the Slack workspace. Excludes deleted/deactivated users.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number of users to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `users` | array | List of user objects with id, name, email, is_bot, is_admin |
| `count` | integer | Number of users |

---

## NETSUITE (20 capabilities)

### `netsuite.account.list`

**Description:** Get chart of accounts

> Retrieves the chart of accounts from NetSuite using SuiteQL. Returns account numbers, names, types, and balances. Use to look up account IDs for journal entries and bills.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_type` | string |  | Filter by account type (Bank, Expense, Income, etc.) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | List of accounts with id, number, name, type, balance |
| `count` | integer | Number of accounts returned |

---

### `netsuite.customrecord.create`

**Description:** Create a custom record

> Creates a custom record in NetSuite. Custom records are user-defined record types created in NetSuite. Record type ID format: customrecord_XXX

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `record_type` | string | ✓ | Custom record type ID (e.g., customrecord_myrecord) |
| `fields` | object |  | Field values for the custom record |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | Created record ID prefixed with 'ns:' |
| `record_type` | string | Record type ID |
| `status` | string | Creation status ('created') |

---

### `netsuite.gl.transactions`

**Description:** Get GL transactions for reconciliation

> Retrieves general ledger transaction lines from NetSuite using SuiteQL. Essential for bank reconciliation workflows - matches bank statement lines to GL entries. Filter by account and date range.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_ids` | array |  | Account internal IDs to filter (omit for all accounts) |
| `from_date` | string | ✓ | Start date (YYYY-MM-DD) |
| `to_date` | string | ✓ | End date (YYYY-MM-DD) |
| `subsidiary_id` | string |  | Filter by subsidiary (OneWorld only) |
| `limit` | integer |  | Max results (default 1000) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `transactions` | array | GL transaction lines with account, debit/credit, memo |
| `count` | integer | Number of transactions returned |
| `has_more` | boolean | Whether more results exist |

---

### `netsuite.journal.create`

**Description:** Create a journal entry in NetSuite

> Creates a journal entry in NetSuite's general ledger. CRITICAL: Total debits must equal total credits or the entry will be rejected. Each line requires an account ID and either a debit or credit amount. Uses REST API with TBA or OAuth 2.0 authentication.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `subsidiary_id` | string | ✓ | Internal ID of the subsidiary (OneWorld only) |
| `lines` | array | ✓ | Journal entry lines (each with account_id and debit OR credi |
| `tran_date` | string |  | Transaction date (YYYY-MM-DD). Defaults to today. |
| `memo` | string |  | Header memo for the journal entry |
| `doc_number` | string |  | Custom document number (tranId) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `journal_entry_id` | string | NetSuite internal ID prefixed with 'ns:' |
| `tran_id` | string | Transaction number assigned by NetSuite |
| `tran_date` | string | Transaction date |
| `status` | string | Journal entry status |

---

### `netsuite.journal.get`

**Description:** Get a journal entry by ID

> Retrieves a journal entry from NetSuite by its internal ID. Returns full details including all line items with account information, debits, credits, and any segment values (department, class, location).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `journal_entry_id` | string | ✓ | NetSuite internal ID (with or without 'ns:' prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `journal_entry_id` | string | NetSuite internal ID prefixed with 'ns:' |
| `tran_id` | string | Transaction number |
| `tran_date` | string | Transaction date |
| `memo` | string | Header memo |
| `subsidiary_id` | string | Subsidiary internal ID |
| `lines` | array | Line items with account, debit/credit amounts |
| `status` | string | Approval/posting status |

---

### `netsuite.payment.batch`

**Description:** Process multiple vendor payments

> Processes multiple vendor payments in a batch. Each payment is processed independently - failures don't affect others. Returns results and errors for each payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payments` | array | ✓ | Array of payment specifications (same format as payment.crea |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `processed` | integer | Number of payments successfully processed |
| `failed` | integer | Number of payments that failed |
| `payments` | array | Successful payment results |
| `errors` | array | Failed payments with error details |

---

### `netsuite.payment.create`

**Description:** Create a vendor payment

> Creates a vendor payment in NetSuite to pay one or more bills. Specify the vendor, bank account, and bills to pay. Payments can be partial or full payment of bills.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Vendor internal ID (with or without 'ns:' prefix) |
| `bank_account_id` | string | ✓ | Bank account internal ID to pay from |
| `bills_to_pay` | array |  | Bills to pay with optional amounts |
| `payment_date` | string |  | Payment date (YYYY-MM-DD). Defaults to today. |
| `memo` | string |  | Payment memo |
| `payment_method` | string |  | Payment method internal ID (check, ACH, wire, etc.) |
| `subsidiary_id` | string |  | Subsidiary internal ID (OneWorld only) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | NetSuite payment ID prefixed with 'ns:' |
| `tran_id` | string | Transaction number |
| `total` | number | Total payment amount |
| `status` | string | Payment status |

---

### `netsuite.purchaseorder.create`

**Description:** Create a purchase order

> Creates a purchase order in NetSuite. POs are used to order items from vendors. When received, POs can be converted to vendor bills.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Vendor internal ID (with or without 'ns:' prefix) |
| `item_lines` | array | ✓ | Item lines with item_id, quantity, and optional rate |
| `tran_date` | string |  | Order date (YYYY-MM-DD). Defaults to today. |
| `memo` | string |  | PO memo |
| `location` | string |  | Location internal ID for receiving |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `purchase_order_id` | string | NetSuite PO ID prefixed with 'ns:' |
| `tran_id` | string | Transaction number |
| `total` | number | PO total amount |
| `status` | string | PO status |

---

### `netsuite.query`

**Description:** Execute SuiteQL query

> Executes a SuiteQL query against NetSuite. SuiteQL is NetSuite's SQL-like query language. Max 100,000 total results, 1,000 per page. Use for custom data retrieval not covered by other capabilities.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ | SuiteQL query string |
| `limit` | integer |  | Max results per page (max 1000) |
| `offset` | integer |  | Pagination offset |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `items` | array | Query result rows |
| `count` | integer | Number of rows returned |
| `has_more` | boolean | Whether more results exist |

---

### `netsuite.reconcile.bank`

**Description:** Reconcile bank statement

> Compares bank statement balance against NetSuite GL balance for a specific account and date. Returns variance information. Note: Actual reconciliation is typically done in NetSuite UI.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Bank account internal ID |
| `statement_date` | string | ✓ | Statement date (YYYY-MM-DD) |
| `ending_balance` | number | ✓ | Bank statement ending balance |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `account_id` | string | Account ID |
| `statement_date` | string | Statement date |
| `statement_balance` | number | Bank statement balance |
| `gl_balance` | number | NetSuite GL balance |
| `variance` | number | Difference between statement and GL |
| `status` | string | 'balanced' or 'variance_exists' |

---

### `netsuite.subsidiary.list`

**Description:** Get list of subsidiaries

> Retrieves the list of subsidiaries from a NetSuite OneWorld account. Subsidiary IDs are required for journal entries and transactions. Non-OneWorld accounts have a single implicit subsidiary.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `subsidiaries` | array | List of subsidiaries with id, name, country |
| `count` | integer | Number of subsidiaries |

---

### `netsuite.vendor.create`

**Description:** Create a vendor in NetSuite

> Creates a new vendor record in NetSuite. Vendors are entities you pay - suppliers, contractors, service providers. The vendor_id returned can be used to create bills and payments.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_name` | string | ✓ | Vendor company name (must be unique) |
| `email` | string |  | Primary email address |
| `phone` | string |  | Primary phone number |
| `terms` | string |  | Payment terms internal ID |
| `account_number` | string |  | Your account number with this vendor |
| `subsidiary_id` | string |  | Subsidiary internal ID (OneWorld only) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendor_id` | string | NetSuite internal ID prefixed with 'ns:' |
| `company_name` | string | Confirmed company name |
| `status` | string | Vendor status ('active') |

---

### `netsuite.vendor.get`

**Description:** Get vendor details from NetSuite

> Retrieves a vendor record from NetSuite by its internal ID. Returns company information, contact details, and current balance.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Vendor internal ID (with or without 'ns:' prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendor_id` | string | NetSuite internal ID prefixed with 'ns:' |
| `company_name` | string | Vendor company name |
| `email` | string | Primary email address |
| `phone` | string | Primary phone number |
| `balance` | number | Current open balance |

---

### `netsuite.vendor.search`

**Description:** Search for vendors by company name

> Searches for vendors in NetSuite by company name using SuiteQL. Returns matching vendors with basic info. Use before creating vendors to avoid duplicates.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_name` | string | ✓ | Company name to search for (partial match supported) |
| `limit` | integer |  | Max results to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendors` | array | List of matching vendors |
| `count` | integer | Number of vendors found |

---

### `netsuite.vendor.update`

**Description:** Update vendor record

> Updates an existing vendor record in NetSuite. Can update contact info, address, payment terms, and other fields. Only provided fields are updated - others remain unchanged.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Vendor internal ID (with or without 'ns:' prefix) |
| `company_name` | string |  | New company name |
| `email` | string |  | New email address |
| `phone` | string |  | New phone number |
| `address` | object |  | Address object with street1, street2, city, state, zip, coun |
| `terms` | string |  | Payment terms internal ID |
| `account_number` | string |  | Your account number with this vendor |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendor_id` | string | Vendor internal ID |
| `company_name` | string | Updated company name |
| `status` | string | Update status ('updated') |

---

### `netsuite.vendor.upload_document`

**Description:** Attach document to vendor record

> Uploads a document (W-9, contract, etc.) to NetSuite File Cabinet and attaches it to a vendor record. File content must be base64 encoded.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Vendor internal ID |
| `file_name` | string | ✓ | Name for the file |
| `file_content` | string | ✓ | Base64 encoded file content |
| `file_type` | string |  | File type (default: _PDF) |
| `folder_id` | string |  | File Cabinet folder ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | NetSuite file ID |
| `file_name` | string | Uploaded file name |
| `vendor_id` | string | Vendor the file is attached to |
| `status` | string | Upload status ('attached') |

---

### `netsuite.vendorbill.approve`

**Description:** Approve a vendor bill

> Sets the approval status of a vendor bill to Approved. Only applicable if bill approvals are enabled in NetSuite. Approved bills can then be scheduled for payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bill_id` | string | ✓ | Vendor bill internal ID (with or without 'ns:' prefix) |
| `approver_note` | string |  | Optional approval note/memo |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bill_id` | string | Bill internal ID |
| `approval_status` | string | New approval status ('approved') |
| `status` | string | Bill status |

---

### `netsuite.vendorbill.create`

**Description:** Create a vendor bill in NetSuite

> Creates a vendor bill (accounts payable) in NetSuite. Vendor bills track money owed to suppliers. Each bill has expense lines with account allocations. Bills can be approved and paid via vendor payments.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Vendor internal ID (with or without 'ns:' prefix) |
| `expense_lines` | array | ✓ | Expense line items with account_id and amount |
| `tran_date` | string |  | Bill date (YYYY-MM-DD). Defaults to today. |
| `due_date` | string |  | Payment due date (YYYY-MM-DD) |
| `memo` | string |  | Header memo |
| `terms` | string |  | Payment terms internal ID |
| `ref_number` | string |  | Vendor's invoice/reference number |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bill_id` | string | NetSuite internal ID prefixed with 'ns:' |
| `tran_id` | string | Transaction number |
| `amount` | number | Bill total amount |
| `status` | string | Bill status (pendingApproval, open, etc.) |

---

### `netsuite.vendorbill.get`

**Description:** Get a vendor bill by ID

> Retrieves a vendor bill from NetSuite by its internal ID. Returns full details including expense lines, payment status, and approval status.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bill_id` | string | ✓ | Vendor bill internal ID (with or without 'ns:' prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bill_id` | string | NetSuite internal ID prefixed with 'ns:' |
| `tran_id` | string | Transaction number |
| `vendor_id` | string | Vendor internal ID |
| `tran_date` | string | Bill date |
| `due_date` | string | Payment due date |
| `amount` | number | Bill total amount |
| `balance` | number | Amount remaining (unpaid) |
| `status` | string | Bill status |
| `approval_status` | string | Approval workflow status |
| `expense_lines` | array | Expense line items |

---

### `netsuite.vendorbill.list`

**Description:** List vendor bills with filters

> Lists vendor bills using SuiteQL query. Supports filtering by vendor, date range, and status. Returns up to 1000 results per page.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string |  | Filter by vendor internal ID |
| `from_date` | string |  | Start date filter (YYYY-MM-DD) |
| `to_date` | string |  | End date filter (YYYY-MM-DD) |
| `limit` | integer |  | Max results (default 100, max 1000) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bills` | array | List of vendor bills |
| `count` | integer | Number of bills returned |
| `has_more` | boolean | Whether more results exist |

---

## SAGE_INTACCT (25 capabilities)

### `sage_intacct.accounts.create`

**Description:** Create a new GL account in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_no` | string | ✓ | Account number |
| `title` | string | ✓ | Account title |
| `account_type` | string | ✓ | Account type |
| `normal_balance` | string |  | Normal balance (default: based on type) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `account` | object | Created account |
| `status` | string | Should be 'success' |

---

### `sage_intacct.accounts.list`

**Description:** List chart of accounts from Sage Intacct

> Lists GL accounts with optional filtering by type and status.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_type` | string |  | Filter by account type |
| `status` | string |  | Filter by status |
| `page_size` | integer |  | Results per page (default 100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | List of GL accounts |
| `count` | integer | Number of accounts |

---

### `sage_intacct.ar_payments.create`

**Description:** Record an AR payment in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID for the payment |
| `bank_account_id` | string | ✓ | Bank account ID for deposit |
| `payment_date` | string | ✓ | Payment date (YYYY-MM-DD) |
| `invoices` | array | ✓ | Invoices to apply with invoice_key and amount |
| `payment_method` | string |  | Payment method (check, ACH, wire) |
| `reference_number` | string |  | Check or reference number |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment` | object | Created payment |
| `status` | string | Should be 'success' |

---

### `sage_intacct.bank_accounts.balance`

**Description:** Get bank account balance from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bank_account_id` | string | ✓ | Bank account ID to check |
| `as_of_date` | string |  | Balance as of date (YYYY-MM-DD) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bank_account_id` | string | Account ID |
| `gl_balance` | number | GL balance |
| `bank_balance` | number | Bank balance |
| `uncleared_amount` | number | Uncleared |

---

### `sage_intacct.bank_accounts.list`

**Description:** List bank accounts from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Filter by status |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bank_accounts` | array | Bank accounts |
| `count` | integer | Account count |

---

### `sage_intacct.bill_payments.create`

**Description:** Create a bill payment in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bank_account_id` | string | ✓ | Bank account ID for payment |
| `payment_date` | string | ✓ | Payment date (YYYY-MM-DD) |
| `bills` | array | ✓ | Bills to pay with bill_key and amount |
| `payment_method` | string |  | Payment method (check, ACH, wire) |
| `reference_number` | string |  | Check or reference number |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment` | object | Created payment |
| `status` | string | Should be 'success' |

---

### `sage_intacct.bills.create`

**Description:** Create an AP bill in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Vendor ID for the bill |
| `bill_date` | string | ✓ | Bill date (YYYY-MM-DD) |
| `due_date` | string |  | Due date (YYYY-MM-DD) |
| `bill_number` | string |  | External bill/invoice number |
| `lines` | array | ✓ | Bill lines with gl_account, amount, memo |
| `description` | string |  | Bill description or memo |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bill` | object | Created bill |
| `status` | string | Should be 'success' |

---

### `sage_intacct.bills.list`

**Description:** List AP bills from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string |  | Filter by vendor ID |
| `status` | string |  | Filter by bill status |
| `date_from` | string |  | Start date filter (YYYY-MM-DD) |
| `date_to` | string |  | End date filter (YYYY-MM-DD) |
| `page_size` | integer |  | Number of results per page |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bills` | array | AP bills |
| `count` | integer | Bill count |

---

### `sage_intacct.bills.post`

**Description:** Post a draft AP bill in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bill_key` | string | ✓ | Sage Intacct bill record key |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bill_key` | string | Posted bill key |
| `status` | string | Should be 'posted' |

---

### `sage_intacct.company.get`

**Description:** Get Sage Intacct company information

> Retrieves company details including name, ID, and configuration.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `company_id` | string | Company ID |
| `company_name` | string | Company name |

---

### `sage_intacct.customers.create`

**Description:** Create a customer in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Unique customer identifier |
| `name` | string | ✓ | Customer display name |
| `email` | string |  | Customer email address |
| `phone` | string |  | Customer phone number |
| `payment_terms` | string |  | Payment terms code |
| `credit_limit` | number |  | Customer credit limit |
| `billing_address` | object |  | Billing address object |
| `shipping_address` | object |  | Shipping address object |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customer` | object | Created customer |
| `status` | string | Should be 'success' |

---

### `sage_intacct.customers.list`

**Description:** List customers from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Filter by status |
| `customer_type` | string |  | Filter by customer type |
| `page_size` | integer |  | Number of results per page |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customers` | array | List of customers |
| `count` | integer | Customer count |

---

### `sage_intacct.deposits.create`

**Description:** Create a bank deposit in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bank_account_id` | string | ✓ | Bank account ID for deposit |
| `deposit_date` | string | ✓ | Deposit date (YYYY-MM-DD) |
| `entries` | array | ✓ | Deposit entries with gl_account and amount |
| `description` | string |  | Deposit description or memo |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `deposit` | object | Created deposit |
| `status` | string | Should be 'success' |

---

### `sage_intacct.invoices.create`

**Description:** Create an AR invoice in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID for the invoice |
| `invoice_date` | string | ✓ | Invoice date (YYYY-MM-DD) |
| `due_date` | string |  | Due date (YYYY-MM-DD) |
| `lines` | array | ✓ | Invoice lines |
| `description` | string |  | Invoice description or memo |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice` | object | Created invoice |
| `status` | string | Should be 'success' |

---

### `sage_intacct.invoices.list`

**Description:** List AR invoices from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string |  | Filter by customer ID |
| `status` | string |  | Filter by invoice status |
| `date_from` | string |  | Start date filter (YYYY-MM-DD) |
| `date_to` | string |  | End date filter (YYYY-MM-DD) |
| `page_size` | integer |  | Number of results per page |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoices` | array | AR invoices |
| `count` | integer | Invoice count |

---

### `sage_intacct.journals.create`

**Description:** Create a journal entry in Sage Intacct

> Creates a journal entry with debit and credit lines. Total debits must equal total credits.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `journal_date` | string | ✓ | Journal date (YYYY-MM-DD) |
| `description` | string |  | Journal description |
| `lines` | array | ✓ | Journal lines with account_no, amount, memo, debit/credit |
| `reference_number` | string |  | External reference |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `journal_entry` | object | Created journal |
| `status` | string | Should be 'success' |

---

### `sage_intacct.journals.list`

**Description:** List journal entries from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `date_from` | string |  | Start date (YYYY-MM-DD) |
| `date_to` | string |  | End date (YYYY-MM-DD) |
| `state` | string |  | Filter by state |
| `page_size` | integer |  | Results per page |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `journals` | array | Journal entries |
| `count` | integer | Number of entries |

---

### `sage_intacct.journals.post`

**Description:** Post a draft journal entry in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `journal_key` | string | ✓ | Journal key to post |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `journal_key` | string | Posted journal key |
| `status` | string | Should be 'posted' |

---

### `sage_intacct.reports.ap_aging`

**Description:** Get AP aging report from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `as_of_date` | string |  | Report as-of date (YYYY-MM-DD) |
| `vendor_id` | string |  | Filter by vendor ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `aging` | object | Aging buckets (current, 1-30, 31-60, 61-90, over 90) |
| `total` | number | Total AP balance |

---

### `sage_intacct.reports.ar_aging`

**Description:** Get AR aging report from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `as_of_date` | string |  | Report as-of date (YYYY-MM-DD) |
| `customer_id` | string |  | Filter by customer ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `aging` | object | Aging buckets (current, 1-30, 31-60, 61-90, over 90) |
| `total` | number | Total AR balance |

---

### `sage_intacct.reports.cash_flow`

**Description:** Get cash flow statement from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `start_date` | string | ✓ | Period start date (YYYY-MM-DD) |
| `end_date` | string | ✓ | Period end date (YYYY-MM-DD) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `operating` | object | Operating activities |
| `investing` | object | Investing activities |
| `financing` | object | Financing activities |
| `net_change` | number | Net cash change |

---

### `sage_intacct.reports.trial_balance`

**Description:** Get trial balance report from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `as_of_date` | string |  | Report as-of date (YYYY-MM-DD) |
| `reporting_period` | string |  | Reporting period key |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | Accounts with debit/credit balances |
| `total_debits` | number | Total debits |
| `total_credits` | number | Total credits |

---

### `sage_intacct.transfers.create`

**Description:** Create a bank transfer in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `from_account_id` | string | ✓ | Source bank account ID |
| `to_account_id` | string | ✓ | Destination bank account ID |
| `transfer_date` | string | ✓ | Transfer date (YYYY-MM-DD) |
| `amount` | number | ✓ | Transfer amount |
| `description` | string |  | Transfer description or memo |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `transfer` | object | Created transfer |
| `status` | string | Should be 'success' |

---

### `sage_intacct.vendors.create`

**Description:** Create a vendor in Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Unique vendor identifier |
| `name` | string | ✓ | Vendor display name |
| `email` | string |  | Vendor email address |
| `phone` | string |  | Vendor phone number |
| `tax_id` | string |  | Tax identification number |
| `payment_term` | string |  | Payment terms code |
| `address` | object |  | Vendor address object |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendor` | object | Created vendor |
| `status` | string | Should be 'success' |

---

### `sage_intacct.vendors.list`

**Description:** List vendors from Sage Intacct

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Filter by status |
| `vendor_type` | string |  | Filter by vendor type |
| `page_size` | integer |  | Number of results per page |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendors` | array | List of vendors |
| `count` | integer | Vendor count |

---

## MICROSOFT (16 capabilities)

### `excel.range.get`

**Description:** Get cell values from an Excel range

> Retrieves values from a specified range in an Excel workbook stored in OneDrive. Returns a 2D array of cell values. Use for reading financial data, reports, or any tabular data. The workbook must be accessible via Microsoft Graph API.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workbook_id` | string | ✓ | OneDrive item ID of the Excel file |
| `worksheet_name` | string |  | Name of the worksheet (default: Sheet1) |
| `range` | string | ✓ | Cell range in A1 notation |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `workbook_id` | string | Workbook ID |
| `worksheet` | string | Worksheet name |
| `range` | string | Actual range address |
| `values` | array | 2D array of cell values (rows x columns) |
| `row_count` | integer | Number of rows |
| `column_count` | integer | Number of columns |

**Example:**
```json
{
  "capability": "excel.range.get",
  "params": {
    "workbook_id": "01ABCDEFGHIJKLMNOP",
    "worksheet_name": "Revenue",
    "range": "A1:E20"
  }
}
```

---

### `excel.range.update`

**Description:** Update cell values in an Excel range

> Updates values in a specified range of an Excel workbook. Values must be provided as a 2D array matching the dimensions of the target range. Use for updating financial data, posting journal entries, or bulk data updates.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workbook_id` | string | ✓ | OneDrive item ID of the Excel file |
| `worksheet_name` | string |  | Name of the worksheet (default: Sheet1) |
| `range` | string | ✓ | Cell range to update in A1 notation |
| `values` | array | ✓ | 2D array of values to write (must match range dimensions) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `workbook_id` | string | Workbook ID |
| `worksheet` | string | Worksheet name |
| `updated_range` | string | Updated range address |
| `status` | string | Should be 'updated' |

**Example:**
```json
{
  "capability": "excel.range.update",
  "params": {
    "workbook_id": "01ABCDEFGHIJKLMNOP",
    "worksheet_name": "Budget",
    "range": "B2:B4",
    "values": [
      [
        150000
      ],
      [
        175000
      ],
      [
        200000
      ]
    ]
  }
}
```

---

### `excel.row.append`

**Description:** Append a row to the end of data in Excel worksheet

> Appends a single row of data after the last used row in a worksheet. Automatically detects the end of existing data and adds the new row below. Ideal for adding new transactions, log entries, or incremental data.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workbook_id` | string | ✓ | OneDrive item ID of the Excel file |
| `worksheet_name` | string |  | Name of the worksheet (default: Sheet1) |
| `values` | array | ✓ | Array of values for the new row |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `workbook_id` | string | Workbook ID |
| `worksheet` | string | Worksheet name |
| `appended_range` | string | Range address of the appended row (e.g., A25:D25) |
| `status` | string | Should be 'appended' |

**Example:**
```json
{
  "capability": "excel.row.append",
  "params": {
    "workbook_id": "01ABCDEFGHIJKLMNOP",
    "worksheet_name": "Transactions",
    "values": [
      "2025-01-15",
      "Vendor Payment",
      -5000.0,
      "Bank of America"
    ]
  }
}
```

---

### `excel.table.create`

**Description:** Create an Excel table from a range

> Converts a range of cells into a formatted Excel table. Tables provide structured references, auto-filtering, and better formula support. Ideal for financial data that needs sorting, filtering, or PivotTable source.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workbook_id` | string | ✓ | OneDrive item ID of the Excel file |
| `worksheet_name` | string |  | Name of the worksheet (default: Sheet1) |
| `range` | string | ✓ | Range to convert to table in A1 notation |
| `has_headers` | boolean |  | Whether the first row contains headers (default: true) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `workbook_id` | string | Workbook ID |
| `worksheet` | string | Worksheet name |
| `table_id` | string | Created table ID |
| `table_name` | string | Table name |
| `status` | string | Should be 'created' |

---

### `excel.worksheet.create`

**Description:** Create a new worksheet in an Excel workbook

> Creates a new worksheet (tab) in an existing Excel workbook. Use for organizing data by period, department, or category.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workbook_id` | string | ✓ | OneDrive item ID of the Excel file |
| `worksheet_name` | string | ✓ | Name for the new worksheet |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `workbook_id` | string | Workbook ID |
| `worksheet_id` | string | New worksheet ID |
| `worksheet_name` | string | Worksheet name |
| `status` | string | Should be 'created' |

---

### `excel.worksheet.list`

**Description:** List all worksheets in an Excel workbook

> Lists all worksheets (tabs) in an Excel workbook with their IDs, names, positions, and visibility status. Use to discover available data sheets.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workbook_id` | string | ✓ | OneDrive item ID of the Excel file |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `workbook_id` | string | Workbook ID |
| `worksheets` | array | List of worksheets with id, name, position, visibility |
| `count` | integer | Number of worksheets |

---

### `onedrive.file.download`

**Description:** Download file from OneDrive

> Downloads a file from OneDrive by its file ID. Returns the file content as base64 encoded string.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_id` | string | ✓ | OneDrive file ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | File ID |
| `file_name` | string | File name |
| `size_bytes` | integer | File size |
| `file_content` | string | Base64 encoded content |
| `status` | string | Should be 'downloaded' |

---

### `onedrive.file.list`

**Description:** List files in OneDrive

> Lists files in OneDrive, optionally filtered by folder ID or path. Returns file metadata including IDs, names, sizes, and folder indicators.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `folder_id` | string |  | List files in specific folder by ID |
| `folder_path` | string |  | List files in specific folder by path (e.g., '/Documents') |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `files` | array | List of file objects with id, name, size, is_folder, timesta |
| `count` | integer | Number of files returned |

---

### `onedrive.file.metadata`

**Description:** Get file metadata without downloading content

> Retrieves detailed metadata for a file including name, size, type, timestamps, and whether it's a folder. Does not download the file content.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_id` | string | ✓ | OneDrive file ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | File ID |
| `file_name` | string | File name |
| `size_bytes` | integer | File size |
| `is_folder` | boolean | Whether item is a folder |
| `created_time` | string | Creation time |
| `modified_time` | string | Last modified time |
| `web_url` | string | View URL |
| `mime_type` | string | MIME type (files only) |

---

### `onedrive.file.upload`

**Description:** Upload file to OneDrive

> Uploads a file to OneDrive. File content must be base64 encoded. Optionally specify a folder path to upload into a specific folder.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_name` | string | ✓ | Name for the uploaded file |
| `file_content` | string | ✓ | Base64 encoded file content |
| `folder_path` | string |  | Folder path (e.g., '/Documents'). Uploads to root if omitted |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | OneDrive file ID |
| `file_name` | string | Uploaded file name |
| `size_bytes` | integer | File size in bytes |
| `created_time` | string | Creation timestamp |
| `web_url` | string | URL to view file |
| `status` | string | Should be 'uploaded' |

---

### `onedrive.folder.create`

**Description:** Create a folder in OneDrive

> Creates a new folder in OneDrive. Can be created at root level or as a subfolder using parent folder ID or path.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `folder_name` | string | ✓ | Name for the new folder |
| `parent_folder_id` | string |  | Parent folder ID |
| `parent_folder_path` | string |  | Parent folder path (e.g., '/Documents') |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `folder_id` | string | New folder ID |
| `folder_name` | string | Folder name |
| `web_url` | string | URL to view folder |
| `status` | string | Should be 'created' |

---

### `outlook.availability.check`

**Description:** Check free/busy availability for attendees

> Checks the availability of one or more people in a time range. Returns free/busy status for scheduling meetings when everyone is available.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `attendees` | array | ✓ | Email addresses to check availability for |
| `start_datetime` | string | ✓ | Start of range to check (ISO 8601) |
| `end_datetime` | string | ✓ | End of range to check (ISO 8601) |
| `timezone` | string |  | Timezone (default: Eastern Standard Time) |
| `interval_minutes` | integer |  | Availability check interval in minutes (default: 30) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `start_time` | string | Range start |
| `end_time` | string | Range end |
| `attendees` | array | Attendee availability with email, availability_view (0=free, |

---

### `outlook.event.cancel`

**Description:** Cancel a calendar event and notify attendees

> Cancels an event and sends cancellation notices to all attendees. Optionally include a comment explaining the cancellation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | string | ✓ | Event ID to cancel |
| `comment` | string |  | Cancellation message to attendees |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Cancelled event ID |
| `status` | string | Should be 'cancelled' |

---

### `outlook.event.create`

**Description:** Create a calendar event in Outlook

> Creates a new calendar event in the user's Outlook calendar. Supports attendees, location, Teams meetings, and rich text body. Use for scheduling finance reviews, audit meetings, or deadline reminders.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `subject` | string | ✓ | Event subject/title |
| `start_datetime` | string | ✓ | Start time in ISO 8601 format |
| `end_datetime` | string | ✓ | End time in ISO 8601 format |
| `body` | string |  | Event body/description |
| `is_html` | boolean |  | Whether body is HTML (default: false) |
| `timezone` | string |  | Timezone (default: Eastern Standard Time) |
| `attendees` | array |  | List of attendee email addresses |
| `location` | string |  | Event location |
| `add_teams_meeting` | boolean |  | Create Teams meeting link (default: false) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Created event ID |
| `subject` | string | Event subject |
| `start_time` | string | Start time |
| `end_time` | string | End time |
| `web_link` | string | URL to view event in Outlook |
| `teams_link` | string | Teams meeting join URL (if Teams meeting enabled) |
| `status` | string | Should be 'confirmed' |
| `attendees` | array | Attendees with email and response_status |

**Example:**
```json
{
  "capability": "outlook.event.create",
  "params": {
    "subject": "Month-End Close Review",
    "start_datetime": "2025-01-31T16:00:00",
    "end_datetime": "2025-01-31T17:00:00",
    "attendees": [
      "controller@company.com",
      "ap@company.com"
    ],
    "add_teams_meeting": true,
    "body": "Review month-end close status and outstanding items."
  }
}
```

---

### `outlook.event.list`

**Description:** List calendar events in a date range

> Retrieves calendar events within a specified date range. Returns event details including attendees, location, and Teams links.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `start_datetime` | string |  | Start of date range (ISO 8601) |
| `end_datetime` | string |  | End of date range (ISO 8601) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `events` | array | Events with event_id, subject, body, start_time, end_time, l |
| `count` | integer | Number of events |

---

### `outlook.event.update`

**Description:** Update an existing calendar event

> Updates an existing calendar event. Only provided fields are updated. Attendees receive update notifications automatically.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | string | ✓ | Event ID to update |
| `subject` | string |  | New event subject |
| `start_datetime` | string |  | New start time (ISO 8601) |
| `end_datetime` | string |  | New end time (ISO 8601) |
| `body` | string |  | New event body |
| `is_html` | boolean |  | Whether body is HTML |
| `timezone` | string |  | Timezone for new times |
| `location` | string |  | New location |
| `attendees` | array |  | Updated attendee list (replaces existing) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Updated event ID |
| `subject` | string | Event subject |
| `start_time` | string | Start time |
| `end_time` | string | End time |
| `web_link` | string | Event URL |
| `status` | string | Should be 'updated' |

---

## GOOGLE (23 capabilities)

### `email.download_attachment`

**Description:** Download email attachment to specified path

> Downloads an email attachment and saves it to the specified file path.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | string | ✓ | Gmail message ID |
| `attachment_id` | string | ✓ | Attachment ID from get_message_full |
| `output_path` | string | ✓ | File path to save attachment |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `output_path` | string | Saved file path |
| `size_bytes` | integer | File size |
| `status` | string | Should be 'downloaded' |

---

### `email.draft`

**Description:** Create a draft email in Gmail

> Creates a draft email that can be edited and sent later from Gmail.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `to` | string | ✓ | Recipient email address |
| `subject` | string | ✓ | Email subject line |
| `body` | string |  | Email body content |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `draft_id` | string | Draft ID |
| `message_id` | string | Message ID |
| `status` | string | Should be 'draft' |

---

### `email.forward`

**Description:** Forward an email to another recipient

> Forwards an email message to a new recipient. Includes the original message content with forward headers.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | string | ✓ | Gmail message ID to forward |
| `to` | string | ✓ | Recipient email address |
| `message` | string |  | Additional message to include above forwarded content |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | New message ID |
| `thread_id` | string | Thread ID |
| `status` | string | Should be 'forwarded' |
| `to` | string | Recipient |
| `original_message_id` | string | Original ID |

---

### `email.get_history`

**Description:** Fetch Gmail history changes for incremental sync

> Retrieves history of changes since a given history ID. Used for efficient incremental synchronization with push notifications.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `start_history_id` | string | ✓ | History ID to start from |
| `max_results` | integer |  | Maximum number of history records |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `history` | array | History records |
| `history_id` | string | Current history ID |
| `next_page_token` | string | Pagination |

---

### `email.get_message_full`

**Description:** Get full email message with headers, body, and attachments

> Retrieves complete email message including headers, body content, and attachment metadata (attachments are not downloaded).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | string | ✓ | Gmail message ID |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message ID |
| `thread_id` | string | Thread ID |
| `label_ids` | array | Label IDs |
| `headers` | object | Email headers |
| `subject` | string | Subject |
| `from` | string | Sender |
| `to` | string | Recipient |
| `date` | string | Date |
| `body` | string | Body content |
| `attachments` | array | Attachment metadata |

---

### `email.label.apply`

**Description:** Apply or remove labels from a message

> Modifies the labels on an email message. Can add and remove multiple labels in a single operation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | string | ✓ | Gmail message ID |
| `add_label_ids` | array |  | Label IDs to add |
| `remove_label_ids` | array |  | Label IDs to remove |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message ID |
| `added_labels` | array | Labels added |
| `removed_labels` | array | Labels removed |
| `status` | string | Should be 'modified' |

---

### `email.label.create`

**Description:** Create a new label

> Creates a new user label in Gmail for organizing messages.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | ✓ | Label name |
| `visibility` | string |  | Label visibility: labelShow, labelShowIfUnread, or labelHide |
| `message_visibility` | string |  | Message list visibility: show or hide |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `label_id` | string | New label ID |
| `name` | string | Label name |
| `type` | string | Label type (user) |
| `status` | string | Should be 'created' |

---

### `email.label.list`

**Description:** List all labels in the mailbox

> Retrieves all labels in the Gmail mailbox, including system labels (INBOX, SENT, TRASH, etc.) and user-created labels.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `labels` | array | List of label objects with id, name, and type |
| `count` | integer | Number of labels |

---

### `email.mark_as_read`

**Description:** Mark email message as read

> Marks an email message as read by removing the UNREAD label.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | string | ✓ | Gmail message ID |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message ID |
| `status` | string | Should be 'read' |

---

### `email.read`

**Description:** Read emails from Gmail

> Retrieves emails from Gmail inbox using search queries. Supports Gmail search operators like from:, to:, subject:, etc.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string |  | Gmail search query |
| `max_results` | integer |  | Maximum number of emails to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `emails` | array | List of email objects |
| `count` | integer | Number of emails |
| `next_page_token` | string | Token for pagination |

---

### `email.reply`

**Description:** Reply to an email in the same thread

> Sends a reply to an existing email thread. The reply is added to the same conversation thread in Gmail.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `thread_id` | string | ✓ | Gmail thread ID to reply to |
| `to` | string | ✓ | Recipient email address |
| `body` | string |  | Reply body content |
| `subject` | string |  | Subject line (defaults to 'Re: ') |
| `is_html` | boolean |  | Whether body is HTML content |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | New message ID |
| `thread_id` | string | Thread ID |
| `status` | string | Should be 'sent' |
| `to` | string | Recipient |

---

### `email.send`

**Description:** Send an email via Gmail

> Sends an email through the Gmail API. Supports HTML content, CC/BCC recipients, and file attachments. Requires OAuth authentication.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `to` | string | ✓ | Recipient email address |
| `subject` | string | ✓ | Email subject line |
| `body` | string |  | Email body content |
| `cc` | string |  | CC recipients (comma-separated) |
| `bcc` | string |  | BCC recipients (comma-separated) |
| `is_html` | boolean |  | Whether body is HTML content |
| `attachments` | array |  | File attachments |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Gmail message ID |
| `thread_id` | string | Thread ID |
| `status` | string | Should be 'sent' |
| `to` | string | Recipient |
| `subject` | string | Subject |

---

### `email.setup_watch`

**Description:** Set up Gmail push notifications watch

> Configures Gmail to send push notifications to a Cloud Pub/Sub topic when new emails arrive. Watch expires after 7 days and must be renewed.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic_name` | string | ✓ | Cloud Pub/Sub topic name |
| `label_ids` | array |  | Labels to watch |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `history_id` | string | Starting history ID |
| `expiration` | string | Watch expiration |
| `status` | string | Should be 'active' |

---

### `email.star`

**Description:** Star or unstar an email message

> Adds or removes the STARRED label from an email message. Starred messages appear in the Starred view in Gmail.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | string | ✓ | Gmail message ID |
| `starred` | boolean |  | True to star, False to unstar |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message ID |
| `starred` | boolean | New starred status |
| `status` | string | 'starred' or 'unstarred' |

---

### `email.thread.get`

**Description:** Get a full email thread with all messages

> Retrieves a complete email thread including all messages in the conversation. Useful for understanding the full context of an email exchange.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `thread_id` | string | ✓ | Gmail thread ID |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `thread_id` | string | Thread ID |
| `messages` | array | List of messages in the thread with full content |
| `message_count` | integer | Number of messages |

---

### `email.thread.list`

**Description:** List email threads

> Lists email threads matching a search query. Threads group related messages together (like email conversations in Gmail).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string |  | Gmail search query |
| `max_results` | integer |  | Maximum number of threads to return |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `threads` | array | List of thread objects with id and snippet |
| `count` | integer | Number of threads |
| `next_page_token` | string | Pagination token |

---

### `email.trash`

**Description:** Move email message to trash

> Moves an email message to the Trash folder. Messages in Trash are automatically deleted after 30 days.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | string | ✓ | Gmail message ID to trash |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message ID |
| `status` | string | Should be 'trashed' |

---

### `email.untrash`

**Description:** Restore email message from trash

> Restores an email message from the Trash folder back to its original location.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | string | ✓ | Gmail message ID to restore |
| `email_address` | string |  | Email address (use 'me' for authenticated user) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message ID |
| `status` | string | Should be 'restored' |

---

### `gdrive.file.download`

**Description:** Download file from Google Drive

> Downloads a file from Google Drive by its file ID. Returns the file content as base64 encoded string.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_id` | string | ✓ | Google Drive file ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | File ID |
| `file_name` | string | File name |
| `mime_type` | string | File MIME type |
| `size_bytes` | integer | File size |
| `file_content` | string | Base64 encoded content |
| `status` | string | Should be 'downloaded' |

---

### `gdrive.file.list`

**Description:** List files in Google Drive

> Lists files in Google Drive, optionally filtered by folder or query string. Returns file metadata including IDs, names, and sizes.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `folder_id` | string |  | List files in specific folder (root if omitted) |
| `query` | string |  | Drive query string for filtering |
| `max_results` | integer |  | Maximum number of files to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `files` | array | List of file objects with id, name, mimeType, size, timestam |
| `count` | integer | Number of files returned |
| `next_page_token` | string | Token for pagination |

---

### `gdrive.file.metadata`

**Description:** Get file metadata without downloading content

> Retrieves detailed metadata for a file including name, size, type, timestamps, and ownership information. Does not download the file content.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_id` | string | ✓ | Google Drive file ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | File ID |
| `file_name` | string | File name |
| `mime_type` | string | MIME type |
| `size_bytes` | integer | File size |
| `created_time` | string | Creation time |
| `modified_time` | string | Last modified time |
| `web_view_link` | string | View URL |
| `owners` | array | Owner email addresses |

---

### `gdrive.file.upload`

**Description:** Upload file to Google Drive

> Uploads a file to Google Drive. File content must be base64 encoded. Optionally specify a parent folder ID to upload into a specific folder.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_name` | string | ✓ | Name for the uploaded file |
| `file_content` | string | ✓ | Base64 encoded file content |
| `folder_id` | string |  | Parent folder ID (uploads to root if omitted) |
| `mime_type` | string |  | MIME type of the file |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | Google Drive file ID |
| `file_name` | string | Uploaded file name |
| `mime_type` | string | File MIME type |
| `size_bytes` | integer | File size in bytes |
| `created_time` | string | Creation timestamp |
| `web_view_link` | string | URL to view file |
| `status` | string | Should be 'uploaded' |

---

### `gdrive.folder.create`

**Description:** Create a folder in Google Drive

> Creates a new folder in Google Drive. Can be created at root level or as a subfolder under an existing folder.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `folder_name` | string | ✓ | Name for the new folder |
| `parent_folder_id` | string |  | Parent folder ID (creates at root if omitted) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `folder_id` | string | New folder ID |
| `folder_name` | string | Folder name |
| `web_view_link` | string | URL to view folder |
| `status` | string | Should be 'created' |

---

## STRIPE (224 capabilities)

### `stripe.account.create`

**Description:** Create a Connect account

> Creates a new connected account for Stripe Connect. Connected accounts represent your platform's sellers, service providers, or vendors.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | string | ✓ | Account type |
| `country` | string |  | Two-letter country code |
| `email` | string |  | Account email |
| `capabilities` | object |  | Requested capabilities |
| `business_type` | string |  | Business type |
| `business_profile` | object |  | Business details |
| `company` | object |  | Company details (if business) |
| `individual` | object |  | Individual details |
| `tos_acceptance` | object |  | ToS acceptance |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Account ID |
| `type` | string | Account type |
| `email` | string | Email |
| `capabilities` | object | Capabilities |
| `payouts_enabled` | boolean | Can payout |
| `charges_enabled` | boolean | Can charge |

---

### `stripe.account.delete`

**Description:** Delete a Connect account

> Deletes a connected account. Only Custom or Express accounts created by your platform can be deleted.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Account ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted account ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.account.list`

**Description:** List Connect accounts

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `created` | object |  | Filter by created date |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of accounts |
| `has_more` | boolean | More results |

---

### `stripe.account.login_link.create`

**Description:** Create a login link for Express Dashboard

> Creates a single-use login link for an Express connected account to access their Stripe Express Dashboard.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Express account ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Login URL |

---

### `stripe.account.retrieve`

**Description:** Retrieve a Connect account

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Account ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Account ID |
| `type` | string | Type |
| `email` | string | Email |
| `capabilities` | object | Capabilities |
| `payouts_enabled` | boolean | Payouts enabled |
| `charges_enabled` | boolean | Charges enabled |
| `requirements` | object | Requirements |

---

### `stripe.account.update`

**Description:** Update a Connect account

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Account ID to update |
| `email` | string |  | New email |
| `business_profile` | object |  | Update business info |
| `company` | object |  | Update company info |
| `individual` | object |  | Update individual info |
| `capabilities` | object |  | Request/remove capabilities |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Account ID |
| `email` | string | Updated email |

---

### `stripe.account_link.create`

**Description:** Create an account link

> Creates an account link for onboarding a connected account. Links redirect users to Stripe-hosted onboarding pages.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account` | string | ✓ | Connected account ID |
| `type` | string | ✓ | Link type |
| `refresh_url` | string | ✓ | URL if link expires or fails |
| `return_url` | string | ✓ | URL after onboarding completes |
| `collect` | string |  | Info to collect |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Onboarding URL |
| `expires_at` | integer | Link expiration |

---

### `stripe.application_fee.list`

**Description:** List application fees

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `charge` | string |  | Filter by charge ID |
| `created` | object |  | Filter by created date |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of fees |
| `has_more` | boolean | More results |

---

### `stripe.application_fee.retrieve`

**Description:** Retrieve an application fee

> Retrieves an application fee collected on a payment from a connected account.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `fee_id` | string | ✓ | Application fee ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Fee ID |
| `amount` | integer | Fee amount |
| `currency` | string | Currency |
| `charge` | string | Charge ID |
| `account` | string | Connected account |

---

### `stripe.application_fee_refund.create`

**Description:** Refund an application fee

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `fee_id` | string | ✓ | Application fee ID |
| `amount` | integer |  | Amount to refund (partial) |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Refund ID |
| `amount` | integer | Refunded amount |
| `fee` | string | Fee ID |

---

### `stripe.balance.get`

**Description:** Get current Stripe balance

> Retrieves the current account balance, showing available and pending amounts by currency. Use to check how much can be paid out.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `available` | array | Available balance by currency |
| `pending` | array | Pending balance by currency |
| `connect_reserved` | array | Reserved funds for Connect (platform accounts) |
| `livemode` | boolean | Live or test mode |

---

### `stripe.balance.transactions.list`

**Description:** List Stripe balance transactions

> Returns a list of transactions that have contributed to the Stripe account balance. Includes charges, payouts, refunds, transfers, etc.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | string |  | Filter by transaction type |
| `payout` | string |  | Filter by payout ID |
| `source` | string |  | Filter by source ID (charge, refund, etc.) |
| `limit` | integer |  | Maximum number to return (1-100) |
| `created` | object |  | Filter by created date (gte, lte, gt, lt) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of balance transactions |
| `has_more` | boolean | More results |

---

### `stripe.billing_portal.configuration.create`

**Description:** Create a billing portal configuration

> Creates a configuration defining what customers can do in the portal, such as updating subscriptions, payment methods, or viewing invoices.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `business_profile` | object | ✓ | Business info shown in portal |
| `features` | object | ✓ | Portal features configuration |
| `default_return_url` | string |  | Default return URL |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Configuration ID |
| `is_default` | boolean | Is default config |
| `active` | boolean | Is active |
| `features` | object | Features config |

---

### `stripe.billing_portal.configuration.list`

**Description:** List billing portal configurations

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `is_default` | boolean |  | Filter by default status |
| `active` | boolean |  | Filter by active status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of configurations |
| `has_more` | boolean | More results |

---

### `stripe.billing_portal.configuration.retrieve`

**Description:** Retrieve a billing portal configuration

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `configuration_id` | string | ✓ | Configuration ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Configuration ID |
| `is_default` | boolean | Is default |
| `active` | boolean | Is active |
| `business_profile` | object | Business info |
| `features` | object | Features |

---

### `stripe.billing_portal.configuration.update`

**Description:** Update a billing portal configuration

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `configuration_id` | string | ✓ | Configuration ID to update |
| `active` | boolean |  | Activate or deactivate |
| `business_profile` | object |  | Update business info |
| `features` | object |  | Update features |
| `default_return_url` | string |  | Update return URL |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Configuration ID |
| `active` | boolean | Is active |

---

### `stripe.billing_portal.session.create`

**Description:** Create a billing portal session

> Creates a portal session for a customer to manage their subscription, update payment methods, and view invoices in a self-service interface.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string | ✓ | Customer ID |
| `return_url` | string |  | URL to return to after portal |
| `configuration` | string |  | Portal configuration ID |
| `flow_data` | object |  | Start portal in specific flow |
| `locale` | string |  | Portal language |
| `on_behalf_of` | string |  | Connected account (for Connect) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Portal session ID |
| `url` | string | Portal URL |
| `return_url` | string | Return URL |
| `customer` | string | Customer ID |
| `configuration` | string | Config ID |

---

### `stripe.charge.list`

**Description:** List charges in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string |  | Filter by customer ID |
| `payment_intent` | string |  | Filter by payment intent ID |
| `limit` | integer |  | Maximum number to return (1-100) |
| `created` | object |  | Filter by created date (gte, lte, gt, lt) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of charge objects |
| `has_more` | boolean | More results available |

---

### `stripe.charge.retrieve`

**Description:** Retrieve a charge in Stripe

> Retrieves the details of a charge. Charges are created when a PaymentIntent is confirmed and payment is attempted.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `charge_id` | string | ✓ | Charge ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Charge ID |
| `status` | string | Charge status |
| `amount` | integer | Amount in cents |
| `amount_refunded` | integer | Amount refunded |
| `currency` | string | Currency code |
| `customer` | string | Customer ID |
| `payment_intent` | string | PaymentIntent ID |
| `refunded` | boolean | Fully refunded |
| `receipt_url` | string | Receipt URL |

---

### `stripe.checkout.lineitems.list`

**Description:** List line items for a Checkout Session

> Retrieves the line items for a Checkout Session. Line items show what the customer purchased or will purchase.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | ✓ | Checkout Session ID |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of line items with price, quantity, amount |
| `has_more` | boolean | More results |

---

### `stripe.checkout.session.create`

**Description:** Create a Checkout Session in Stripe

> Creates a Checkout Session for collecting payment. Stripe Checkout is a pre-built, hosted payment page that handles card input, validation, and 3D Secure authentication. Supports one-time and subscription payments.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `mode` | string | ✓ | Checkout mode |
| `success_url` | string | ✓ | URL to redirect after successful payment |
| `cancel_url` | string |  | URL to redirect if customer cancels |
| `line_items` | array |  | Line items for the checkout (price or price_data) |
| `customer` | string |  | Existing customer ID |
| `customer_email` | string |  | Pre-fill customer email |
| `client_reference_id` | string |  | Your reference ID for this session |
| `metadata` | object |  | Key-value pairs for your own use |
| `payment_method_types` | array |  | Allowed payment methods |
| `allow_promotion_codes` | boolean |  | Allow promotion codes |
| `billing_address_collection` | string |  | Collect billing address |
| `shipping_address_collection` | object |  | Collect shipping address (allowed_countries) |
| `expires_at` | integer |  | Unix timestamp when session expires |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Checkout Session ID |
| `url` | string | Checkout page URL to redirect customer |
| `status` | string | Session status (open, complete, expired) |
| `payment_status` | string | Payment status (unpaid, paid, no_payment_required) |
| `customer` | string | Customer ID if created |
| `payment_intent` | string | PaymentIntent ID |
| `subscription` | string | Subscription ID if mode=subscription |

**Example:**
```json
{
  "capability": "stripe.checkout.session.create",
  "params": {
    "mode": "payment",
    "success_url": "https://example.com/success",
    "cancel_url": "https://example.com/cancel",
    "line_items": [
      {
        "price": "price_ABC123",
        "quantity": 1
      }
    ]
  }
}
```

---

### `stripe.checkout.session.expire`

**Description:** Expire a Checkout Session in Stripe

> Expires an open Checkout Session, preventing it from being completed. Useful for invalidating sessions that are no longer valid.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | ✓ | Checkout Session ID to expire |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session ID |
| `status` | string | Should be 'expired' |

---

### `stripe.checkout.session.list`

**Description:** List Checkout Sessions in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string |  | Filter by customer ID |
| `payment_intent` | string |  | Filter by payment intent ID |
| `subscription` | string |  | Filter by subscription ID |
| `limit` | integer |  | Maximum number to return (1-100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of sessions |
| `has_more` | boolean | More results available |

---

### `stripe.checkout.session.retrieve`

**Description:** Retrieve a Checkout Session in Stripe

> Retrieves a Checkout Session. Use to verify payment completion after customer returns from the hosted checkout page.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | ✓ | Checkout Session ID |
| `expand` | array |  | Objects to expand (e.g., line_items, customer) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session ID |
| `status` | string | Session status |
| `payment_status` | string | Payment status |
| `customer` | string | Customer ID |
| `customer_email` | string | Customer email |
| `amount_total` | integer | Total in cents |
| `currency` | string | Currency |
| `payment_intent` | string | PaymentIntent ID |
| `subscription` | string | Subscription ID |
| `metadata` | object | Metadata |

---

### `stripe.coupon.create`

**Description:** Create a coupon in Stripe

> Creates a coupon that can be applied to customers, subscriptions, or invoices to provide a discount.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `percent_off` | number |  | Percentage discount (1-100) |
| `amount_off` | integer |  | Fixed amount discount in cents |
| `currency` | string |  | Currency (required if amount_off) |
| `duration` | string | ✓ | How long the discount applies |
| `duration_in_months` | integer |  | Months for repeating duration |
| `id` | string |  | Unique coupon code |
| `name` | string |  | Display name |
| `max_redemptions` | integer |  | Maximum redemption count |
| `redeem_by` | integer |  | Unix timestamp redemption deadline |
| `applies_to` | object |  | Product restrictions |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Coupon ID/code |
| `percent_off` | number | Percent off |
| `amount_off` | integer | Amount off |
| `duration` | string | Duration |
| `valid` | boolean | Is valid |
| `times_redeemed` | integer | Redemptions |

---

### `stripe.coupon.delete`

**Description:** Delete a coupon

> Deletes a coupon. Existing discounts using the coupon remain valid.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `coupon_id` | string | ✓ | Coupon ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted coupon ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.coupon.list`

**Description:** List coupons

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of coupons |
| `has_more` | boolean | More results |

---

### `stripe.coupon.retrieve`

**Description:** Retrieve a coupon

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `coupon_id` | string | ✓ | Coupon ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Coupon ID |
| `percent_off` | number | Percent off |
| `amount_off` | integer | Amount off |
| `duration` | string | Duration |
| `valid` | boolean | Is valid |

---

### `stripe.coupon.update`

**Description:** Update a coupon

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `coupon_id` | string | ✓ | Coupon ID to update |
| `name` | string |  | New display name |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Coupon ID |
| `name` | string | Updated name |

---

### `stripe.credit_note.create`

**Description:** Create a credit note

> Creates a credit note for an invoice. Credit notes reduce the amount owed and can refund customers or create account credit.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice` | string | ✓ | Invoice ID to credit |
| `lines` | array |  | Line items to credit |
| `amount` | integer |  | Total credit amount |
| `credit_amount` | integer |  | Amount to add as customer credit |
| `refund_amount` | integer |  | Amount to refund |
| `out_of_band_amount` | integer |  | Amount refunded outside Stripe |
| `reason` | string |  | Reason for credit |
| `memo` | string |  | Internal memo |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Credit note ID |
| `invoice` | string | Invoice ID |
| `amount` | integer | Total credit |
| `status` | string | Status |

---

### `stripe.credit_note.list`

**Description:** List credit notes

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice` | string |  | Filter by invoice |
| `customer` | string |  | Filter by customer |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of credit notes |
| `has_more` | boolean | More results |

---

### `stripe.credit_note.retrieve`

**Description:** Retrieve a credit note

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `credit_note_id` | string | ✓ | Credit note ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Credit note ID |
| `invoice` | string | Invoice |
| `amount` | integer | Amount |
| `status` | string | Status |
| `lines` | object | Line items |

---

### `stripe.credit_note.update`

**Description:** Update a credit note

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `credit_note_id` | string | ✓ | Credit note ID to update |
| `memo` | string |  | Update memo |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Credit note ID |
| `memo` | string | Updated memo |

---

### `stripe.credit_note.void`

**Description:** Void a credit note

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `credit_note_id` | string | ✓ | Credit note ID to void |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Credit note ID |
| `status` | string | Should be void |

---

### `stripe.customer.create`

**Description:** Create a customer in Stripe

> Creates a new customer object in Stripe. Customers allow you to perform recurring charges, save payment methods, and track payments. Creating a customer is often the first step before taking payments.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string |  | Customer's email address |
| `name` | string |  | Customer's full name |
| `phone` | string |  | Customer's phone number |
| `description` | string |  | Internal description for this customer |
| `metadata` | object |  | Key-value pairs for your own use |
| `address` | object |  | Customer's address |
| `payment_method` | string |  | Payment method to attach to customer |
| `invoice_settings` | object |  | Invoice settings (default_payment_method, etc.) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Customer ID |
| `email` | string | Email address |
| `name` | string | Customer name |
| `created` | integer | Unix timestamp |
| `default_source` | string | Default payment source |

**Example:**
```json
{
  "capability": "stripe.customer.create",
  "params": {
    "email": "john@example.com",
    "name": "John Doe",
    "metadata": {
      "user_id": "usr_123"
    }
  }
}
```

---

### `stripe.customer.delete`

**Description:** Delete a customer in Stripe

> Permanently deletes a customer and cancels any active subscriptions. This cannot be undone. Also immediately cancels any active subscriptions.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted customer ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.customer.list`

**Description:** List customers in Stripe

> Returns a list of customers in reverse chronological order.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string |  | Filter by email address |
| `limit` | integer |  | Maximum number to return (1-100) |
| `starting_after` | string |  | Cursor for pagination (customer ID) |
| `ending_before` | string |  | Cursor for pagination (customer ID) |
| `created` | object |  | Filter by created date (gte, lte, gt, lt) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of customer objects |
| `has_more` | boolean | More results available |
| `url` | string | API endpoint URL |

---

### `stripe.customer.retrieve`

**Description:** Retrieve a customer in Stripe

> Retrieves the details of an existing customer by ID.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Customer ID |
| `email` | string | Email address |
| `name` | string | Customer name |
| `phone` | string | Phone number |
| `address` | object | Address object |
| `metadata` | object | Metadata |
| `default_source` | string | Default payment source |
| `invoice_settings` | object | Invoice settings |
| `created` | integer | Unix timestamp |

---

### `stripe.customer.search`

**Description:** Search customers in Stripe

> Search for customers using Stripe's Search API. Supports searching by email, name, phone, metadata, and more using query syntax.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ | Search query string |
| `limit` | integer |  | Maximum number to return (1-100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of matching customers |
| `has_more` | boolean | More results available |
| `total_count` | integer | Total matches |

---

### `stripe.customer.tax_id.create`

**Description:** Add a tax ID to a customer

> Creates a tax ID for a customer. Tax IDs are used for tax compliance and appear on invoices.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `type` | string | ✓ | Type of tax ID |
| `value` | string | ✓ | Tax ID value |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Tax ID object ID |
| `type` | string | Tax ID type |
| `value` | string | Tax ID value |
| `verification` | object | Verification status |

---

### `stripe.customer.tax_id.delete`

**Description:** Delete a customer tax ID

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `tax_id` | string | ✓ | Tax ID object ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted tax ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.customer.tax_id.list`

**Description:** List customer tax IDs

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of tax IDs |
| `has_more` | boolean | More results |

---

### `stripe.customer.tax_id.retrieve`

**Description:** Retrieve a customer tax ID

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID |
| `tax_id` | string | ✓ | Tax ID object ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Tax ID object ID |
| `type` | string | Type |
| `value` | string | Value |
| `verification` | object | Verification |

---

### `stripe.customer.update`

**Description:** Update a customer in Stripe

> Updates the specified customer by setting parameter values.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Customer ID to update |
| `email` | string |  | New email address |
| `name` | string |  | New name |
| `phone` | string |  | New phone number |
| `description` | string |  | New description |
| `metadata` | object |  | Updated metadata (merged with existing) |
| `address` | object |  | Updated address |
| `default_source` | string |  | New default payment source |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Customer ID |
| `email` | string | Updated email |
| `name` | string | Updated name |

---

### `stripe.dispute.close`

**Description:** Close a dispute in Stripe

> Closes a dispute, accepting the customer's claim. This action cannot be undone and the disputed amount will be returned to the customer.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dispute_id` | string | ✓ | Dispute ID to close |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dispute ID |
| `status` | string | Should be 'lost' |

---

### `stripe.dispute.list`

**Description:** List disputes in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `charge` | string |  | Filter by charge ID |
| `payment_intent` | string |  | Filter by payment intent ID |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of disputes |
| `has_more` | boolean | More results |

---

### `stripe.dispute.retrieve`

**Description:** Retrieve a dispute in Stripe

> Retrieves a dispute (chargeback) initiated by a customer's bank. Disputes require evidence submission to challenge.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dispute_id` | string | ✓ | Dispute ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dispute ID |
| `status` | string | Dispute status (warning_needs_response, needs_response, etc. |
| `amount` | integer | Disputed amount |
| `currency` | string | Currency |
| `charge` | string | Related charge ID |
| `reason` | string | Dispute reason |
| `evidence_due_by` | integer | Evidence deadline |

---

### `stripe.dispute.update`

**Description:** Update a dispute with evidence in Stripe

> Updates a dispute with evidence to challenge it. You can submit various types of evidence to support your case.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dispute_id` | string | ✓ | Dispute ID to update |
| `evidence` | object |  | Evidence to submit |
| `submit` | boolean |  | Submit evidence for review (cannot be undone) |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dispute ID |
| `status` | string | Updated status |
| `evidence` | object | Submitted evidence |

---

### `stripe.event.list`

**Description:** List Stripe events

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | string |  | Filter by event type |
| `created` | object |  | Filter by created date (gte, lte) |
| `delivery_success` | boolean |  | Filter by delivery status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of events |
| `has_more` | boolean | More results |

---

### `stripe.event.retrieve`

**Description:** Retrieve a Stripe event

> Retrieves the details of an event. Events are created when something interesting happens in your account (payment succeeds, subscription renews, etc).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `event_id` | string | ✓ | Event ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Event ID |
| `type` | string | Event type |
| `data` | object | Event data object |
| `created` | integer | Unix timestamp |
| `livemode` | boolean | Live or test |

---

### `stripe.file.create`

**Description:** Upload a file to Stripe

> Uploads a file to Stripe for use in disputes, identity verification, or account onboarding.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | string | ✓ | File contents (base64 encoded) |
| `purpose` | string | ✓ | Purpose of the file |
| `file_link_data` | object |  | Create a file link |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | File ID |
| `purpose` | string | File purpose |
| `size` | integer | Size in bytes |
| `type` | string | MIME type |
| `url` | string | Download URL |

---

### `stripe.file.list`

**Description:** List files

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `purpose` | string |  | Filter by purpose |
| `created` | object |  | Filter by created date |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of files |
| `has_more` | boolean | More results |

---

### `stripe.file.retrieve`

**Description:** Retrieve a file

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_id` | string | ✓ | File ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | File ID |
| `purpose` | string | Purpose |
| `size` | integer | Size |
| `type` | string | MIME type |
| `url` | string | URL |

---

### `stripe.file_link.create`

**Description:** Create a file link

> Creates a shareable link for a file that can be accessed without authentication for a limited time.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | string | ✓ | File ID to link |
| `expires_at` | integer |  | Link expiration timestamp |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | File link ID |
| `file` | string | File ID |
| `url` | string | Shareable URL |
| `expires_at` | integer | Expiration |

---

### `stripe.file_link.list`

**Description:** List file links

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | string |  | Filter by file ID |
| `expired` | boolean |  | Filter by expired status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of file links |
| `has_more` | boolean | More results |

---

### `stripe.file_link.retrieve`

**Description:** Retrieve a file link

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_link_id` | string | ✓ | File link ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | File link ID |
| `file` | string | File ID |
| `url` | string | URL |
| `expired` | boolean | Is expired |

---

### `stripe.file_link.update`

**Description:** Update a file link

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_link_id` | string | ✓ | File link ID to update |
| `expires_at` | string |  | New expiration ('now' to expire) |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | File link ID |
| `expired` | boolean | Is expired |

---

### `stripe.financial_connections.account.disconnect`

**Description:** Disconnect a financial account

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Financial account ID to disconnect |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Account ID |
| `status` | string | Should be disconnected |

---

### `stripe.financial_connections.account.list`

**Description:** List linked financial accounts

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_holder` | object |  | Filter by account holder |
| `session` | string |  | Filter by session ID |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of accounts |
| `has_more` | boolean | More results |

---

### `stripe.financial_connections.account.owners.list`

**Description:** List account owners

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Financial account ID |
| `ownership` | string | ✓ | Ownership object ID |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of owners |
| `has_more` | boolean | More results |

---

### `stripe.financial_connections.account.refresh`

**Description:** Refresh financial account data

> Refreshes the data for a linked account including balance and transaction information.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Financial account ID |
| `features` | array | ✓ | Data to refresh |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Account ID |
| `balance_refresh` | object | Balance refresh |

---

### `stripe.financial_connections.account.retrieve`

**Description:** Retrieve a linked financial account

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Financial account ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Account ID |
| `institution_name` | string | Bank name |
| `last4` | string | Last 4 digits |
| `display_name` | string | Account name |
| `status` | string | Connection status |
| `balance` | object | Account balance |
| `ownership` | object | Ownership info |

---

### `stripe.financial_connections.session.create`

**Description:** Create a Financial Connections session

> Creates a session for a customer to connect their bank account. The session provides a secure interface for account linking.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_holder` | object | ✓ | Account holder info |
| `permissions` | array | ✓ | Permissions to request |
| `filters` | object |  | Account filters |
| `return_url` | string |  | URL to return to after linking |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session ID |
| `client_secret` | string | Client secret |
| `accounts` | array | Linked accounts |

---

### `stripe.financial_connections.session.retrieve`

**Description:** Retrieve a Financial Connections session

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | ✓ | Session ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session ID |
| `accounts` | array | Linked accounts |
| `permissions` | array | Permissions |

---

### `stripe.financial_connections.transaction.list`

**Description:** List financial transactions

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account` | string | ✓ | Financial account ID |
| `transacted_at` | object |  | Filter by transaction date |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of transactions |
| `has_more` | boolean | More results |

---

### `stripe.financial_connections.transaction.retrieve`

**Description:** Retrieve a financial transaction

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `transaction_id` | string | ✓ | Transaction ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transaction ID |
| `account` | string | Account ID |
| `amount` | integer | Amount in cents |
| `currency` | string | Currency |
| `description` | string | Description |
| `status` | string | Status |
| `transacted_at` | integer | Timestamp |

---

### `stripe.identity.verification_report.list`

**Description:** List Identity verification reports

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `verification_session` | string |  | Filter by session ID |
| `type` | string |  | Filter by type |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of reports |
| `has_more` | boolean | More results |

---

### `stripe.identity.verification_report.retrieve`

**Description:** Retrieve an Identity verification report

> Retrieves a VerificationReport containing the results of identity verification including document data and selfie match results.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `report_id` | string | ✓ | Verification report ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Report ID |
| `type` | string | Report type |
| `verification_session` | string | Session ID |
| `document` | object | Document data |
| `selfie` | object | Selfie check results |
| `id_number` | object | ID number data |

---

### `stripe.identity.verification_session.cancel`

**Description:** Cancel an Identity verification session

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | ✓ | Session ID to cancel |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session ID |
| `status` | string | Should be canceled |

---

### `stripe.identity.verification_session.create`

**Description:** Create an Identity verification session

> Creates a VerificationSession for collecting and verifying identity documents. Sessions guide users through document capture and selfie verification using Stripe's hosted UI or embedded SDK.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | string | ✓ | Type of verification |
| `options` | object |  | Verification options |
| `return_url` | string |  | URL to redirect after verification |
| `metadata` | object |  | Key-value pairs for your use |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Verification session ID |
| `status` | string | Session status |
| `url` | string | Hosted verification URL |
| `client_secret` | string | Client secret |
| `type` | string | Verification type |

---

### `stripe.identity.verification_session.list`

**Description:** List Identity verification sessions

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of sessions |
| `has_more` | boolean | More results |

---

### `stripe.identity.verification_session.redact`

**Description:** Redact an Identity verification session

> Redacts a VerificationSession to remove all collected identity data. Use for GDPR compliance or when data is no longer needed.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | ✓ | Session ID to redact |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session ID |
| `status` | string | Should be redacted |

---

### `stripe.identity.verification_session.retrieve`

**Description:** Retrieve an Identity verification session

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | ✓ | Verification session ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session ID |
| `status` | string | Status |
| `type` | string | Type |
| `verified_outputs` | object | Outputs |
| `last_error` | object | Last error |
| `last_verification_report` | string | Report |

---

### `stripe.identity.verification_session.update`

**Description:** Update an Identity verification session

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | ✓ | Session ID to update |
| `type` | string |  | New verification type |
| `options` | object |  | Updated options |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Session ID |
| `status` | string | Status |

---

### `stripe.invoice.create`

**Description:** Create an invoice in Stripe

> Creates a draft invoice for a customer. Invoices are automatically created for subscriptions, but you can also create one-off invoices manually.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string | ✓ | Customer ID |
| `auto_advance` | boolean |  | Auto-finalize and send invoice |
| `collection_method` | string |  | How to collect payment |
| `days_until_due` | integer |  | Days until payment is due (if send_invoice) |
| `description` | string |  | Invoice description |
| `metadata` | object |  | Key-value pairs for your own use |
| `default_payment_method` | string |  | Payment method for this invoice |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Invoice ID |
| `status` | string | Invoice status (draft, open, paid, etc.) |
| `customer` | string | Customer ID |
| `amount_due` | integer | Amount due in cents |
| `currency` | string | Currency code |
| `hosted_invoice_url` | string | Payment page URL |

---

### `stripe.invoice.delete`

**Description:** Delete a draft invoice in Stripe

> Permanently deletes a draft invoice. Only draft invoices can be deleted.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted invoice ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.invoice.finalize`

**Description:** Finalize an invoice in Stripe

> Finalizes a draft invoice, transitioning it to 'open' status. Finalized invoices can no longer be edited and are ready for payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to finalize |
| `auto_advance` | boolean |  | Auto-advance to next status |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Invoice ID |
| `status` | string | Should be 'open' |
| `hosted_invoice_url` | string | Payment URL |

---

### `stripe.invoice.list`

**Description:** List invoices in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string |  | Filter by customer ID |
| `subscription` | string |  | Filter by subscription ID |
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return (1-100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of invoices |
| `has_more` | boolean | More results available |

---

### `stripe.invoice.pay`

**Description:** Pay an invoice in Stripe

> Attempts to pay an open invoice using the customer's default payment method or a specified payment method.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to pay |
| `payment_method` | string |  | Payment method to use (uses default if not specified) |
| `source` | string |  | Card source to use (deprecated, use payment_method) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Invoice ID |
| `status` | string | Should be 'paid' |
| `amount_paid` | integer | Amount paid |
| `payment_intent` | string | PaymentIntent ID |

---

### `stripe.invoice.retrieve`

**Description:** Retrieve an invoice in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Invoice ID |
| `status` | string | Invoice status |
| `customer` | string | Customer ID |
| `amount_due` | integer | Amount due |
| `amount_paid` | integer | Amount paid |
| `amount_remaining` | integer | Amount remaining |
| `currency` | string | Currency |
| `due_date` | integer | Due date timestamp |
| `hosted_invoice_url` | string | Payment URL |
| `invoice_pdf` | string | PDF download URL |
| `lines` | object | Invoice line items |

---

### `stripe.invoice.send`

**Description:** Send an invoice in Stripe

> Sends an open invoice to the customer via email. The invoice must be finalized before it can be sent.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to send |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Invoice ID |
| `status` | string | Status |
| `hosted_invoice_url` | string | Payment URL |

---

### `stripe.invoice.update`

**Description:** Update an invoice in Stripe

> Updates a draft invoice. Cannot update finalized invoices.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to update |
| `description` | string |  | Update description |
| `metadata` | object |  | Update metadata |
| `days_until_due` | integer |  | Update days until due |
| `default_payment_method` | string |  | Update payment method |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Invoice ID |
| `status` | string | Status |

---

### `stripe.invoice.void`

**Description:** Void an invoice in Stripe

> Voids an open invoice. Voided invoices cannot be paid and are marked as void.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Invoice ID to void |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Invoice ID |
| `status` | string | Should be 'void' |

---

### `stripe.issuing.authorization.approve`

**Description:** Approve an Issuing authorization

> Approves a pending authorization. Only works for real-time authorizations when you have real-time authorization controls enabled.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `authorization_id` | string | ✓ | Authorization ID to approve |
| `amount` | integer |  | Approved amount (partial approval) |
| `metadata` | object |  | Metadata to attach |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Authorization ID |
| `approved` | boolean | Should be true |
| `status` | string | Updated status |

---

### `stripe.issuing.authorization.decline`

**Description:** Decline an Issuing authorization

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `authorization_id` | string | ✓ | Authorization ID to decline |
| `metadata` | object |  | Metadata to attach |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Authorization ID |
| `approved` | boolean | Should be false |
| `status` | string | Updated status |

---

### `stripe.issuing.authorization.list`

**Description:** List Issuing authorizations

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `card` | string |  | Filter by card ID |
| `cardholder` | string |  | Filter by cardholder ID |
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of authorizations |
| `has_more` | boolean | More results |

---

### `stripe.issuing.authorization.retrieve`

**Description:** Retrieve an Issuing authorization

> Retrieves an authorization representing a request to authorize a purchase on an Issuing card.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `authorization_id` | string | ✓ | Authorization ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Authorization ID |
| `card` | string | Card ID |
| `cardholder` | string | Cardholder ID |
| `amount` | integer | Amount in cents |
| `currency` | string | Currency |
| `status` | string | Authorization status |
| `approved` | boolean | Was approved |
| `merchant_data` | object | Merchant info |

---

### `stripe.issuing.authorization.update`

**Description:** Update an Issuing authorization

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `authorization_id` | string | ✓ | Authorization ID to update |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Authorization ID |
| `metadata` | object | Updated metadata |

---

### `stripe.issuing.card.create`

**Description:** Create an Issuing card

> Creates a new Issuing card for a cardholder. Cards can be physical or virtual. Physical cards are shipped to the cardholder's address.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cardholder` | string | ✓ | Cardholder ID |
| `currency` | string | ✓ | Three-letter ISO currency code |
| `type` | string | ✓ | Card type |
| `status` | string |  | Initial card status |
| `spending_controls` | object |  | Spending limits and restrictions |
| `shipping` | object |  | Shipping details for physical cards |
| `metadata` | object |  | Key-value pairs for your use |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Card ID |
| `cardholder` | string | Cardholder ID |
| `type` | string | Card type |
| `status` | string | Card status |
| `last4` | string | Last 4 digits |
| `exp_month` | integer | Expiry month |
| `exp_year` | integer | Expiry year |
| `brand` | string | Card brand |

---

### `stripe.issuing.card.list`

**Description:** List Issuing cards

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cardholder` | string |  | Filter by cardholder ID |
| `status` | string |  | Filter by status |
| `type` | string |  | Filter by type |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of cards |
| `has_more` | boolean | More results |

---

### `stripe.issuing.card.retrieve`

**Description:** Retrieve an Issuing card

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `card_id` | string | ✓ | Card ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Card ID |
| `cardholder` | string | Cardholder ID |
| `type` | string | Card type |
| `status` | string | Status |
| `last4` | string | Last 4 digits |
| `spending_controls` | object | Limits |

---

### `stripe.issuing.card.update`

**Description:** Update an Issuing card

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `card_id` | string | ✓ | Card ID to update |
| `status` | string |  | New status |
| `spending_controls` | object |  | Updated spending limits |
| `cancellation_reason` | string |  | Reason if canceling |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Card ID |
| `status` | string | Updated status |

---

### `stripe.issuing.cardholder.create`

**Description:** Create an Issuing cardholder

> Creates a new Issuing cardholder. Cardholders represent individuals or businesses that can be issued cards.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | ✓ | Full name |
| `email` | string | ✓ | Email address |
| `phone_number` | string |  | Phone number |
| `type` | string | ✓ | Cardholder type |
| `billing` | object | ✓ | Billing address |
| `individual` | object |  | Individual details (if type is individual) |
| `company` | object |  | Company details (if type is company) |
| `spending_controls` | object |  | Default spending limits for cards |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Cardholder ID |
| `name` | string | Name |
| `email` | string | Email |
| `status` | string | Status |
| `type` | string | Type |

---

### `stripe.issuing.cardholder.list`

**Description:** List Issuing cardholders

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string |  | Filter by email |
| `status` | string |  | Filter by status |
| `type` | string |  | Filter by type |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of cardholders |
| `has_more` | boolean | More results |

---

### `stripe.issuing.cardholder.retrieve`

**Description:** Retrieve an Issuing cardholder

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cardholder_id` | string | ✓ | Cardholder ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Cardholder ID |
| `name` | string | Name |
| `email` | string | Email |
| `status` | string | Status |
| `type` | string | Type |
| `billing` | object | Billing address |

---

### `stripe.issuing.cardholder.update`

**Description:** Update an Issuing cardholder

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cardholder_id` | string | ✓ | Cardholder ID to update |
| `email` | string |  | New email |
| `phone_number` | string |  | New phone |
| `billing` | object |  | Updated billing address |
| `spending_controls` | object |  | Updated spending limits |
| `status` | string |  | New status |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Cardholder ID |
| `status` | string | Updated status |

---

### `stripe.issuing.dispute.create`

**Description:** Create an Issuing dispute

> Creates a dispute for an Issuing transaction. Use when a cardholder disputes a charge on their Issuing card.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `transaction` | string | ✓ | Transaction ID to dispute |
| `evidence` | object |  | Evidence supporting the dispute |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dispute ID |
| `transaction` | string | Transaction ID |
| `status` | string | Dispute status |
| `amount` | integer | Disputed amount |

---

### `stripe.issuing.dispute.list`

**Description:** List Issuing disputes

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `transaction` | string |  | Filter by transaction ID |
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of disputes |
| `has_more` | boolean | More results |

---

### `stripe.issuing.dispute.retrieve`

**Description:** Retrieve an Issuing dispute

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dispute_id` | string | ✓ | Dispute ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dispute ID |
| `transaction` | string | Transaction ID |
| `status` | string | Status |
| `evidence` | object | Evidence |

---

### `stripe.issuing.dispute.submit`

**Description:** Submit an Issuing dispute for review

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dispute_id` | string | ✓ | Dispute ID to submit |
| `metadata` | object |  | Metadata to attach |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dispute ID |
| `status` | string | Should be submitted |

---

### `stripe.issuing.dispute.update`

**Description:** Update an Issuing dispute

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dispute_id` | string | ✓ | Dispute ID to update |
| `evidence` | object |  | Updated evidence |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dispute ID |
| `status` | string | Status |

---

### `stripe.issuing.transaction.list`

**Description:** List Issuing transactions

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `card` | string |  | Filter by card ID |
| `cardholder` | string |  | Filter by cardholder ID |
| `type` | string |  | Filter by type |
| `created` | object |  | Filter by created date |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of transactions |
| `has_more` | boolean | More results |

---

### `stripe.issuing.transaction.retrieve`

**Description:** Retrieve an Issuing transaction

> Retrieves a transaction representing a completed purchase on an Issuing card.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `transaction_id` | string | ✓ | Transaction ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transaction ID |
| `card` | string | Card ID |
| `cardholder` | string | Cardholder ID |
| `amount` | integer | Amount in cents |
| `currency` | string | Currency |
| `type` | string | Transaction type |
| `merchant_data` | object | Merchant info |
| `authorization` | string | Auth ID |

---

### `stripe.issuing.transaction.update`

**Description:** Update an Issuing transaction

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `transaction_id` | string | ✓ | Transaction ID to update |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transaction ID |
| `metadata` | object | Updated metadata |

---

### `stripe.payment.create`

**Description:** Create a payment intent in Stripe

> Creates a PaymentIntent object to represent your intent to collect payment. PaymentIntents track the lifecycle of a payment from creation through checkout. Use for one-time payments; for recurring, use subscriptions instead.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `amount` | integer | ✓ | Amount in smallest currency unit (cents for USD) |
| `currency` | string | ✓ | Three-letter ISO currency code (lowercase) |
| `customer` | string |  | Stripe customer ID to associate with payment |
| `payment_method` | string |  | Payment method ID to use |
| `description` | string |  | Description for the payment (appears in dashboard) |
| `metadata` | object |  | Key-value pairs for your own use |
| `confirm` | boolean |  | Immediately confirm and attempt payment |
| `automatic_payment_methods` | object |  | Enable automatic payment method selection |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | PaymentIntent ID |
| `status` | string | Payment status |
| `amount` | integer | Amount in cents |
| `currency` | string | Currency code |
| `client_secret` | string | Client secret for frontend confirmation |

**Example:**
```json
{
  "capability": "stripe.payment.create",
  "params": {
    "amount": 2000,
    "currency": "usd",
    "description": "Order #12345"
  }
}
```

---

### `stripe.payment.refund`

**Description:** Refund a payment in Stripe

> Creates a refund for a PaymentIntent or Charge. You can refund the full amount or a partial amount. Refunds are processed immediately but may take 5-10 business days to appear on customer's statement.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_intent` | string |  | PaymentIntent ID to refund |
| `charge` | string |  | Charge ID to refund (alternative to payment_intent) |
| `amount` | integer |  | Amount to refund in cents (defaults to full amount) |
| `reason` | string |  | Reason for refund |
| `metadata` | object |  | Key-value pairs for your own use |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Refund ID |
| `status` | string | Refund status (succeeded, pending, failed) |
| `amount` | integer | Refund amount in cents |
| `charge` | string | Associated charge ID |
| `payment_intent` | string | Associated PI ID |

---

### `stripe.payment.retrieve`

**Description:** Retrieve a payment intent in Stripe

> Retrieves the details of a PaymentIntent that was previously created. Use to check payment status or get details for reconciliation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_intent_id` | string | ✓ | PaymentIntent ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | PaymentIntent ID |
| `status` | string | Payment status (requires_payment_method, succeeded, etc.) |
| `amount` | integer | Amount in cents |
| `amount_received` | integer | Amount actually received |
| `currency` | string | Currency code |
| `customer` | string | Customer ID if set |
| `charges` | object | Associated charges |

---

### `stripe.payment_link.create`

**Description:** Create a Payment Link

> Creates a shareable payment link for no-code payment collection. Customers can pay by visiting the URL without needing a website.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `line_items` | array | ✓ | Items to sell |
| `after_completion` | object |  | Post-payment behavior |
| `allow_promotion_codes` | boolean |  | Allow promo codes |
| `billing_address_collection` | string |  | Collect billing address |
| `shipping_address_collection` | object |  | Collect shipping address |
| `customer_creation` | string |  | When to create customer |
| `payment_method_types` | array |  | Allowed payment methods |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payment link ID |
| `url` | string | Shareable URL |
| `active` | boolean | Is active |
| `line_items` | object | Items |

---

### `stripe.payment_link.line_items.list`

**Description:** List line items for a Payment Link

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_link_id` | string | ✓ | Payment link ID |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Line items |
| `has_more` | boolean | More results |

---

### `stripe.payment_link.list`

**Description:** List Payment Links

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `active` | boolean |  | Filter by active status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of payment links |
| `has_more` | boolean | More results |

---

### `stripe.payment_link.retrieve`

**Description:** Retrieve a Payment Link

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_link_id` | string | ✓ | Payment link ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payment link ID |
| `url` | string | URL |
| `active` | boolean | Is active |
| `line_items` | object | Items |

---

### `stripe.payment_link.update`

**Description:** Update a Payment Link

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_link_id` | string | ✓ | Payment link ID to update |
| `active` | boolean |  | Activate or deactivate |
| `line_items` | array |  | Update line items |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payment link ID |
| `active` | boolean | Is active |

---

### `stripe.paymentmethod.attach`

**Description:** Attach a payment method to a customer

> Attaches a PaymentMethod to a Customer. This allows the payment method to be reused for future payments.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_method_id` | string | ✓ | PaymentMethod ID to attach |
| `customer` | string | ✓ | Customer ID to attach to |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | PaymentMethod ID |
| `customer` | string | Customer ID |

---

### `stripe.paymentmethod.create`

**Description:** Create a payment method in Stripe

> Creates a PaymentMethod object. PaymentMethods represent your customer's payment instruments. They can be attached to customers for future payments.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | string | ✓ | Type of payment method |
| `card` | object |  | Card details (number, exp_month, exp_year, cvc) |
| `billing_details` | object |  | Billing details (name, email, phone, address) |
| `metadata` | object |  | Key-value pairs for your own use |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | PaymentMethod ID |
| `type` | string | Payment method type |
| `card` | object | Card details (last4, brand, etc.) |
| `billing_details` | object | Billing info |
| `created` | integer | Unix timestamp |

---

### `stripe.paymentmethod.detach`

**Description:** Detach a payment method from a customer

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_method_id` | string | ✓ | PaymentMethod ID to detach |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | PaymentMethod ID |
| `customer` | string | Should be null |

---

### `stripe.paymentmethod.list`

**Description:** List payment methods for a customer

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string | ✓ | Customer ID |
| `type` | string | ✓ | Filter by payment method type |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of payment methods |
| `has_more` | boolean | More results |

---

### `stripe.paymentmethod.retrieve`

**Description:** Retrieve a payment method in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_method_id` | string | ✓ | PaymentMethod ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | PaymentMethod ID |
| `type` | string | Type |
| `card` | object | Card details |
| `customer` | string | Attached customer |

---

### `stripe.paymentmethod.update`

**Description:** Update a payment method in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_method_id` | string | ✓ | PaymentMethod ID to update |
| `billing_details` | object |  | Updated billing details |
| `card` | object |  | Update card details (exp_month, exp_year only) |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | PaymentMethod ID |
| `billing_details` | object | Updated billing |

---

### `stripe.payout.list`

**Description:** List Stripe payouts

> Returns a list of payouts to your bank account. Payouts are the movement of funds from Stripe to your external account.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Filter by payout status |
| `arrival_date` | object |  | Filter by arrival date (gte, lte) |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of payouts |
| `has_more` | boolean | More results |

---

### `stripe.payout.retrieve`

**Description:** Retrieve a specific Stripe payout

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payout_id` | string | ✓ | Payout ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payout ID |
| `status` | string | Payout status |
| `amount` | integer | Amount in cents |
| `currency` | string | Currency |
| `arrival_date` | integer | Arrival timestamp |
| `destination` | string | Bank account ID |
| `failure_code` | string | Failure code if failed |
| `failure_message` | string | Failure message |

---

### `stripe.price.create`

**Description:** Create a price in Stripe

> Creates a new price for a product. Prices define how much and how often to charge. A product can have multiple prices (e.g., monthly vs annual).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `product` | string | ✓ | Product ID this price is for |
| `unit_amount` | integer |  | Price in smallest currency unit (cents) |
| `currency` | string | ✓ | Three-letter ISO currency code |
| `recurring` | object |  | Recurring billing configuration |
| `nickname` | string |  | Brief description (for your reference) |
| `billing_scheme` | string |  | How to compute the price |
| `tiers` | array |  | Pricing tiers (if billing_scheme is tiered) |
| `tiers_mode` | string |  | How tiers are applied |
| `metadata` | object |  | Key-value pairs for your own use |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Price ID |
| `product` | string | Product ID |
| `unit_amount` | integer | Amount in cents |
| `currency` | string | Currency code |
| `recurring` | object | Recurring config |
| `type` | string | one_time or recurring |

**Example:**
```json
{
  "capability": "stripe.price.create",
  "params": {
    "product": "prod_ABC123",
    "unit_amount": 2999,
    "currency": "usd",
    "recurring": {
      "interval": "month"
    },
    "nickname": "Monthly Plan"
  }
}
```

---

### `stripe.price.list`

**Description:** List prices in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `product` | string |  | Filter by product ID |
| `active` | boolean |  | Filter by active status |
| `type` | string |  | Filter by type |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of price objects |
| `has_more` | boolean | More results |

---

### `stripe.price.retrieve`

**Description:** Retrieve a price in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `price_id` | string | ✓ | Price ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Price ID |
| `product` | string | Product ID |
| `unit_amount` | integer | Amount |
| `currency` | string | Currency |
| `recurring` | object | Recurring config |
| `active` | boolean | Is active |

---

### `stripe.price.search`

**Description:** Search prices in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ | Search query string |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Matching prices |
| `has_more` | boolean | More results |

---

### `stripe.price.update`

**Description:** Update a price in Stripe

> Updates a price. Most fields are immutable after creation - you can only update metadata, nickname, and active status.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `price_id` | string | ✓ | Price ID to update |
| `active` | boolean |  | Set active status |
| `nickname` | string |  | Update nickname |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Price ID |
| `active` | boolean | Active status |

---

### `stripe.product.create`

**Description:** Create a product in Stripe

> Creates a new product object in Stripe. Products represent goods or services you sell. After creating a product, create prices to define how much to charge.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | ✓ | Product name displayed to customers |
| `description` | string |  | Product description |
| `active` | boolean |  | Whether product is available for purchase |
| `metadata` | object |  | Key-value pairs for your own use |
| `images` | array |  | URLs of product images |
| `default_price_data` | object |  | Create default price alongside product |
| `tax_code` | string |  | Tax code for automatic tax calculation |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Product ID |
| `name` | string | Product name |
| `active` | boolean | Is active |
| `default_price` | string | Default price ID |
| `created` | integer | Unix timestamp |

**Example:**
```json
{
  "capability": "stripe.product.create",
  "params": {
    "name": "Pro Plan",
    "description": "Full access to all features",
    "default_price_data": {
      "unit_amount": 2999,
      "currency": "usd",
      "recurring": {
        "interval": "month"
      }
    }
  }
}
```

---

### `stripe.product.delete`

**Description:** Delete a product in Stripe

> Deletes a product. Products can only be deleted if they have no prices associated with them.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `product_id` | string | ✓ | Product ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted product ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.product.list`

**Description:** List products in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `active` | boolean |  | Filter by active status |
| `limit` | integer |  | Maximum number to return (1-100) |
| `starting_after` | string |  | Cursor for pagination |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of product objects |
| `has_more` | boolean | More results available |

---

### `stripe.product.retrieve`

**Description:** Retrieve a product in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `product_id` | string | ✓ | Product ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Product ID |
| `name` | string | Product name |
| `description` | string | Description |
| `active` | boolean | Is active |
| `default_price` | string | Default price ID |
| `metadata` | object | Metadata |
| `images` | array | Image URLs |

---

### `stripe.product.search`

**Description:** Search products in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ | Search query string |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Matching products |
| `has_more` | boolean | More results |

---

### `stripe.product.update`

**Description:** Update a product in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `product_id` | string | ✓ | Product ID to update |
| `name` | string |  | New product name |
| `description` | string |  | New description |
| `active` | boolean |  | Set active status |
| `metadata` | object |  | Updated metadata |
| `default_price` | string |  | New default price ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Product ID |
| `name` | string | Updated name |
| `active` | boolean | Active status |

---

### `stripe.promotion_code.create`

**Description:** Create a promotion code

> Creates a promotion code that customers can enter to apply a coupon. Promotion codes can have restrictions like customer, date, or usage limits.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `coupon` | string | ✓ | Coupon ID this code applies |
| `code` | string |  | The customer-facing code |
| `active` | boolean |  | Whether code is active |
| `customer` | string |  | Restrict to specific customer |
| `expires_at` | integer |  | Expiration timestamp |
| `max_redemptions` | integer |  | Maximum number of redemptions |
| `restrictions` | object |  | Usage restrictions |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Promotion code ID |
| `code` | string | The code |
| `coupon` | string | Coupon ID |
| `active` | boolean | Is active |
| `times_redeemed` | integer | Redemptions |

---

### `stripe.promotion_code.list`

**Description:** List promotion codes

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `coupon` | string |  | Filter by coupon ID |
| `code` | string |  | Filter by code |
| `active` | boolean |  | Filter by active status |
| `customer` | string |  | Filter by customer |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of promotion codes |
| `has_more` | boolean | More results |

---

### `stripe.promotion_code.retrieve`

**Description:** Retrieve a promotion code

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `promotion_code_id` | string | ✓ | Promotion code ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Promotion code ID |
| `code` | string | The code |
| `coupon` | object | Coupon details |
| `active` | boolean | Is active |
| `restrictions` | object | Restrictions |

---

### `stripe.promotion_code.update`

**Description:** Update a promotion code

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `promotion_code_id` | string | ✓ | Promotion code ID to update |
| `active` | boolean |  | Activate or deactivate |
| `restrictions` | object |  | Update restrictions |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Promotion code ID |
| `active` | boolean | Is active |

---

### `stripe.quote.accept`

**Description:** Accept a quote

> Accepts a quote on behalf of the customer, creating a subscription or invoice based on the quote configuration.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `quote_id` | string | ✓ | Quote ID to accept |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Quote ID |
| `status` | string | Should be accepted |
| `invoice` | string | Created invoice |
| `subscription` | string | Created sub |

---

### `stripe.quote.cancel`

**Description:** Cancel a quote

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `quote_id` | string | ✓ | Quote ID to cancel |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Quote ID |
| `status` | string | Should be canceled |

---

### `stripe.quote.create`

**Description:** Create a quote in Stripe

> Creates a quote for a customer. Quotes allow you to send pricing proposals that customers can accept to start a subscription or payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string | ✓ | Customer ID |
| `line_items` | array |  | Items to quote |
| `description` | string |  | Quote description |
| `header` | string |  | Header text |
| `footer` | string |  | Footer text |
| `expires_at` | integer |  | Expiration timestamp |
| `collection_method` | string |  | How to collect payment |
| `automatic_tax` | object |  | Automatic tax settings |
| `discounts` | array |  | Discounts to apply |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Quote ID |
| `status` | string | Quote status |
| `amount_total` | integer | Total amount |
| `customer` | string | Customer ID |

---

### `stripe.quote.finalize`

**Description:** Finalize a quote

> Finalizes a quote, preventing further edits and generating a PDF. Finalized quotes can be sent to customers for acceptance.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `quote_id` | string | ✓ | Quote ID to finalize |
| `expires_at` | integer |  | Set expiration when finalizing |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Quote ID |
| `status` | string | Should be open |

---

### `stripe.quote.list`

**Description:** List quotes

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string |  | Filter by customer |
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of quotes |
| `has_more` | boolean | More results |

---

### `stripe.quote.pdf`

**Description:** Download quote PDF

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `quote_id` | string | ✓ | Quote ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `pdf_content` | string | PDF binary data |

---

### `stripe.quote.retrieve`

**Description:** Retrieve a quote

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `quote_id` | string | ✓ | Quote ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Quote ID |
| `status` | string | Status |
| `customer` | string | Customer |
| `amount_total` | integer | Total |
| `line_items` | object | Items |

---

### `stripe.quote.update`

**Description:** Update a quote

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `quote_id` | string | ✓ | Quote ID to update |
| `line_items` | array |  | Update line items |
| `description` | string |  | Update description |
| `expires_at` | integer |  | Update expiration |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Quote ID |
| `status` | string | Status |

---

### `stripe.radar.early_fraud_warning.list`

**Description:** List early fraud warnings

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `charge` | string |  | Filter by charge ID |
| `payment_intent` | string |  | Filter by payment intent ID |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of warnings |
| `has_more` | boolean | More results |

---

### `stripe.radar.early_fraud_warning.retrieve`

**Description:** Retrieve an early fraud warning

> Retrieves an early fraud warning indicating a charge is potentially fraudulent. Issued when card networks report suspected fraud.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `warning_id` | string | ✓ | Early fraud warning ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Warning ID |
| `charge` | string | Charge ID |
| `payment_intent` | string | PI ID |
| `fraud_type` | string | Type of fraud |
| `actionable` | boolean | Is actionable |
| `created` | integer | Unix timestamp |

---

### `stripe.radar.review.approve`

**Description:** Approve a Radar review

> Approves a payment that was placed in review. The payment will proceed.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `review_id` | string | ✓ | Review ID to approve |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Review ID |
| `open` | boolean | Should be false |
| `closed_reason` | string | Should be approved |

---

### `stripe.radar.review.list`

**Description:** List Radar reviews

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of reviews |
| `has_more` | boolean | More results |

---

### `stripe.radar.review.retrieve`

**Description:** Retrieve a Radar review

> Retrieves a review generated by Radar when a payment is flagged for manual review based on your rules.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `review_id` | string | ✓ | Review ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Review ID |
| `charge` | string | Charge ID |
| `payment_intent` | string | PI ID |
| `reason` | string | Review reason |
| `open` | boolean | Is open |
| `opened_reason` | string | Why opened |
| `closed_reason` | string | Why closed |

---

### `stripe.radar.value_list.create`

**Description:** Create a Radar value list

> Creates a value list for use in Radar rules. Value lists can contain email addresses, IP addresses, card fingerprints, or strings.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `alias` | string | ✓ | Unique identifier for the list |
| `name` | string | ✓ | Display name for the list |
| `item_type` | string | ✓ | Type of items in the list |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Value list ID |
| `alias` | string | Alias |
| `name` | string | Name |
| `item_type` | string | Item type |

---

### `stripe.radar.value_list.delete`

**Description:** Delete a Radar value list

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `value_list_id` | string | ✓ | Value list ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted list ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.radar.value_list.list`

**Description:** List Radar value lists

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `alias` | string |  | Filter by alias |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of value lists |
| `has_more` | boolean | More results |

---

### `stripe.radar.value_list.retrieve`

**Description:** Retrieve a Radar value list

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `value_list_id` | string | ✓ | Value list ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | List ID |
| `alias` | string | Alias |
| `name` | string | Name |
| `item_type` | string | Item type |
| `list_items` | object | Items in list |

---

### `stripe.radar.value_list.update`

**Description:** Update a Radar value list

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `value_list_id` | string | ✓ | Value list ID to update |
| `name` | string |  | New name |
| `alias` | string |  | New alias |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | List ID |
| `name` | string | Updated name |

---

### `stripe.radar.value_list_item.create`

**Description:** Add an item to a Radar value list

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `value_list` | string | ✓ | Value list ID |
| `value` | string | ✓ | Value to add |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Item ID |
| `value` | string | Value |
| `value_list` | string | List ID |

---

### `stripe.radar.value_list_item.delete`

**Description:** Delete a value list item

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_id` | string | ✓ | Item ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted item ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.radar.value_list_item.list`

**Description:** List items in a value list

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `value_list` | string | ✓ | Value list ID |
| `value` | string |  | Filter by value |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of items |
| `has_more` | boolean | More results |

---

### `stripe.radar.value_list_item.retrieve`

**Description:** Retrieve a value list item

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_id` | string | ✓ | Item ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Item ID |
| `value` | string | Value |
| `value_list` | string | List ID |

---

### `stripe.refund.cancel`

**Description:** Cancel a refund in Stripe

> Cancels a refund with a status of requires_action. You cannot cancel refunds that have already been processed.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `refund_id` | string | ✓ | Refund ID to cancel |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Refund ID |
| `status` | string | Should be 'canceled' |

---

### `stripe.refund.list`

**Description:** List refunds in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `charge` | string |  | Filter by charge ID |
| `payment_intent` | string |  | Filter by payment intent ID |
| `limit` | integer |  | Maximum number to return (1-100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of refund objects |
| `has_more` | boolean | More results available |

---

### `stripe.refund.retrieve`

**Description:** Retrieve a refund in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `refund_id` | string | ✓ | Refund ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Refund ID |
| `status` | string | Refund status |
| `amount` | integer | Amount in cents |
| `charge` | string | Charge ID |
| `reason` | string | Refund reason |
| `created` | integer | Unix timestamp |

---

### `stripe.refund.update`

**Description:** Update a refund in Stripe

> Updates the metadata on a refund. Other fields cannot be changed.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `refund_id` | string | ✓ | Refund ID to update |
| `metadata` | object |  | Key-value pairs to update |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Refund ID |
| `metadata` | object | Updated metadata |

---

### `stripe.reporting.report_run.create`

**Description:** Create a report run

> Creates a new report run to generate a report of a specific type. Reports are generated asynchronously.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `report_type` | string | ✓ | Type of report |
| `parameters` | object |  | Report parameters |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Report run ID |
| `report_type` | string | Report type |
| `status` | string | Run status |
| `result` | object | Result when done |

---

### `stripe.reporting.report_run.list`

**Description:** List report runs

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `created` | object |  | Filter by created date |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of report runs |
| `has_more` | boolean | More results |

---

### `stripe.reporting.report_run.retrieve`

**Description:** Retrieve a report run

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `report_run_id` | string | ✓ | Report run ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Report run ID |
| `report_type` | string | Type |
| `status` | string | Status |
| `result` | object | Result file info |

---

### `stripe.reporting.report_type.list`

**Description:** List available report types

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of report types |
| `has_more` | boolean | More results |

---

### `stripe.reporting.report_type.retrieve`

**Description:** Retrieve a report type

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `report_type` | string | ✓ | Report type ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Report type ID |
| `name` | string | Human-readable name |
| `data_available_start` | integer | Data start |
| `data_available_end` | integer | Data end |
| `default_columns` | array | Default columns |

---

### `stripe.setup_intent.cancel`

**Description:** Cancel a Setup Intent

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `setup_intent_id` | string | ✓ | SetupIntent ID to cancel |
| `cancellation_reason` | string |  | Reason for cancellation |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | SetupIntent ID |
| `status` | string | Should be canceled |

---

### `stripe.setup_intent.confirm`

**Description:** Confirm a Setup Intent

> Confirms a SetupIntent to complete the payment method setup process. May require customer authentication for 3D Secure.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `setup_intent_id` | string | ✓ | SetupIntent ID to confirm |
| `payment_method` | string |  | Payment method to attach |
| `return_url` | string |  | URL for redirect after auth |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | SetupIntent ID |
| `status` | string | Should be succeeded |
| `payment_method` | string | Saved method |

---

### `stripe.setup_intent.create`

**Description:** Create a Setup Intent

> Creates a SetupIntent for collecting payment method details without charging. Use to save cards for future payments like subscriptions or metered billing.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string |  | Customer to attach payment method to |
| `payment_method_types` | array |  | Allowed payment method types |
| `usage` | string |  | How payment method will be used |
| `confirm` | boolean |  | Immediately confirm the intent |
| `payment_method` | string |  | Payment method to attach and confirm |
| `return_url` | string |  | URL for redirect after setup |
| `metadata` | object |  | Key-value pairs for your use |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | SetupIntent ID |
| `client_secret` | string | Client secret |
| `status` | string | Setup status |
| `customer` | string | Customer ID |
| `payment_method` | string | Payment method |

---

### `stripe.setup_intent.list`

**Description:** List Setup Intents

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string |  | Filter by customer ID |
| `payment_method` | string |  | Filter by payment method |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of SetupIntents |
| `has_more` | boolean | More results |

---

### `stripe.setup_intent.retrieve`

**Description:** Retrieve a Setup Intent

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `setup_intent_id` | string | ✓ | SetupIntent ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | SetupIntent ID |
| `status` | string | Status |
| `customer` | string | Customer |
| `payment_method` | string | Payment method |
| `client_secret` | string | Client secret |

---

### `stripe.setup_intent.update`

**Description:** Update a Setup Intent

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `setup_intent_id` | string | ✓ | SetupIntent ID to update |
| `customer` | string |  | New customer ID |
| `payment_method` | string |  | New payment method |
| `payment_method_types` | array |  | Update allowed types |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | SetupIntent ID |
| `status` | string | Status |

---

### `stripe.subscription.cancel`

**Description:** Cancel a subscription in Stripe

> Cancels a subscription. By default, cancels immediately. Set cancel_at_period_end to cancel at the end of the current billing period.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `subscription_id` | string | ✓ | Subscription ID to cancel |
| `cancel_at_period_end` | boolean |  | Cancel at end of period instead of immediately |
| `invoice_now` | boolean |  | Generate final invoice immediately |
| `prorate` | boolean |  | Prorate final invoice |
| `cancellation_details` | object |  | Cancellation reason details |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Subscription ID |
| `status` | string | Should be 'canceled' |
| `canceled_at` | integer | Cancellation timestamp |
| `cancel_at_period_end` | boolean | Whether canceling at period end |

---

### `stripe.subscription.create`

**Description:** Create a subscription in Stripe

> Creates a new subscription for a customer. Subscriptions automatically charge customers on a recurring basis. Requires a customer with a payment method.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string | ✓ | Customer ID |
| `items` | array | ✓ | List of subscription items with price IDs |
| `default_payment_method` | string |  | Payment method to use for this subscription |
| `trial_period_days` | integer |  | Number of trial days before charging |
| `trial_end` | integer |  | Unix timestamp when trial ends |
| `cancel_at_period_end` | boolean |  | Cancel at end of current period |
| `billing_cycle_anchor` | integer |  | Unix timestamp for billing cycle start |
| `proration_behavior` | string |  | How to handle prorations |
| `metadata` | object |  | Key-value pairs for your own use |
| `collection_method` | string |  | How to collect payments |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Subscription ID |
| `status` | string | Subscription status |
| `current_period_start` | integer | Start of current billing period |
| `current_period_end` | integer | End of current billing period |
| `customer` | string | Customer ID |
| `items` | object | Subscription items |
| `latest_invoice` | string | Latest invoice ID |

**Example:**
```json
{
  "capability": "stripe.subscription.create",
  "params": {
    "customer": "cus_ABC123",
    "items": [
      {
        "price": "price_monthly"
      }
    ],
    "trial_period_days": 14
  }
}
```

---

### `stripe.subscription.list`

**Description:** List subscriptions in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer` | string |  | Filter by customer ID |
| `status` | string |  | Filter by status |
| `price` | string |  | Filter by price ID |
| `limit` | integer |  | Maximum number to return (1-100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of subscriptions |
| `has_more` | boolean | More results available |

---

### `stripe.subscription.retrieve`

**Description:** Retrieve a subscription in Stripe

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `subscription_id` | string | ✓ | Subscription ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Subscription ID |
| `status` | string | Status (active, past_due, canceled, etc.) |
| `customer` | string | Customer ID |
| `current_period_start` | integer | Period start |
| `current_period_end` | integer | Period end |
| `cancel_at_period_end` | boolean | Will cancel |
| `canceled_at` | integer | When canceled |
| `items` | object | Subscription items |
| `latest_invoice` | string | Latest invoice |
| `default_payment_method` | string | Payment method |

---

### `stripe.subscription.update`

**Description:** Update a subscription in Stripe

> Updates an existing subscription. Can change items (upgrade/downgrade), payment method, billing settings, and more.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `subscription_id` | string | ✓ | Subscription ID to update |
| `items` | array |  | Updated subscription items |
| `default_payment_method` | string |  | New default payment method |
| `cancel_at_period_end` | boolean |  | Set to cancel at period end |
| `proration_behavior` | string |  | How to handle prorations |
| `trial_end` | string |  | Unix timestamp or 'now' to end trial |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Subscription ID |
| `status` | string | Updated status |
| `items` | object | Updated items |

---

### `stripe.tax.calculation.create`

**Description:** Create a tax calculation

> Calculates tax for a transaction. Returns the tax amounts that should be collected based on the customer's location and the items being sold.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `currency` | string | ✓ | Three-letter ISO currency code |
| `line_items` | array | ✓ | Items to calculate tax for |
| `customer_details` | object | ✓ | Customer location info |
| `shipping_cost` | object |  | Shipping cost details |
| `tax_date` | integer |  | Unix timestamp for tax rates |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Calculation ID |
| `amount_total` | integer | Total amount |
| `tax_amount_exclusive` | integer | Excl. tax |
| `tax_amount_inclusive` | integer | Incl. tax |
| `line_items` | object | Calculated items |
| `shipping_cost` | object | Shipping tax |

---

### `stripe.tax.calculation.line_items.list`

**Description:** List line items for a tax calculation

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `calculation_id` | string | ✓ | Tax calculation ID |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Line items |
| `has_more` | boolean | More results |

---

### `stripe.tax.calculation.retrieve`

**Description:** Retrieve a tax calculation

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `calculation_id` | string | ✓ | Tax calculation ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Calculation ID |
| `amount_total` | integer | Total |
| `tax_amount_exclusive` | integer | Tax |
| `line_items` | object | Items |

---

### `stripe.tax.registration.create`

**Description:** Create a tax registration

> Creates a tax registration indicating you're registered to collect tax in a jurisdiction. Required for accurate tax calculations.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `country` | string | ✓ | Two-letter country code |
| `active_from` | string | ✓ | When registration becomes active |
| `country_options` | object | ✓ | Country-specific options |
| `expires_at` | integer |  | When registration expires |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Registration ID |
| `country` | string | Country |
| `status` | string | Status |
| `active_from` | integer | Active from |

---

### `stripe.tax.registration.list`

**Description:** List tax registrations

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of registrations |
| `has_more` | boolean | More results |

---

### `stripe.tax.registration.retrieve`

**Description:** Retrieve a tax registration

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `registration_id` | string | ✓ | Registration ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Registration ID |
| `country` | string | Country |
| `status` | string | Status |

---

### `stripe.tax.registration.update`

**Description:** Update a tax registration

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `registration_id` | string | ✓ | Registration ID to update |
| `expires_at` | integer |  | New expiration timestamp |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Registration ID |
| `expires_at` | integer | New expiration |

---

### `stripe.tax.settings.retrieve`

**Description:** Retrieve tax settings

> Retrieves your Stripe Tax settings including head office location and default tax behavior.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `defaults` | object | Default settings |
| `head_office` | object | Head office |
| `status_details` | object | Status |

---

### `stripe.tax.settings.update`

**Description:** Update tax settings

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `defaults` | object |  | Update default settings |
| `head_office` | object |  | Update head office location |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `defaults` | object | Updated defaults |
| `head_office` | object | Updated office |

---

### `stripe.tax.transaction.create_from_calculation`

**Description:** Create a tax transaction from a calculation

> Creates a tax transaction from an existing calculation. Use this to record the tax collected when completing a payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `calculation` | string | ✓ | Tax calculation ID |
| `reference` | string | ✓ | Your reference for this transaction |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transaction ID |
| `reference` | string | Reference |
| `type` | string | Transaction type |
| `tax_date` | integer | Tax date |

---

### `stripe.tax.transaction.create_reversal`

**Description:** Create a tax transaction reversal

> Creates a reversal for a tax transaction. Use when refunding a payment to properly account for the tax reversal.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `mode` | string | ✓ | Reversal mode |
| `original_transaction` | string | ✓ | Original transaction ID to reverse |
| `reference` | string | ✓ | Your reference for this reversal |
| `line_items` | array |  | Line items to reverse (for partial) |
| `flat_amount` | integer |  | Flat amount to reverse |
| `shipping_cost` | object |  | Shipping cost to reverse |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Reversal transaction ID |
| `type` | string | Should be reversal |
| `original_transaction` | string | Original |

---

### `stripe.tax.transaction.line_items.list`

**Description:** List line items for a tax transaction

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `transaction_id` | string | ✓ | Tax transaction ID |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Line items |
| `has_more` | boolean | More results |

---

### `stripe.tax.transaction.retrieve`

**Description:** Retrieve a tax transaction

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `transaction_id` | string | ✓ | Tax transaction ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transaction ID |
| `type` | string | Type |
| `reference` | string | Reference |
| `tax_date` | integer | Tax date |
| `line_items` | object | Line items |

---

### `stripe.terminal.connection_token.create`

**Description:** Create a Terminal connection token

> Creates a connection token for the Terminal SDK. Tokens are used to connect your application to Terminal readers.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location` | string |  | Location to scope the token to |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `secret` | string | Connection token |

---

### `stripe.terminal.location.create`

**Description:** Create a Terminal location

> Creates a location representing a physical place where Terminal readers are deployed. Useful for organizing readers across multiple stores.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `display_name` | string | ✓ | Name displayed in Dashboard |
| `address` | object | ✓ | Physical address |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Location ID |
| `display_name` | string | Name |
| `address` | object | Address |

---

### `stripe.terminal.location.delete`

**Description:** Delete a Terminal location

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_id` | string | ✓ | Location ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted location ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.terminal.location.list`

**Description:** List Terminal locations

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of locations |
| `has_more` | boolean | More results |

---

### `stripe.terminal.location.retrieve`

**Description:** Retrieve a Terminal location

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_id` | string | ✓ | Location ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Location ID |
| `display_name` | string | Name |
| `address` | object | Address |

---

### `stripe.terminal.location.update`

**Description:** Update a Terminal location

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_id` | string | ✓ | Location ID to update |
| `display_name` | string |  | New name |
| `address` | object |  | Updated address |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Location ID |
| `display_name` | string | Updated name |

---

### `stripe.terminal.reader.cancel_action`

**Description:** Cancel the current action on a reader

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `reader_id` | string | ✓ | Reader ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Reader ID |
| `action` | object | Canceled action |

---

### `stripe.terminal.reader.create`

**Description:** Register a Terminal reader

> Registers a new Terminal reader to your Stripe account. Readers are physical devices that accept in-person payments.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `registration_code` | string | ✓ | Registration code from the reader |
| `label` | string |  | Custom label for the reader |
| `location` | string |  | Location ID to assign reader to |
| `metadata` | object |  | Key-value pairs for your use |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Reader ID |
| `device_type` | string | Reader model |
| `label` | string | Custom label |
| `location` | string | Location ID |
| `status` | string | Reader status |
| `serial_number` | string | Serial number |

---

### `stripe.terminal.reader.delete`

**Description:** Delete a Terminal reader

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `reader_id` | string | ✓ | Reader ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted reader ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.terminal.reader.list`

**Description:** List Terminal readers

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location` | string |  | Filter by location ID |
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of readers |
| `has_more` | boolean | More results |

---

### `stripe.terminal.reader.process_payment`

**Description:** Process a payment on a Terminal reader

> Initiates a payment on a Terminal reader. The reader will prompt the customer to present their card.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `reader_id` | string | ✓ | Reader ID to process on |
| `payment_intent` | string | ✓ | PaymentIntent ID to collect |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Reader ID |
| `action` | object | Current action |

---

### `stripe.terminal.reader.retrieve`

**Description:** Retrieve a Terminal reader

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `reader_id` | string | ✓ | Reader ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Reader ID |
| `device_type` | string | Model |
| `label` | string | Label |
| `location` | string | Location |
| `status` | string | Status |
| `ip_address` | string | IP address |

---

### `stripe.terminal.reader.update`

**Description:** Update a Terminal reader

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `reader_id` | string | ✓ | Reader ID to update |
| `label` | string |  | New label |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Reader ID |
| `label` | string | Updated label |

---

### `stripe.transfer.create`

**Description:** Create a transfer to connected account (Connect)

> Creates a transfer to a connected Stripe account. Requires Stripe Connect. Use for marketplace payouts to sellers or service providers.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `amount` | integer | ✓ | Amount in cents to transfer |
| `currency` | string | ✓ | Three-letter ISO currency code |
| `destination` | string | ✓ | Connected account ID |
| `description` | string |  | Description for the transfer |
| `source_transaction` | string |  | Charge ID to transfer from |
| `transfer_group` | string |  | Group ID for related transfers |
| `metadata` | object |  | Key-value pairs for your own use |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transfer ID |
| `amount` | integer | Amount transferred |
| `currency` | string | Currency |
| `destination` | string | Connected account |
| `created` | integer | Unix timestamp |

---

### `stripe.transfer.list`

**Description:** List transfers to connected accounts

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `destination` | string |  | Filter by destination account |
| `transfer_group` | string |  | Filter by transfer group |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of transfers |
| `has_more` | boolean | More results |

---

### `stripe.treasury.financial_account.create`

**Description:** Create a Treasury financial account

> Creates a FinancialAccount for holding funds. Treasury financial accounts provide banking-like functionality including account numbers and routing numbers.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `supported_currencies` | array | ✓ | Currencies the account will support |
| `features` | object |  | Features to enable |
| `platform_restrictions` | object |  | Platform-level restrictions |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Financial account ID |
| `supported_currencies` | array | Currencies |
| `balance` | object | Current balance |
| `financial_addresses` | array | Bank details |
| `status` | string | Account status |

---

### `stripe.treasury.financial_account.list`

**Description:** List Treasury financial accounts

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of accounts |
| `has_more` | boolean | More results |

---

### `stripe.treasury.financial_account.retrieve`

**Description:** Retrieve a Treasury financial account

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `financial_account_id` | string | ✓ | Financial account ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Account ID |
| `balance` | object | Balance |
| `financial_addresses` | array | Addresses |
| `status` | string | Status |
| `features` | object | Features |

---

### `stripe.treasury.financial_account.update`

**Description:** Update a Treasury financial account

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `financial_account_id` | string | ✓ | Financial account ID to update |
| `features` | object |  | Update features |
| `platform_restrictions` | object |  | Update restrictions |
| `metadata` | object |  | Updated metadata |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Account ID |
| `features` | object | Updated features |

---

### `stripe.treasury.outbound_payment.cancel`

**Description:** Cancel a Treasury outbound payment

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outbound_payment_id` | string | ✓ | Outbound payment ID to cancel |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payment ID |
| `status` | string | Should be canceled |

---

### `stripe.treasury.outbound_payment.create`

**Description:** Create a Treasury outbound payment

> Creates an outbound payment from a FinancialAccount to an external destination (bank account, debit card, or Stripe account).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `financial_account` | string | ✓ | Source financial account ID |
| `amount` | integer | ✓ | Amount in cents |
| `currency` | string | ✓ | Currency code |
| `destination_payment_method` | string |  | Destination payment method ID |
| `destination_payment_method_data` | object |  | Inline destination data |
| `description` | string |  | Description for the payment |
| `statement_descriptor` | string |  | Statement descriptor |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Outbound payment ID |
| `amount` | integer | Amount |
| `status` | string | Payment status |
| `financial_account` | string | Source |
| `expected_arrival_date` | integer | ETA |

---

### `stripe.treasury.outbound_payment.list`

**Description:** List Treasury outbound payments

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `financial_account` | string | ✓ | Financial account ID |
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of payments |
| `has_more` | boolean | More results |

---

### `stripe.treasury.outbound_payment.retrieve`

**Description:** Retrieve a Treasury outbound payment

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outbound_payment_id` | string | ✓ | Outbound payment ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payment ID |
| `amount` | integer | Amount |
| `status` | string | Status |
| `financial_account` | string | Source |

---

### `stripe.treasury.outbound_transfer.cancel`

**Description:** Cancel a Treasury outbound transfer

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outbound_transfer_id` | string | ✓ | Outbound transfer ID to cancel |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transfer ID |
| `status` | string | Should be canceled |

---

### `stripe.treasury.outbound_transfer.create`

**Description:** Create a Treasury outbound transfer

> Creates an outbound transfer from a FinancialAccount to a connected Stripe account's external bank account.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `financial_account` | string | ✓ | Source financial account ID |
| `destination_payment_method` | string | ✓ | Destination payment method ID |
| `amount` | integer | ✓ | Amount in cents |
| `currency` | string | ✓ | Currency code |
| `description` | string |  | Transfer description |
| `statement_descriptor` | string |  | Statement descriptor |
| `metadata` | object |  | Key-value pairs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transfer ID |
| `amount` | integer | Amount |
| `status` | string | Status |
| `financial_account` | string | Source |

---

### `stripe.treasury.outbound_transfer.list`

**Description:** List Treasury outbound transfers

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `financial_account` | string | ✓ | Financial account ID |
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of transfers |
| `has_more` | boolean | More results |

---

### `stripe.treasury.outbound_transfer.retrieve`

**Description:** Retrieve a Treasury outbound transfer

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outbound_transfer_id` | string | ✓ | Outbound transfer ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transfer ID |
| `amount` | integer | Amount |
| `status` | string | Status |

---

### `stripe.treasury.transaction.list`

**Description:** List Treasury transactions

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `financial_account` | string | ✓ | Financial account ID |
| `status` | string |  | Filter by status |
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of transactions |
| `has_more` | boolean | More results |

---

### `stripe.treasury.transaction.retrieve`

**Description:** Retrieve a Treasury transaction

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `transaction_id` | string | ✓ | Transaction ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transaction ID |
| `amount` | integer | Amount |
| `currency` | string | Currency |
| `financial_account` | string | Account |
| `flow_type` | string | Flow type |
| `status` | string | Status |

---

### `stripe.webhook.create`

**Description:** Create a webhook endpoint in Stripe

> Creates a webhook endpoint that Stripe will send events to. Webhooks notify your application of events like successful payments, subscription changes, and dispute updates.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | ✓ | URL that receives webhook events |
| `enabled_events` | array | ✓ | Events to send to this endpoint |
| `description` | string |  | Description of the webhook endpoint |
| `api_version` | string |  | Stripe API version for events |
| `metadata` | object |  | Key-value pairs for your use |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Webhook endpoint ID |
| `url` | string | Endpoint URL |
| `status` | string | Endpoint status |
| `secret` | string | Signing secret |
| `enabled_events` | array | Enabled events |

---

### `stripe.webhook.delete`

**Description:** Delete a webhook endpoint

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `webhook_endpoint_id` | string | ✓ | Webhook endpoint ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deleted endpoint ID |
| `deleted` | boolean | True if deleted |

---

### `stripe.webhook.list`

**Description:** List webhook endpoints

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of endpoints |
| `has_more` | boolean | More results |

---

### `stripe.webhook.retrieve`

**Description:** Retrieve a webhook endpoint

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `webhook_endpoint_id` | string | ✓ | Webhook endpoint ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Endpoint ID |
| `url` | string | Endpoint URL |
| `status` | string | Status |
| `enabled_events` | array | Events |
| `api_version` | string | API version |

---

### `stripe.webhook.update`

**Description:** Update a webhook endpoint

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `webhook_endpoint_id` | string | ✓ | Webhook endpoint ID to update |
| `url` | string |  | New URL |
| `enabled_events` | array |  | Updated event list |
| `disabled` | boolean |  | Disable the endpoint |
| `description` | string |  | Update description |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Endpoint ID |
| `url` | string | Updated URL |
| `status` | string | Status |

---

## BILLCOM (9 capabilities)

### `billcom.bill.approve`

**Description:** Approve a bill in Bill.com

> Approves a bill for payment in Bill.com. Bills typically require approval before they can be paid. Approval may be part of a multi-step workflow depending on company settings.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bill_id` | string | ✓ | Bill.com bill ID to approve |
| `notes` | string |  | Approver notes or comments |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bill_id` | string | Approved bill ID |
| `status` | string | New bill status (APPROVED) |
| `approved_at` | string | Approval timestamp |
| `approved_by` | string | Approver user ID or name |

---

### `billcom.bill.create`

**Description:** Create a bill in Bill.com

> Creates a new bill (accounts payable) in Bill.com. Bills track amounts owed to vendors and flow through the approval workflow before payment. Supports line items for detailed tracking.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Bill.com vendor ID (with or without bc: prefix) |
| `invoice_number` | string | ✓ | Vendor's invoice number for reference |
| `invoice_date` | string | ✓ | Invoice date (YYYY-MM-DD format) |
| `due_date` | string | ✓ | Payment due date (YYYY-MM-DD format) |
| `amount` | number | ✓ | Total bill amount |
| `line_items` | array |  | Itemized line items with amounts and GL accounts |
| `description` | string |  | Bill description or memo |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bill_id` | string | Bill.com bill ID (prefixed with bc:) |
| `invoice_number` | string | Invoice number as stored |
| `amount` | number | Bill total amount |
| `status` | string | Bill status (open, approved, paid) |
| `due_date` | string | Payment due date |

---

### `billcom.bill.list`

**Description:** List bills from Bill.com

> Retrieves a paginated list of bills from Bill.com. Filter by status (OPEN, PAID, SCHEDULED) or vendor. Use to find bills pending approval or payment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `page` | integer |  | Page number |
| `page_size` | integer |  | Bills per page |
| `status` | string |  | Filter by status |
| `vendor_id` | string |  | Filter by vendor ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bills` | array | List of bill records with id, amount, status, due_date |
| `total` | integer | Total bills matching criteria |
| `page` | integer | Current page number |

---

### `billcom.payment.bulk`

**Description:** Create bulk payments in Bill.com

> Creates multiple payments in a single batch operation. Useful for weekly or monthly payment runs. Returns a batch ID for tracking the overall status.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payments` | array | ✓ | Array of payment objects with bill_ids, amount, payment_meth |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `batch_id` | string | Batch ID for tracking the payment run |
| `total_payments` | integer | Number of payments created |
| `total_amount` | number | Sum of all payment amounts |
| `status` | string | Batch status |

---

### `billcom.payment.create`

**Description:** Create a payment in Bill.com

> Creates a payment for one or more approved bills. Supports ACH (electronic), wire transfer, and check payments. Payments are scheduled for the specified process date.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bill_ids` | array | ✓ | List of bill IDs to pay |
| `payment_method` | string |  | Payment method |
| `process_date` | string |  | Date to process payment (YYYY-MM-DD), defaults to today |
| `amount` | number |  | Payment amount (defaults to bill total) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | Bill.com payment ID |
| `amount` | number | Payment amount |
| `payment_method` | string | Payment method used |
| `status` | string | Payment status (SCHEDULED, PROCESSING, COMPLETED) |
| `process_date` | string | Scheduled process date |

---

### `billcom.payment.status`

**Description:** Get payment status from Bill.com

> Retrieves the current status and details of a payment. Track payment progress from SCHEDULED through PROCESSING to COMPLETED. Includes vendor information and any error details.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_id` | string | ✓ | Bill.com payment ID to look up |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | Payment ID |
| `amount` | number | Payment amount |
| `status` | string | Current status (SCHEDULED, PROCESSING, COMPLETED, FAILED) |
| `payment_method` | string | Payment method used |
| `process_date` | string | Process date |
| `vendor_name` | string | Vendor receiving payment |

---

### `billcom.vendor.create`

**Description:** Create a vendor in Bill.com

> Creates a new vendor record in Bill.com for payables management. Vendors can be paid via ACH, wire, or check once created. Each vendor requires a unique name and payment terms.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_name` | string | ✓ | Name of the vendor/supplier |
| `email` | string |  | Vendor contact email for payment notifications |
| `phone` | string |  | Vendor phone number |
| `account_number` | string |  | Your account number with the vendor |
| `payment_terms` | string |  | Payment terms (NET_30, NET_60, DUE_ON_RECEIPT, etc.) |
| `address` | object |  | Vendor mailing address |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendor_id` | string | Bill.com vendor ID (prefixed with bc:) |
| `vendor_name` | string | Vendor name as stored |
| `email` | string | Vendor email address |
| `status` | string | Vendor status (ACTIVE, INACTIVE) |

---

### `billcom.vendor.list`

**Description:** List vendors from Bill.com

> Retrieves a paginated list of vendors from Bill.com. Use to find vendor IDs for creating bills or payments, or to sync vendor data with your accounting system.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `page` | integer |  | Page number for pagination |
| `page_size` | integer |  | Number of vendors per page |
| `active_only` | boolean |  | Only return active vendors |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `vendors` | array | List of vendor records |
| `total` | integer | Total number of vendors matching criteria |

---

### `billcom.vendorcredit.create`

**Description:** Create a vendor credit in Bill.com

> Creates a vendor credit to track refunds, returns, or adjustments. Credits can be applied against future bills from the same vendor. Useful for managing vendor rebates or billing corrections.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_id` | string | ✓ | Bill.com vendor ID |
| `amount` | number | ✓ | Credit amount |
| `credit_date` | string |  | Credit date (YYYY-MM-DD), defaults to today |
| `description` | string |  | Reason for credit |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `credit_id` | string | Vendor credit ID |
| `vendor_id` | string | Vendor ID |
| `amount` | number | Credit amount |
| `status` | string | Credit status |

---

## DOCUSIGN (11 capabilities)

### `docusign.documents.download`

**Description:** Download a document from an envelope

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `envelope_id` | string | ✓ | Envelope ID |
| `document_id` | string | ✓ | Document ID or 'combined' for all docs |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `document_base64` | string | Base64 encoded document |
| `content_type` | string | MIME type |

---

### `docusign.documents.list`

**Description:** List documents in an envelope

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `envelope_id` | string | ✓ | Envelope ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `documents` | array | Documents with document_id, name, type, uri |

---

### `docusign.envelopes.create`

**Description:** Create and send envelope for signature

> Creates a new envelope with documents and recipients. Can be sent immediately or saved as draft.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email_subject` | string | ✓ | Email subject line |
| `email_blurb` | string |  | Email body text |
| `documents` | array | ✓ | Documents with document_id, name, file_extension, document_b |
| `recipients` | object | ✓ | Recipients: signers, carbonCopies, etc. |
| `status` | string |  | 'sent' to send immediately, 'created' for draft |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `envelope_id` | string | Created envelope ID |
| `status` | string | Envelope status |
| `uri` | string | Envelope URI |

---

### `docusign.envelopes.create_from_template`

**Description:** Create envelope from a template

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `template_id` | string | ✓ | Template ID to use |
| `email_subject` | string |  | Override email subject |
| `template_roles` | array | ✓ | Role assignments with role_name, name, email |
| `status` | string |  | 'sent' to send immediately, 'created' for draft |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `envelope_id` | string | Created envelope ID |
| `status` | string | Envelope status |

---

### `docusign.envelopes.get`

**Description:** Get envelope details from DocuSign

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `envelope_id` | string | ✓ | DocuSign envelope ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `envelope_id` | string | Envelope ID |
| `status` | string | Envelope status |
| `email_subject` | string | Email subject |
| `email_blurb` | string | Email message |
| `sender` | object | Sender info |
| `recipients` | object | Recipients by type |
| `documents` | array | Document list |
| `created_date_time` | string | Created |
| `sent_date_time` | string | Sent |
| `completed_date_time` | string | Completed |

---

### `docusign.envelopes.list`

**Description:** List envelopes from DocuSign

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `from_date` | string |  | Start date (ISO 8601) |
| `to_date` | string |  | End date (ISO 8601) |
| `status` | string |  | Envelope status filter |
| `folder_ids` | string |  | Folder IDs to filter by |
| `count` | integer |  | Max 100 |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `envelopes` | array | Envelopes with envelope_id, status, subject, sent_date, comp |
| `result_set_size` | integer | Count returned |
| `total_set_size` | integer | Total available |

---

### `docusign.envelopes.send`

**Description:** Send a draft envelope

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `envelope_id` | string | ✓ | Envelope ID to send |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `envelope_id` | string | Sent envelope ID |
| `status` | string | Should be 'sent' |

---

### `docusign.envelopes.void`

**Description:** Void an envelope

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `envelope_id` | string | ✓ | Envelope ID to void |
| `voided_reason` | string | ✓ | Reason for voiding |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `envelope_id` | string | Voided envelope ID |
| `status` | string | Should be 'voided' |

---

### `docusign.recipients.list`

**Description:** List recipients for an envelope

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `envelope_id` | string | ✓ | Envelope ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `signers` | array | Signers |
| `carbon_copies` | array | CC recipients |
| `recipient_count` | integer | Total recipients |

---

### `docusign.recipients.update`

**Description:** Update recipient information

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `envelope_id` | string | ✓ | Envelope ID |
| `recipient_id` | string | ✓ | Recipient ID to update |
| `name` | string |  | Updated recipient name |
| `email` | string |  | Updated recipient email |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `recipient_id` | string | Updated recipient ID |
| `status` | string | Update status |

---

### `docusign.templates.list`

**Description:** List templates from DocuSign

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `folder_id` | string |  | Folder ID to filter by |
| `search_text` | string |  | Search text filter |
| `count` | integer |  | Maximum templates to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `templates` | array | Templates with template_id, name, description, created |
| `result_set_size` | integer | Count |

---

## SHOPIFY (13 capabilities)

### `shopify.customer.create`

**Description:** Create a customer in Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `first_name` | string |  | Customer first name |
| `last_name` | string |  | Customer last name |
| `email` | string | ✓ | Customer email |
| `phone` | string |  | Customer phone number |
| `addresses` | array |  | Customer addresses |
| `send_email_welcome` | boolean |  | Send welcome email |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Created customer ID |
| `email` | string | Customer email |

---

### `shopify.customer.get`

**Description:** Get customer details from Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Shopify customer ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Customer ID |
| `email` | string | Email |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `orders_count` | integer | Order count |
| `total_spent` | string | Total spent |
| `created_at` | string | Created date |
| `addresses` | array | Addresses |

---

### `shopify.customers.list`

**Description:** List customers from Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `created_at_min` | string |  | Filter customers created after this date |
| `created_at_max` | string |  | Filter customers created before this date |
| `limit` | integer |  | Maximum customers to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customers` | array | Customers with id, email, first_name, last_name, orders_coun |
| `count` | integer | Customer count |

---

### `shopify.fulfillment.create`

**Description:** Create a fulfillment for an order

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `line_items_by_fulfillment_order` | array | ✓ | Fulfillment order IDs and line items to fulfill |
| `tracking_info` | object |  | Tracking number and URL |
| `notify_customer` | boolean |  | Send shipment notification to customer |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Fulfillment ID |
| `order_id` | string | Order ID |
| `status` | string | Fulfillment status |
| `tracking_number` | string | Tracking number |

---

### `shopify.order.cancel`

**Description:** Cancel an order in Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `order_id` | string | ✓ | Shopify order ID |
| `reason` | string |  | Cancellation reason |
| `restock` | boolean |  | Restock inventory |
| `email` | boolean |  | Send cancellation email to customer |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Order ID |
| `cancelled_at` | string | Cancellation timestamp |

---

### `shopify.order.create`

**Description:** Create an order in Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `line_items` | array | ✓ | Order line items with title, price, quantity |
| `customer` | object |  | Customer info (id or email) |
| `billing_address` | object |  | Billing address |
| `shipping_address` | object |  | Shipping address |
| `financial_status` | string |  | Payment status |
| `send_receipt` | boolean |  | Send receipt email to customer |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Created order ID |
| `name` | string | Order number |
| `total_price` | string | Total price |

---

### `shopify.order.get`

**Description:** Get order details from Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `order_id` | string | ✓ | Shopify order ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Order ID |
| `name` | string | Order number (#1001) |
| `email` | string | Customer email |
| `created_at` | string | Created timestamp |
| `total_price` | string | Total price |
| `subtotal_price` | string | Subtotal |
| `total_tax` | string | Tax amount |
| `total_discounts` | string | Discounts |
| `financial_status` | string | Payment status |
| `fulfillment_status` | string | Fulfillment |
| `line_items` | array | Order items |
| `shipping_lines` | array | Shipping |
| `refunds` | array | Any refunds |

---

### `shopify.order.update`

**Description:** Update an order in Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `order_id` | string | ✓ | Shopify order ID |
| `note` | string |  | Order note |
| `tags` | string |  | Comma-separated tags |
| `email` | string |  | Customer email |
| `shipping_address` | object |  | Updated shipping address |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Order ID |
| `updated_at` | string | Update timestamp |

---

### `shopify.orders.count`

**Description:** Get order count from Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Order status filter |
| `financial_status` | string |  | Financial status filter |
| `created_at_min` | string |  | Filter orders created after this date |
| `created_at_max` | string |  | Filter orders created before this date |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Order count |

---

### `shopify.orders.list`

**Description:** List orders from Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Order status filter |
| `financial_status` | string |  | Financial status filter |
| `fulfillment_status` | string |  | Fulfillment status filter |
| `created_at_min` | string |  | Filter orders created after this date |
| `created_at_max` | string |  | Filter orders created before this date |
| `limit` | integer |  | Max 250 |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `orders` | array | Orders with id, name, total_price, financial_status, line_it |
| `count` | integer | Order count |

---

### `shopify.payouts.list`

**Description:** List Shopify Payments payouts

> Lists payouts from Shopify Payments to your bank account. Useful for reconciling deposits.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Payout status filter |
| `date_min` | string |  | Filter payouts after this date |
| `date_max` | string |  | Filter payouts before this date |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payouts` | array | Payouts with id, date, amount, status |
| `count` | integer | Payout count |

---

### `shopify.products.list`

**Description:** List products from Shopify

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string |  | Product status filter |
| `product_type` | string |  | Filter by product type |
| `vendor` | string |  | Filter by vendor name |
| `limit` | integer |  | Maximum products to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `products` | array | Products with id, title, vendor, product_type, variants |
| `count` | integer | Product count |

---

### `shopify.shop.get`

**Description:** Get Shopify shop information

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Shop ID |
| `name` | string | Shop name |
| `email` | string | Shop email |
| `domain` | string | Primary domain |
| `currency` | string | Currency code |
| `timezone` | string | Timezone |
| `plan_name` | string | Shopify plan |

---

## SQUARE (19 capabilities)

### `square.customers.create`

**Description:** Create a customer in Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `idempotency_key` | string | ✓ | Unique key for idempotency |
| `given_name` | string |  | Customer first name |
| `family_name` | string |  | Customer last name |
| `company_name` | string |  | Company name |
| `email_address` | string |  | Email address |
| `phone_number` | string |  | Phone number |
| `reference_id` | string |  | External reference ID |
| `note` | string |  | Customer note |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | string | Created customer ID |

---

### `square.customers.list`

**Description:** List customers from Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cursor` | string |  | Pagination cursor |
| `limit` | integer |  | Maximum customers to return |
| `sort_field` | string |  | Field to sort by |
| `sort_order` | string |  | Sort order |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customers` | array | Customers with id, given_name, family_name, email, phone |
| `cursor` | string | Pagination cursor |

---

### `square.customers.update`

**Description:** Update a customer in Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | string | ✓ | Square customer ID |
| `given_name` | string |  | Customer first name |
| `family_name` | string |  | Customer last name |
| `email_address` | string |  | Email address (null to clear) |
| `phone_number` | string |  | Phone number (null to clear) |
| `note` | string |  | Customer note |
| `version` | integer |  | Current version for optimistic locking |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | string | Updated customer ID |
| `version` | integer | New version |

---

### `square.invoices.cancel`

**Description:** Cancel a published invoice

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Square invoice ID |
| `version` | integer | ✓ | Current invoice version |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Cancelled invoice ID |
| `status` | string | Should be CANCELED |

---

### `square.invoices.create`

**Description:** Create an invoice in Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `idempotency_key` | string | ✓ | Unique key for idempotency |
| `location_id` | string | ✓ | Location ID |
| `order_id` | string | ✓ | Order ID to invoice |
| `primary_recipient` | object | ✓ | Customer recipient |
| `payment_requests` | array | ✓ | Payment request details |
| `delivery_method` | string |  | How to deliver the invoice |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Created invoice ID |
| `invoice_number` | string | Invoice number |
| `status` | string | DRAFT, UNPAID, etc. |

---

### `square.invoices.get`

**Description:** Get invoice details from Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Square invoice ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Invoice ID |
| `invoice_number` | string | Invoice number |
| `status` | string | DRAFT, SCHEDULED, etc. |
| `version` | integer | Invoice version |
| `primary_recipient` | object | Customer info |
| `payment_requests` | array | Payment requests |

---

### `square.invoices.list`

**Description:** List invoices from Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_id` | string | ✓ | Location ID |
| `cursor` | string |  | Pagination cursor |
| `limit` | integer |  | Maximum invoices to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoices` | array | Invoices with id, invoice_number, status, payment_requests |
| `cursor` | string | Pagination cursor |

---

### `square.invoices.publish`

**Description:** Publish a draft invoice to send to customer

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Square invoice ID |
| `version` | integer | ✓ | Current invoice version |
| `idempotency_key` | string |  | Unique key for idempotency |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Published invoice ID |
| `status` | string | Should be UNPAID or SCHEDULED |
| `public_url` | string | Customer payment URL |

---

### `square.invoices.update`

**Description:** Update an invoice in Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `invoice_id` | string | ✓ | Square invoice ID |
| `version` | integer | ✓ | Current invoice version |
| `invoice` | object | ✓ | Invoice fields to update |
| `idempotency_key` | string |  | Unique key for idempotency |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | string | Updated invoice ID |
| `version` | integer | New version |

---

### `square.locations.list`

**Description:** List Square locations (stores)

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `locations` | array | Locations with id, name, address, timezone, currency |
| `count` | integer | Location count |

---

### `square.orders.create`

**Description:** Create an order in Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `idempotency_key` | string | ✓ | Unique key for idempotency |
| `location_id` | string | ✓ | Location ID for the order |
| `line_items` | array |  | Order line items |
| `reference_id` | string |  | External reference ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `order_id` | string | Created order ID |
| `state` | string | Order state |

---

### `square.orders.get`

**Description:** Get order details from Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `order_id` | string | ✓ | Square order ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Order ID |
| `location_id` | string | Location |
| `line_items` | array | Order items |
| `total_money` | object | Total |
| `total_tax_money` | object | Tax |
| `total_discount_money` | object | Discounts |
| `state` | string | OPEN, COMPLETED, etc. |
| `tenders` | array | Payment tenders |
| `refunds` | array | Refunds |

---

### `square.orders.list`

**Description:** Search/list orders from Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_ids` | array | ✓ | Location IDs to search |
| `query` | object |  | Search query filters |
| `limit` | integer |  | Maximum orders to return |
| `cursor` | string |  | Pagination cursor |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `orders` | array | Orders with id, location_id, line_items, total_money, state |
| `cursor` | string | Pagination cursor |

---

### `square.orders.update`

**Description:** Update an order in Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `order_id` | string | ✓ | Square order ID |
| `fields_to_clear` | array |  | Fields to clear from the order |
| `order` | object |  | Order fields to update |
| `idempotency_key` | string |  | Unique key for idempotency |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `order_id` | string | Updated order ID |
| `version` | integer | New order version |

---

### `square.payments.create`

**Description:** Create a payment in Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source_id` | string | ✓ | Payment source (card nonce, card on file, etc.) |
| `amount_money` | object | ✓ | Amount with currency {amount: cents, currency: 'USD'} |
| `idempotency_key` | string | ✓ | Unique key for idempotency |
| `location_id` | string |  | Location ID |
| `customer_id` | string |  | Customer ID to associate |
| `reference_id` | string |  | External reference ID |
| `note` | string |  | Payment note |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | Created payment ID |
| `status` | string | Payment status |
| `receipt_url` | string | Receipt URL |

---

### `square.payments.get`

**Description:** Get payment details from Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_id` | string | ✓ | Square payment ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payment ID |
| `amount_money` | object | Amount with currency |
| `status` | string | COMPLETED, FAILED, etc. |
| `source_type` | string | CARD, CASH, etc. |
| `location_id` | string | Location ID |
| `order_id` | string | Associated order |
| `created_at` | string | Created timestamp |
| `processing_fee` | array | Processing fees |
| `card_details` | object | Card info if card |

---

### `square.payments.list`

**Description:** List payments from Square

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_id` | string |  | Filter by location ID |
| `begin_time` | string |  | Filter payments after this time |
| `end_time` | string |  | Filter payments before this time |
| `sort_order` | string |  | Sort order |
| `cursor` | string |  | Pagination cursor |
| `limit` | integer |  | Maximum payments to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payments` | array | Payments with id, amount, status, source_type, created_at |
| `cursor` | string | Pagination cursor |

---

### `square.payments.refund`

**Description:** Refund a Square payment

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `payment_id` | string | ✓ | Payment ID to refund |
| `idempotency_key` | string | ✓ | Unique key for idempotency |
| `amount_money` | object | ✓ | Amount to refund |
| `reason` | string |  | Reason for refund |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `refund_id` | string | Refund ID |
| `status` | string | PENDING, COMPLETED, etc. |
| `amount_money` | object | Refunded amount |

---

### `square.payouts.list`

**Description:** List payouts from Square

> Lists payouts to your bank account. Use for reconciliation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location_id` | string |  | Filter by location ID |
| `status` | string |  | Payout status filter |
| `begin_time` | string |  | Filter payouts after this time |
| `end_time` | string |  | Filter payouts before this time |
| `cursor` | string |  | Pagination cursor |
| `limit` | integer |  | Maximum payouts to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payouts` | array | Payouts with id, status, amount, arrival_date |
| `cursor` | string | Pagination cursor |

---

## AIRTABLE (13 capabilities)

### `airtable.bases.list`

**Description:** List bases accessible to the user

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `bases` | array | Bases with id, name, permission_level |

---

### `airtable.fields.create`

**Description:** Create a new field in an Airtable table

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `table_id` | string | ✓ | Table ID or name |
| `name` | string | ✓ | Field name |
| `type` | string | ✓ | Field type to create |
| `options` | object |  | Type-specific options (e.g., select choices) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Field ID |
| `name` | string | Field name |
| `type` | string | Field type |

---

### `airtable.fields.update`

**Description:** Update a field's name or description

> Updates an existing field. Only name and description can be modified. Field type cannot be changed after creation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `table_id` | string | ✓ | Table ID |
| `field_id` | string | ✓ | Field ID to update |
| `name` | string |  | New field name |
| `description` | string |  | New field description |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Field ID |
| `name` | string | Updated field name |
| `type` | string | Field type (unchanged) |
| `description` | string | Updated description |

---

### `airtable.records.create`

**Description:** Create record(s) in Airtable

> Creates one or more records in an Airtable table. Can create up to 10 records per request.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `table_id` | string | ✓ | Table ID or name |
| `records` | array | ✓ | Records to create, each with {fields: {...}} |
| `typecast` | boolean |  | Auto-convert strings to proper field types |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `records` | array | Created records with id, created_time, fields |

---

### `airtable.records.delete`

**Description:** Delete record(s) from Airtable

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `table_id` | string | ✓ | Table ID or name |
| `record_ids` | array | ✓ | Record IDs to delete (max 10) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `records` | array | Deleted records with id and deleted: true |

---

### `airtable.records.get`

**Description:** Get a specific record from Airtable

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `table_id` | string | ✓ | Table ID or name |
| `record_id` | string | ✓ | Airtable record ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Record ID |
| `created_time` | string | Created timestamp |
| `fields` | object | Field values |

---

### `airtable.records.list`

**Description:** List records from an Airtable table

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `table_id` | string | ✓ | Table ID or name |
| `view` | string |  | View ID or name |
| `fields` | array |  | Field names to return |
| `filter_by_formula` | string |  | Airtable formula to filter records |
| `sort` | array |  | Sort specification [{field, direction}] |
| `max_records` | integer |  | Maximum records to return |
| `page_size` | integer |  | Records per page (max 100) |
| `offset` | string |  | Pagination offset |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `records` | array | Records with id, created_time, fields |
| `offset` | string | Offset for next page (if more records) |

---

### `airtable.records.update`

**Description:** Update record(s) in Airtable

> Updates one or more records. PATCH updates only specified fields, PUT replaces all fields.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `table_id` | string | ✓ | Table ID or name |
| `records` | array | ✓ | Records to update, each with {id, fields: {...}} |
| `typecast` | boolean |  | Auto-convert types |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `records` | array | Updated records with id, created_time, fields |

---

### `airtable.tables.create`

**Description:** Create a new table in a base

> Creates a new table with specified fields. At least one field must be provided. The first field becomes the primary field.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `name` | string | ✓ | Table name |
| `description` | string |  | Table description |
| `fields` | array | ✓ | Fields to create with name, type, and optional options |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Created table ID |
| `name` | string | Table name |
| `primary_field_id` | string | Primary field ID |
| `fields` | array | Created fields |

---

### `airtable.tables.list`

**Description:** List tables in a base

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `tables` | array | Tables with id, name, primary_field_id, fields, views |

---

### `airtable.webhooks.create`

**Description:** Create a webhook for record changes

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `notification_url` | string | ✓ | URL to receive notifications |
| `specification` | object | ✓ | Webhook specification (triggers, data types) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Webhook ID |
| `mac_secret_base64` | string | Secret for verifying payloads |
| `expiration_time` | string | Expiration |

---

### `airtable.webhooks.delete`

**Description:** Delete a webhook

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |
| `webhook_id` | string | ✓ | Webhook ID to delete |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `deleted` | boolean | True if successfully deleted |

---

### `airtable.webhooks.list`

**Description:** List webhooks for a base

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_id` | string | ✓ | Airtable base ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `webhooks` | array | Webhooks with id, notification_url, specification |

---

## GUSTO (14 capabilities)

### `gusto.company.get`

**Description:** Get Gusto company information

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Company UUID |
| `name` | string | Company name |
| `ein` | string | Employer ID Number |
| `entity_type` | string | LLC, Corp, etc. |
| `locations` | array | Work locations |

---

### `gusto.contractor.create`

**Description:** Create a contractor in Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |
| `first_name` | string | ✓ | Contractor first name |
| `last_name` | string | ✓ | Contractor last name |
| `start_date` | string | ✓ | Contract start date (YYYY-MM-DD) |
| `type` | string |  | Contractor type |
| `wage_type` | string |  | How contractor is paid |
| `hourly_rate` | string |  | Hourly rate if wage_type is Hourly |
| `self_onboarding` | boolean |  | Allow contractor to self-onboard |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Created contractor UUID |

---

### `gusto.contractor_payments.list`

**Description:** List contractor payments from Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |
| `start_date` | string |  | Filter start date (YYYY-MM-DD) |
| `end_date` | string |  | Filter end date (YYYY-MM-DD) |
| `contractor_id` | string |  | Filter by contractor UUID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payments` | array | Payments with contractor, date, amount, reimbursements |
| `count` | integer | Payment count |

---

### `gusto.contractors.list`

**Description:** List contractors from Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `contractors` | array | Contractors with id, name, email, type (individual/business) |
| `count` | integer | Contractor count |

---

### `gusto.employee.create`

**Description:** Create an employee in Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |
| `first_name` | string | ✓ | Employee first name |
| `last_name` | string | ✓ | Employee last name |
| `email` | string | ✓ | Employee email address |
| `date_of_birth` | string |  | Date of birth (YYYY-MM-DD) |
| `ssn` | string |  | Social Security Number |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Created employee UUID |
| `status` | string | Should be 'created' |

---

### `gusto.employee.get`

**Description:** Get employee details from Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `employee_id` | string | ✓ | Gusto employee UUID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Employee UUID |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `email` | string | Email |
| `ssn` | string | Last 4 of SSN |
| `date_of_birth` | string | DOB |
| `jobs` | array | Job assignments |
| `compensations` | array | Pay rates |
| `home_address` | object | Address |

---

### `gusto.employee.terminate`

**Description:** Terminate an employee in Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `employee_id` | string | ✓ | Gusto employee UUID |
| `effective_date` | string | ✓ | Last day of work (YYYY-MM-DD) |
| `run_termination_payroll` | boolean |  | Run a separate termination payroll |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Termination UUID |
| `employee_id` | string | Employee UUID |
| `effective_date` | string | Termination date |

---

### `gusto.employee.update`

**Description:** Update an employee in Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `employee_id` | string | ✓ | Gusto employee UUID |
| `version` | string | ✓ | Current version for optimistic locking |
| `first_name` | string |  | Employee first name |
| `last_name` | string |  | Employee last name |
| `email` | string |  | Employee email address |
| `date_of_birth` | string |  | Date of birth (YYYY-MM-DD) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Employee UUID |
| `version` | string | New version |

---

### `gusto.employees.list`

**Description:** List employees from Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |
| `terminated` | boolean |  | Include terminated employees |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `employees` | array | Employees with id, first_name, last_name, email, department |
| `count` | integer | Employee count |

---

### `gusto.payroll.calculate`

**Description:** Calculate payroll (preview before submitting)

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |
| `payroll_id` | string | ✓ | Payroll UUID to calculate |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payroll_id` | string | Payroll UUID |
| `totals` | object | Calculated totals |
| `employee_compensations` | array | Per-employee calculations |

---

### `gusto.payroll.get`

**Description:** Get payroll details from Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |
| `payroll_id` | string | ✓ | Payroll UUID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payroll UUID |
| `pay_period` | object | Start/end dates |
| `check_date` | string | Check date |
| `processed` | boolean | Is processed |
| `totals` | object | Gross pay, net pay, employer taxes, employee taxes |
| `employee_compensations` | array | Per-employee breakdown |

---

### `gusto.payroll.submit`

**Description:** Submit payroll for processing

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |
| `payroll_id` | string | ✓ | Payroll UUID to submit |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payroll_id` | string | Submitted payroll |
| `status` | string | Should be 'processed' |

---

### `gusto.payrolls.list`

**Description:** List payroll runs from Gusto

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |
| `start_date` | string |  | Filter start date (YYYY-MM-DD) |
| `end_date` | string |  | Filter end date (YYYY-MM-DD) |
| `processed` | boolean |  | Only return processed payrolls |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payrolls` | array | Payrolls with id, pay_period, check_date, totals, status |
| `count` | integer | Payroll count |

---

### `gusto.tax_forms.list`

**Description:** List tax forms from Gusto (W-2s, 1099s)

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | Gusto company UUID |
| `year` | integer | ✓ | Tax year (e.g., 2025) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `forms` | array | Tax forms (W-2s and 1099s) with employee/contractor, wages,  |
| `count` | integer | Form count |

---

## MONDAY (13 capabilities)

### `monday.board.get`

**Description:** Get board details from Monday.com with columns and groups

> Get full details of a specific board including all columns (fields), groups (sections), and owner information. Essential for understanding board structure before creating or updating items.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | string | ✓ | Board ID to retrieve |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Board ID |
| `name` | string | Board name |
| `description` | string | Board description |
| `state` | string | Board state |
| `board_kind` | string | public/private/share |
| `item_count` | integer | Number of items |
| `columns` | array | Column definitions with id, title, type, settings |
| `groups` | array | Group definitions with id, title, color |
| `owner` | object | Board owner details |

---

### `monday.board.list`

**Description:** List boards in Monday.com workspace

> Get all boards accessible to the authenticated user. Supports filtering by board kind (public/private) and state (active/archived).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number of boards to return (default: 25) |
| `board_kind` | string |  | Filter by board kind |
| `state` | string |  | Filter by state |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of boards returned |
| `boards` | array | List of boards with id, name, description, state, item_count |

---

### `monday.column.change_multiple_values`

**Description:** Change multiple column values on Monday.com item at once

> Update multiple column values for an item in a single request. More efficient than multiple single column updates.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | string | ✓ | Board ID |
| `item_id` | string | ✓ | Item ID to update |
| `column_values` | object | ✓ | Dictionary of column_id -> value (e.g., {"status": {"label": |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Updated item ID |
| `name` | string | Item name |

---

### `monday.column.change_value`

**Description:** Change single column value on Monday.com item (status, date, text)

> Update a single column value for an item. Column value format depends on column type: {"label": "Done"} for status, {"date": "2025-01-15"} for date, {"text": "value"} for text.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | string | ✓ | Board ID |
| `item_id` | string | ✓ | Item ID to update |
| `column_id` | string | ✓ | Column ID to update |
| `value` | object | ✓ | JSON value for the column (e.g., {"label": "Done"}) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Updated item ID |
| `name` | string | Item name |

---

### `monday.group.create`

**Description:** Create group on Monday.com board

> Create a new group (section) on a board. Groups help organize items by category, status, or workflow stage.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | string | ✓ | Board ID to create group on |
| `group_name` | string | ✓ | Name for the new group |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Created group ID |
| `title` | string | Group title |
| `color` | string | Group color |

---

### `monday.item.create`

**Description:** Create item on Monday.com board for finance workflows

> Create a new item (row) on a Monday.com board. Optionally specify a group and initial column values. Use for invoice tracking, approval workflows, and month-end close tasks.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | string | ✓ | Board ID to create item on |
| `item_name` | string | ✓ | Name for the new item |
| `group_id` | string |  | Group ID to add item to (defaults to first group) |
| `column_values` | object |  | JSON object of column values (e.g., {"status": {"label": "Do |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Created item ID |
| `name` | string | Item name |
| `url` | string | Relative link to item |
| `state` | string | Item state |
| `created_at` | string | Creation timestamp |

---

### `monday.item.get`

**Description:** Get item details from Monday.com

> Retrieve full details of a specific item including all column values, creator, board, and group information.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_id` | string | ✓ | Item ID to retrieve |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Item ID |
| `name` | string | Item name |
| `state` | string | Item state |
| `url` | string | Relative link to item |
| `created_at` | string | Creation timestamp |
| `updated_at` | string | Last update timestamp |
| `creator` | object | Creator details |
| `column_values` | array | All column values with id, title, type, text, value |
| `board` | object | Parent board details |
| `group` | object | Parent group details |

---

### `monday.item.list`

**Description:** List items on Monday.com board with pagination

> List all items on a board with pagination support. Returns items with their column values for filtering and display.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | string | ✓ | Board ID to list items from |
| `limit` | integer |  | Max items per page (default: 50, max: 100) |
| `cursor` | string |  | Pagination cursor for next page |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of items in this page |
| `items` | array | Items with id, name, state, url, created_at, column_values |
| `cursor` | string | Cursor for next page (null if no more pages) |

---

### `monday.item.update`

**Description:** Update item name on Monday.com

> Update an item's name. To update column values, use monday.column.change_value or monday.column.change_multiple_values.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_id` | string | ✓ | Item ID to update |
| `item_name` | string | ✓ | New name for the item |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Updated item ID |
| `name` | string | New item name |

---

### `monday.update.create`

**Description:** Create update (comment) on Monday.com item

> Post an update (comment) on a Monday.com item. Updates appear in the item's activity feed and can trigger notifications.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_id` | string | ✓ | Item ID to comment on |
| `body` | string | ✓ | Update text/body |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Update ID |
| `body` | string | Update body |
| `creator` | object | Creator details |
| `created_at` | string | Creation timestamp |

---

### `monday.update.list`

**Description:** Get all updates (comments) on Monday.com item

> Retrieve all updates (comments) for a specific item. Useful for viewing approval history and team discussions.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `item_id` | string | ✓ | Item ID to get updates for |
| `limit` | integer |  | Max updates to return (default: 25) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of updates |
| `updates` | array | Updates with id, body, creator, created_at |

---

### `monday.user.get_current`

**Description:** Get current authenticated Monday.com user

> Get details of the currently authenticated user, including account information.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | User ID |
| `name` | string | User name |
| `email` | string | User email |
| `title` | string | User title |
| `account` | object | Account details with id, name, slug |

---

### `monday.user.list`

**Description:** Get users in Monday.com account

> List all users in the Monday.com account. Can filter by user kind (guests, non-guests, pending).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `kind` | string |  | Filter by user kind (default: all) |
| `limit` | integer |  | Max users to return (default: 50) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of users |
| `users` | array | Users with id, name, email, enabled, is_guest, title |

---

## BREX (8 capabilities)

### `brex.balance.get`

**Description:** Get cash account balance

> Get current and available balances for Brex Cash accounts. Shows all cash accounts with their respective balances.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Brex OAuth access token |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | Cash accounts with account_id, name, current_balance, availa |

---

### `brex.card.limit.update`

**Description:** Update card spending limit

> Update the spending limit for an existing card. Can increase or decrease the limit.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Brex OAuth access token |
| `card_id` | string | ✓ | Card ID to update |
| `new_limit` | number | ✓ | New spending limit amount |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `card_id` | string | Updated card ID |
| `new_limit` | number | New spending limit |
| `status` | string | Should be 'updated' |

---

### `brex.card.lock`

**Description:** Lock a card in Brex

> Lock a card to prevent new transactions. Useful for suspected fraud, employee offboarding, or temporary spend freezes.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Brex OAuth access token |
| `card_id` | string | ✓ | Card ID to lock |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `card_id` | string | Locked card ID |
| `status` | string | Should be 'locked' |

---

### `brex.card.unlock`

**Description:** Unlock a card in Brex

> Unlock a previously locked card to resume transactions. Card returns to active status.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Brex OAuth access token |
| `card_id` | string | ✓ | Card ID to unlock |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `card_id` | string | Unlocked card ID |
| `status` | string | Should be 'active' |

---

### `brex.card.virtual.create`

**Description:** Create virtual card with spending limits

> Create a new virtual card with configurable spending limits. Assign to a user and set monthly or per-transaction limits.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Brex OAuth access token |
| `user_id` | string | ✓ | Brex user ID to assign card to |
| `display_name` | string | ✓ | Card display name |
| `spend_limit` | number | ✓ | Spending limit amount |
| `limit_duration` | string |  | Limit duration (default: MONTHLY) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `card_id` | string | Created card ID |
| `last_four` | string | Last 4 digits of card number |
| `status` | string | Card status |

---

### `brex.expense.list`

**Description:** List expenses with categories in Brex

> List expenses with category assignments, memos, and receipts. Useful for expense reporting and reconciliation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Brex OAuth access token |
| `limit` | integer |  | Max expenses to return (default: 100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `expenses` | array | Expenses with id, amount, memo, category, receipts, purchase |

---

### `brex.payment.create`

**Description:** Create vendor payment in Brex

> Create a vendor payment from Brex Cash account. Requires a counterparty (vendor) to be set up in Brex.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Brex OAuth access token |
| `counterparty_id` | string | ✓ | Brex counterparty (vendor) ID |
| `amount` | number | ✓ | Payment amount |
| `currency` | string |  | Payment currency (default: USD) |
| `description` | string |  | Payment description/memo |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | Created payment ID |
| `status` | string | Payment status |
| `amount` | object | Payment amount with currency |

---

### `brex.transaction.list`

**Description:** List card transactions in Brex

> List card transactions within a date range. Includes merchant details, card info, and posting status. Supports cursor-based pagination.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Brex OAuth access token |
| `start_date` | string |  | Start date (ISO 8601) |
| `end_date` | string |  | End date (ISO 8601) |
| `limit` | integer |  | Max transactions to return (default: 100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `transactions` | array | Transactions with id, amount, merchant_name, card_id, user_i |
| `next_cursor` | string | Cursor for next page (null if no more) |

---

## MERCURY (6 capabilities)

### `mercury.account.list`

**Description:** List Mercury banking accounts

> List all Mercury bank accounts for the organization. Returns account details including balances, account types, and status.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | Accounts with account_id, name, type, balance, currency, sta |

---

### `mercury.payment.create`

**Description:** Create ACH payment (100 free/month)

> Create an ACH payment from a Mercury account to a recipient. Mercury offers 100 free ACH payments per month. Use idempotency_key to prevent duplicate payments.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Mercury account ID to pay from |
| `recipient_id` | string | ✓ | Recipient ID (create with mercury.recipient.create) |
| `amount` | number | ✓ | Payment amount in USD |
| `description` | string |  | Payment description (default: 'Payment via Stargate') |
| `idempotency_key` | string |  | Unique key to prevent duplicate payments |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | Created payment ID |
| `status` | string | Payment status |
| `amount` | number | Payment amount |
| `estimated_delivery` | string | Estimated delivery date |

---

### `mercury.recipient.create`

**Description:** Create payment recipient

> Create a payment recipient in Mercury with bank account details. Required before creating ACH payments or wire transfers.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | ✓ | Recipient name |
| `email` | string |  | Recipient email address |
| `routing_number` | string | ✓ | Bank routing number (9 digits) |
| `account_number` | string | ✓ | Bank account number |
| `account_type` | string |  | Account type (default: checking) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `recipient_id` | string | Created recipient ID |
| `name` | string | Recipient name |
| `status` | string | Recipient status |

---

### `mercury.recipient.list`

**Description:** List payment recipients

> List all payment recipients configured in Mercury. Use to find recipient_id for payments.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `recipients` | array | Recipients with recipient_id, name, email, status |

---

### `mercury.transaction.get`

**Description:** Get transactions from Mercury

> Get transactions for a Mercury account within a date range. Supports pagination via offset parameter.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Mercury account ID |
| `start_date` | string |  | Start date (YYYY-MM-DD) |
| `end_date` | string |  | End date (YYYY-MM-DD) |
| `limit` | integer |  | Max transactions to return (default: 100) |
| `offset` | integer |  | Pagination offset (default: 0) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `transactions` | array | Transactions with transaction_id, amount, description, statu |
| `total` | integer | Total transaction count |

---

### `mercury.wire.create`

**Description:** Create wire transfer (domestic/international)

> Create a wire transfer from a Mercury account. Mercury offers free domestic and international wire transfers. Faster than ACH but typically used for larger or time-sensitive payments.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | string | ✓ | Mercury account ID to wire from |
| `recipient_id` | string | ✓ | Recipient ID (create with mercury.recipient.create) |
| `amount` | number | ✓ | Wire amount in USD |
| `wire_type` | string |  | Wire type (default: domestic) |
| `description` | string |  | Wire transfer description/reference |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `wire_id` | string | Created wire transfer ID |
| `status` | string | Wire status |
| `amount` | number | Wire amount |
| `fee` | number | Wire fee (typically $0 for Mercury) |

---

## ASANA (12 capabilities)

### `asana.attachment.upload`

**Description:** Upload attachment to task

> Upload a file attachment to a task. Useful for attaching invoices, receipts, or documentation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `task_gid` | string | ✓ | Task GID to attach file to |
| `file_content` | string | ✓ | File content (base64 encoded or binary stream) |
| `file_name` | string | ✓ | Name for the uploaded file |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `attachment_gid` | string | Uploaded attachment GID |
| `name` | string | Attachment name |
| `download_url` | string | Download URL (temporary) |
| `permanent_url` | string | Permanent Asana URL |

---

### `asana.customfield.add`

**Description:** Add custom field to project

> Add an existing custom field to a project. Custom fields must be created in Asana first, then can be added to multiple projects.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `project_gid` | string | ✓ | Project GID to add field to |
| `custom_field_gid` | string | ✓ | Custom field GID to add |
| `insert_before` | string |  | Field GID to insert before (for ordering) |
| `insert_after` | string |  | Field GID to insert after (for ordering) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `custom_field_setting_gid` | string | Custom field setting GID |
| `custom_field` | object | Custom field details |
| `project` | object | Project details |

---

### `asana.customfield.update`

**Description:** Update custom field on task

> Update the value of a custom field on a task. The value format depends on the field type (text, number, enum, etc.).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `task_gid` | string | ✓ | Task GID to update |
| `custom_field_gid` | string | ✓ | Custom field GID |
| `value` | object | ✓ | New value (type depends on field type - can be string, numbe |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `task_gid` | string | Updated task GID |
| `custom_fields` | array | Updated custom fields |

---

### `asana.project.create`

**Description:** Create project in Asana

> Create a new project in Asana. Can be a list or board layout. Optionally assign to a team and set owner.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `project_name` | string | ✓ | Name for the project |
| `workspace_gid` | string | ✓ | Workspace GID |
| `notes` | string |  | Project description |
| `layout` | string |  | Project layout (default: list) |
| `team` | string |  | Team GID to assign project to |
| `color` | string |  | Project color |
| `owner` | string |  | Owner user GID |
| `due_date` | string |  | Project due date (YYYY-MM-DD) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `project_gid` | string | Created project GID |
| `name` | string | Project name |
| `permalink_url` | string | Direct link to project |
| `created_at` | string | Creation timestamp |

---

### `asana.project.get`

**Description:** Get project details

> Retrieve full details of a specific project including members, custom fields, owner, and team information.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `project_gid` | string | ✓ | Project GID to retrieve |
| `opt_fields` | string |  | Comma-separated fields to include |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `project_gid` | string | Project GID |
| `name` | string | Project name |
| `notes` | string | Project description |
| `color` | string | Project color |
| `completed` | boolean | Completion status |
| `owner` | object | Owner details |
| `team` | object | Team details |
| `members` | array | Project members |
| `custom_fields` | array | Custom field settings |
| `permalink_url` | string | Direct link to project |

---

### `asana.project.list`

**Description:** List projects in workspace

> List all projects in a workspace. Returns projects with basic information including owner and completion status.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `workspace_gid` | string | ✓ | Workspace GID to list projects from |
| `opt_fields` | string |  | Comma-separated fields to include (default: name,owner,compl |
| `limit` | integer |  | Max projects to return (default: 100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `projects` | array | Projects with project_gid, name, owner, completed |

---

### `asana.section.addtask`

**Description:** Add task to section

> Move a task into a section within a project. Can optionally specify position within the section.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `section_gid` | string | ✓ | Section GID to add task to |
| `task_gid` | string | ✓ | Task GID to move |
| `insert_before` | string |  | Task GID to insert before (for ordering) |
| `insert_after` | string |  | Task GID to insert after (for ordering) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Operation success |
| `section_gid` | string | Section GID |
| `task_gid` | string | Task GID |

---

### `asana.section.create`

**Description:** Create section in project

> Create a new section in a project. Sections help organize tasks into groups like 'To Do', 'In Progress', 'Complete'.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `project_gid` | string | ✓ | Project GID to create section in |
| `section_name` | string | ✓ | Name for the section |
| `insert_before` | string |  | Section GID to insert before (for ordering) |
| `insert_after` | string |  | Section GID to insert after (for ordering) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `section_gid` | string | Created section GID |
| `name` | string | Section name |
| `project` | object | Parent project details |
| `created_at` | string | Creation timestamp |

---

### `asana.task.create`

**Description:** Create task in Asana

> Create a new task in Asana. Can be added to one or more projects, assigned to a user, and include custom fields. Supports subtasks via parent field.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `task_name` | string | ✓ | Name for the task |
| `workspace_gid` | string | ✓ | Workspace GID |
| `projects` | array |  | Array of project GIDs to add task to |
| `notes` | string |  | Task description/notes |
| `assignee` | string |  | User GID to assign task to |
| `due_on` | string |  | Due date (YYYY-MM-DD) |
| `due_at` | string |  | Due datetime (ISO 8601) |
| `custom_fields` | object |  | Custom field values as {field_gid: value} |
| `parent` | string |  | Parent task GID (for creating subtasks) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `task_gid` | string | Created task GID |
| `name` | string | Task name |
| `permalink_url` | string | Direct link to task |
| `created_at` | string | Creation timestamp |

---

### `asana.task.get`

**Description:** Get task details

> Retrieve full details of a specific task including custom fields, projects, tags, and assignee information.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `task_gid` | string | ✓ | Task GID to retrieve |
| `opt_fields` | string |  | Comma-separated fields to include |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `task_gid` | string | Task GID |
| `name` | string | Task name |
| `notes` | string | Task description |
| `completed` | boolean | Completion status |
| `assignee` | object | Assignee details |
| `due_on` | string | Due date |
| `custom_fields` | array | Custom field values |
| `projects` | array | Projects task belongs to |
| `tags` | array | Task tags |
| `permalink_url` | string | Direct link to task |

---

### `asana.task.list`

**Description:** List tasks in project

> List all tasks in a specific project. Returns tasks with basic information including completion status and assignee.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `project_gid` | string | ✓ | Project GID to list tasks from |
| `opt_fields` | string |  | Comma-separated fields to include (default: name,completed,a |
| `limit` | integer |  | Max tasks to return (default: 100) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `tasks` | array | Tasks with task_gid, name, completed, assignee, due_on |

---

### `asana.task.update`

**Description:** Update existing task

> Update an existing task's properties. Only provided fields are updated. Can mark tasks complete, reassign, or update custom fields.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Asana OAuth access token |
| `task_gid` | string | ✓ | Task GID to update |
| `name` | string |  | New task name |
| `notes` | string |  | New description/notes |
| `completed` | boolean |  | Mark task as complete/incomplete |
| `assignee` | string |  | New assignee GID (null to unassign) |
| `due_on` | string |  | New due date (YYYY-MM-DD, null to clear) |
| `custom_fields` | object |  | Custom field values to update |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `task_gid` | string | Updated task GID |
| `name` | string | Task name |
| `completed` | boolean | Completion status |
| `modified_at` | string | Last modification timestamp |

---

## HUBSPOT (18 capabilities)

### `crm.company.create`

**Description:** Create a company in HubSpot CRM

> Creates a new company record in HubSpot CRM. Companies represent organizations you do business with.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_name` | string | ✓ | Company name |
| `domain` | string |  | Company website domain |
| `industry` | string |  | Industry category |
| `phone` | string |  | Company phone number |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `company_id` | string | HubSpot company ID (prefixed with hs:) |
| `company_name` | string | Company name |
| `domain` | string | Website domain |
| `created_at` | string | Creation timestamp |

---

### `crm.company.delete`

**Description:** Delete a company from HubSpot CRM

> Permanently deletes a company from HubSpot.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | HubSpot company ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `company_id` | string | Company ID |
| `status` | string | Should be 'deleted' |

---

### `crm.company.get`

**Description:** Get company details from HubSpot CRM

> Retrieves details for a specific company by ID.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | HubSpot company ID (with or without hs: prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `company_id` | string | Company ID |
| `company_name` | string | Company name |
| `domain` | string | Website domain |
| `industry` | string | Industry |

---

### `crm.company.list`

**Description:** List companies from HubSpot CRM

> Retrieves a list of companies from HubSpot CRM.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number of companies to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `companies` | array | List of company objects |
| `count` | integer | Number of companies |

---

### `crm.company.search`

**Description:** Search companies in HubSpot CRM

> Searches for companies using HubSpot's search API.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ | Search query string |
| `limit` | integer |  | Maximum number of results |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Search query used |
| `companies` | array | Matching companies |
| `count` | integer | Number of results |

---

### `crm.company.update`

**Description:** Update a company in HubSpot CRM

> Updates an existing company's properties in HubSpot.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_id` | string | ✓ | HubSpot company ID |
| `company_name` | string |  | Updated company name |
| `domain` | string |  | Updated website domain |
| `industry` | string |  | Updated industry |
| `phone` | string |  | Updated phone number |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `company_id` | string | Company ID |
| `company_name` | string | Company name |
| `domain` | string | Domain |
| `updated_at` | string | Update timestamp |

---

### `crm.contact.create`

**Description:** Create a contact in HubSpot CRM

> Creates a new contact record in HubSpot CRM. Contacts represent individual people you interact with.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string | ✓ | Contact email address (must be unique) |
| `first_name` | string |  | Contact first name |
| `last_name` | string |  | Contact last name |
| `phone` | string |  | Contact phone number |
| `company` | string |  | Company name |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `contact_id` | string | HubSpot contact ID (prefixed with hs:) |
| `email` | string | Contact email |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `created_at` | string | Creation timestamp |

---

### `crm.contact.delete`

**Description:** Delete a contact from HubSpot CRM

> Permanently deletes a contact from HubSpot.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` | string | ✓ | HubSpot contact ID (with or without hs: prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `contact_id` | string | Contact ID |
| `status` | string | Should be 'deleted' |

---

### `crm.contact.get`

**Description:** Get contact details from HubSpot CRM

> Retrieves details for a specific contact by ID.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` | string | ✓ | HubSpot contact ID (with or without hs: prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `contact_id` | string | Contact ID |
| `email` | string | Email address |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `company` | string | Company name |

---

### `crm.contact.list`

**Description:** List contacts from HubSpot CRM

> Retrieves a list of contacts from HubSpot CRM.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number of contacts to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `contacts` | array | List of contact objects |
| `count` | integer | Number of contacts |

---

### `crm.contact.search`

**Description:** Search contacts in HubSpot CRM

> Searches for contacts using HubSpot's search API. Supports full-text search across contact properties.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ | Search query string |
| `limit` | integer |  | Maximum number of results |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Search query used |
| `contacts` | array | Matching contacts |
| `count` | integer | Number of results |

---

### `crm.contact.update`

**Description:** Update a contact in HubSpot CRM

> Updates an existing contact's properties in HubSpot.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` | string | ✓ | HubSpot contact ID (with or without hs: prefix) |
| `email` | string |  | Updated email address |
| `first_name` | string |  | Updated first name |
| `last_name` | string |  | Updated last name |
| `phone` | string |  | Updated phone number |
| `company` | string |  | Updated company name |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `contact_id` | string | Contact ID |
| `email` | string | Email |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `updated_at` | string | Update timestamp |

---

### `crm.deal.create`

**Description:** Create a deal in HubSpot CRM

> Creates a new deal record in HubSpot CRM. Deals represent potential revenue opportunities in your sales pipeline.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deal_name` | string | ✓ | Deal name/title |
| `amount` | number |  | Deal value/amount |
| `deal_stage` | string |  | Pipeline stage |
| `pipeline` | string |  | Pipeline ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `deal_id` | string | HubSpot deal ID (prefixed with hs:) |
| `deal_name` | string | Deal name |
| `amount` | number | Deal amount |
| `stage` | string | Current stage |
| `created_at` | string | Creation timestamp |

---

### `crm.deal.delete`

**Description:** Delete a deal from HubSpot CRM

> Permanently deletes a deal from HubSpot.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deal_id` | string | ✓ | HubSpot deal ID |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `deal_id` | string | Deal ID |
| `status` | string | Should be 'deleted' |

---

### `crm.deal.get`

**Description:** Get deal details from HubSpot CRM

> Retrieves details for a specific deal by ID.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deal_id` | string | ✓ | HubSpot deal ID (with or without hs: prefix) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `deal_id` | string | Deal ID |
| `deal_name` | string | Deal name |
| `amount` | number | Deal amount |
| `stage` | string | Pipeline stage |
| `close_date` | string | Expected close date |

---

### `crm.deal.list`

**Description:** List deals from HubSpot CRM

> Retrieves a list of deals from HubSpot CRM.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  | Maximum number of deals to return |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `deals` | array | List of deal objects |
| `count` | integer | Number of deals |

---

### `crm.deal.search`

**Description:** Search deals in HubSpot CRM

> Searches for deals using HubSpot's search API.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ | Search query string |
| `limit` | integer |  | Maximum number of results |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Search query used |
| `deals` | array | Matching deals |
| `count` | integer | Number of results |

---

### `crm.deal.update`

**Description:** Update a deal in HubSpot CRM

> Updates an existing deal's properties in HubSpot.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deal_id` | string | ✓ | HubSpot deal ID |
| `deal_name` | string |  | Updated deal name |
| `amount` | number |  | Updated deal amount |
| `deal_stage` | string |  | Updated pipeline stage |
| `close_date` | string |  | Updated close date (YYYY-MM-DD) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `deal_id` | string | Deal ID |
| `deal_name` | string | Deal name |
| `amount` | number | Amount |
| `stage` | string | Stage |
| `updated_at` | string | Update timestamp |

---

## PLAID (11 capabilities)

### `plaid.accesstoken.exchange`

**Description:** Exchange public token for access token

> Exchanges the public_token returned by Plaid Link for a permanent access_token. This access_token is used for all subsequent API calls to retrieve account data. Must be stored securely - it provides full access to the linked account.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `public_token` | string | ✓ | Public token from Plaid Link onSuccess callback |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | Permanent access token for API calls (store securely) |
| `item_id` | string | Unique identifier for the Item (linked institution) |

---

### `plaid.accounts.get`

**Description:** Get linked accounts

> Retrieves the list of accounts associated with an Item (linked institution). Returns account names, types, subtypes, and masked account numbers. Use this to display available accounts before fetching balances or transactions.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Plaid access token for the linked account |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | List of accounts with id, name, type, subtype, mask |
| `item_id` | string | Unique identifier for the Item |

---

### `plaid.auth.get`

**Description:** Get bank account numbers (with TANs support)

> Retrieves account and routing numbers for ACH and wire transfers. Some institutions use tokenized account numbers (TANs) for security. Requires the 'auth' product to be enabled during Link initialization.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Plaid access token with auth product enabled |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | Accounts with routing, account, wire_routing numbers |
| `numbers` | object | Raw ACH, EFT, and international numbers |
| `item_id` | string | Unique identifier for the Item |

---

### `plaid.balance.get`

**Description:** Get account balances

> Retrieves real-time balance information for accounts. Unlike cached data, this makes a live request to the institution. Returns current balance, available balance, and credit limit where applicable.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Plaid access token for the linked account |
| `account_ids` | array |  | Specific account IDs to fetch (all if omitted) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | Accounts with current_balance, available_balance, limit, cur |

---

### `plaid.identity.get`

**Description:** Get identity information

> Retrieves identity information for account holders including names, addresses, phone numbers, and email addresses. Useful for KYC/AML verification. Requires the 'identity' product to be enabled.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Plaid access token with identity product enabled |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | Accounts with owners array containing identity data |

---

### `plaid.link.create`

**Description:** Create Link token for Plaid initialization

> Creates a Link token to initialize Plaid Link in the client application. Link is the client-side component that users interact with to connect their bank accounts. The token is short-lived and must be used immediately.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `products` | array |  | Plaid products to enable (transactions, auth, identity, bala |
| `client_name` | string |  | Name displayed to user during Link flow |
| `webhook` | string |  | Webhook URL for transaction updates |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `link_token` | string | Token for initializing Plaid Link |
| `expiration` | string | Token expiration timestamp (typically 30 minutes) |

---

### `plaid.processor.token.create`

**Description:** Create processor token for third-party

> Creates a processor token to share account access with a third-party processor (Stripe, Dwolla, etc.) without exposing the access_token. The processor token is single-use and scoped to the specified account and processor.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Plaid access token for the account |
| `account_id` | string | ✓ | Account ID to create token for |
| `processor` | string |  | Processor name (stripe, dwolla, checkbook, etc.) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `processor_token` | string | Token to provide to the processor |

---

### `plaid.transactions.get`

**Description:** Get transactions (legacy method - uses sync)

> Retrieves transactions using the /transactions/sync endpoint (recommended method). Returns added, modified, and removed transactions since the last sync. Use cursor-based pagination for efficient incremental updates.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Plaid access token for the linked account |
| `cursor` | string |  | Cursor from previous sync for incremental updates |
| `count` | integer |  | Number of transactions to fetch per page |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `transactions_added` | array | New transactions since last sync |
| `transactions_modified` | array | Transactions that have been modified |
| `transactions_removed` | array | Transaction IDs that have been removed |
| `next_cursor` | string | Cursor for next page (save for incremental sync) |
| `has_more` | boolean | Whether more transactions are available |

---

### `plaid.transactions.sync`

**Description:** Get transactions using sync (2025 recommended)

> Retrieves transactions using the /transactions/sync endpoint (recommended method). Returns added, modified, and removed transactions since the last sync. Use cursor-based pagination for efficient incremental updates.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Plaid access token for the linked account |
| `cursor` | string |  | Cursor from previous sync for incremental updates |
| `count` | integer |  | Number of transactions to fetch per page |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `transactions_added` | array | New transactions since last sync |
| `transactions_modified` | array | Transactions that have been modified |
| `transactions_removed` | array | Transaction IDs that have been removed |
| `next_cursor` | string | Cursor for next page (save for incremental sync) |
| `has_more` | boolean | Whether more transactions are available |

---

### `plaid.transfer.create`

**Description:** Create ACH transfer via Plaid

> Creates an ACH transfer to move money between accounts using Plaid Transfer. Supports debit (pull money from user) and credit (push money to user) transfers. Same-day ACH available with 'same-day-ach' network option.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `access_token` | string | ✓ | Plaid access token for the source/destination account |
| `account_id` | string | ✓ | Account ID for the transfer |
| `transfer_type` | string |  | Transfer type: 'debit' (pull) or 'credit' (push) |
| `network` | string |  | Transfer network: 'ach' (standard) or 'same-day-ach' |
| `amount` | number | ✓ | Transfer amount in dollars |
| `description` | string |  | Transfer description (appears on bank statement) |
| `ach_class` | string |  | ACH class: 'ppd' (personal), 'ccd' (business), 'web' (intern |
| `user_legal_name` | string | ✓ | Legal name of the account holder |
| `idempotency_key` | string |  | Unique key to prevent duplicate transfers |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `transfer_id` | string | Unique transfer ID for tracking |
| `status` | string | Transfer status (pending, posted, cancelled, failed) |
| `amount` | string | Transfer amount |
| `network` | string | Transfer network used |
| `expected_funds_available_date` | string | Expected date funds will be available |

---

### `plaid.transfer.get`

**Description:** Get transfer status

> Retrieves the current status and details of a transfer. Use this to track transfer progress and handle failures.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `transfer_id` | string | ✓ | Transfer ID from plaid.transfer.create |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `transfer_id` | string | Transfer ID |
| `status` | string | Current status (pending, posted, cancelled, failed, returned |
| `amount` | string | Transfer amount |
| `type` | string | Transfer type (debit or credit) |
| `created` | string | Creation timestamp |
| `network` | string | Transfer network |
| `cancellable` | boolean | Whether transfer can still be cancelled |

---

## CLICKUP (12 capabilities)

### `clickup.comment.create`

**Description:** Create comment on ClickUp task

> Post a comment on a task. Optionally assign with the comment and notify all assignees.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_id` | string | ✓ | Task ID to comment on |
| `comment_text` | string | ✓ | Comment text |
| `assignee` | integer |  | User ID to assign with this comment |
| `notify_all` | boolean |  | Notify all assignees (default: false) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `comment_id` | string | Created comment ID |
| `hist_id` | string | History ID |
| `date` | string | Creation timestamp |

---

### `clickup.comment.list`

**Description:** Get all comments on ClickUp task

> Retrieve all comments on a specific task. Useful for viewing approval history and team discussions.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_id` | string | ✓ | Task ID to get comments for |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of comments |
| `comments` | array | Comments with comment_id, comment_text, user, date |

---

### `clickup.list.get`

**Description:** Get list details from ClickUp

> Get details of a specific list including statuses, folder, space, and task count. Essential for understanding list structure.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `list_id` | string | ✓ | List ID to retrieve |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `list_id` | string | List ID |
| `name` | string | List name |
| `folder` | object | Parent folder with id, name |
| `space` | object | Parent space with id, name |
| `statuses` | array | Available statuses with status, type, color |
| `task_count` | integer | Number of tasks |

---

### `clickup.list.get_in_folder`

**Description:** Get all lists in a ClickUp folder

> Retrieve all lists within a specific folder. Optionally include archived lists.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `folder_id` | string | ✓ | Folder ID to get lists from |
| `archived` | boolean |  | Include archived lists (default: false) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of lists |
| `lists` | array | Lists with list_id, name, task_count |

---

### `clickup.list.get_in_space`

**Description:** Get folderless lists in a ClickUp space

> Retrieve lists that are directly in a space (not in any folder). Optionally include archived lists.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `space_id` | string | ✓ | Space ID to get lists from |
| `archived` | boolean |  | Include archived lists (default: false) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of lists |
| `lists` | array | Lists with list_id, name, task_count |

---

### `clickup.space.get`

**Description:** Get space details from ClickUp

> Get full details of a specific space including statuses and features.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `space_id` | string | ✓ | Space ID to retrieve |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `space_id` | string | Space ID |
| `name` | string | Space name |
| `private` | boolean | Is private space |
| `statuses` | array | Available statuses with status, type, color |
| `features` | object | Enabled features |

---

### `clickup.space.list`

**Description:** List spaces in ClickUp workspace

> Get all spaces in a workspace (team). Optionally include archived spaces.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `team_id` | string | ✓ | Team/Workspace ID |
| `archived` | boolean |  | Include archived spaces (default: false) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of spaces |
| `spaces` | array | Spaces with space_id, name, private, statuses |

---

### `clickup.task.create`

**Description:** Create task in ClickUp for finance workflows (approvals, reviews, month-end)

> Create a new task in a ClickUp list. Supports assignees, priorities, due dates, and status. Ideal for invoice approvals, audit items, and close tasks.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `list_id` | string | ✓ | ID of the list to create task in |
| `name` | string | ✓ | Task name |
| `description` | string |  | Task description (supports markdown) |
| `assignees` | array |  | List of user IDs to assign |
| `priority` | integer |  | Priority level |
| `due_date` | integer |  | Due date timestamp (milliseconds) |
| `start_date` | integer |  | Start date timestamp (milliseconds) |
| `status` | string |  | Status name (must match list's statuses) |
| `tags` | array |  | List of tag names |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Created task ID |
| `name` | string | Task name |
| `url` | string | Direct link to task |
| `status` | string | Task status |
| `assignees` | array | Assigned usernames |
| `due_date` | string | Due date timestamp |
| `priority` | integer | Priority level |

---

### `clickup.task.get`

**Description:** Get task details from ClickUp

> Retrieve full details of a specific task including description, assignees, tags, dates, and custom fields. Optionally include subtasks.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_id` | string | ✓ | Task ID to retrieve |
| `include_subtasks` | boolean |  | Include subtasks in response (default: false) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Task ID |
| `name` | string | Task name |
| `description` | string | Task description |
| `status` | string | Current status |
| `assignees` | array | Assignees with id, username, email |
| `due_date` | string | Due date timestamp |
| `start_date` | string | Start date timestamp |
| `priority` | integer | Priority level |
| `tags` | array | Tag names |
| `url` | string | Direct link to task |
| `date_created` | string | Creation timestamp |
| `date_updated` | string | Last update timestamp |

---

### `clickup.task.list`

**Description:** List tasks in ClickUp with filtering

> List tasks in a list with optional filtering by status, assignees, tags, and due dates. Supports pagination (max 100 per page).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `list_id` | string | ✓ | List ID to get tasks from |
| `archived` | boolean |  | Include archived tasks (default: false) |
| `page` | integer |  | Page number (0-indexed) |
| `order_by` | string |  | Sort field |
| `reverse` | boolean |  | Reverse sort order (default: false) |
| `subtasks` | boolean |  | Include subtasks (default: false) |
| `statuses` | array |  | Filter by status names |
| `assignees` | array |  | Filter by assignee IDs |
| `tags` | array |  | Filter by tag names |
| `due_date_gt` | integer |  | Due date greater than (timestamp) |
| `due_date_lt` | integer |  | Due date less than (timestamp) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of tasks returned |
| `tasks` | array | Tasks with task_id, name, status, assignees, due_date, prior |

---

### `clickup.task.update`

**Description:** Update task in ClickUp (status, assignees, priority)

> Update an existing task's properties. Only provided fields are updated. Use for changing status, reassigning, or updating due dates.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_id` | string | ✓ | Task ID to update |
| `name` | string |  | New task name |
| `description` | string |  | New description |
| `status` | string |  | New status name |
| `priority` | integer |  | New priority (1=urgent, 4=low) |
| `assignees` | array |  | New assignee IDs (replaces existing) |
| `due_date` | integer |  | New due date timestamp (milliseconds) |
| `start_date` | integer |  | New start date timestamp (milliseconds) |

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Updated task ID |
| `name` | string | Task name |
| `status` | string | New status |
| `url` | string | Direct link to task |

---

### `clickup.team.list`

**Description:** Get all ClickUp workspaces user has access to

> List all workspaces (teams) the authenticated user has access to. This is the starting point for navigating the ClickUp hierarchy.

**Returns:**
| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Number of teams |
| `teams` | array | Teams with team_id, name, color, avatar |

---
