# QuickBooks Online API Parity Analysis

**Goal:** Complete coverage of all QBO entities and operations.

**Source:** [Intuit Developer Portal](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account)

---

## CURRENT IMPLEMENTATION: 40 Methods

### What We Have

| Entity | Operations | Status |
|--------|------------|--------|
| Vendor | create, get, list | ✅ |
| Bill | create | ✅ |
| BillPayment | create | ✅ |
| JournalEntry | create | ✅ |
| Customer | create, get, update, list | ✅ |
| Invoice | create, get, send, void, list, list_outstanding | ✅ |
| Item | create, get, list | ✅ |
| Payment | create, apply_to_invoice, get | ✅ |
| Estimate | create, get | ✅ |
| SalesReceipt | create | ✅ |
| CreditMemo | create | ✅ |
| TimeActivity | create | ✅ |
| Purchase (Expense) | create | ✅ |
| PurchaseOrder | create | ✅ |
| Attachable | upload | ✅ |
| Account | get_chart_of_accounts | ✅ |
| Query | query_entities | ✅ |
| Reports | profit_loss, balance_sheet, profit_loss_detail, budget | ✅ |

---

## QBO COMPLETE ENTITY LIST

### Core Accounting Entities (30 Total)

| Entity | Description |
|--------|-------------|
| Account | Chart of accounts |
| Attachable | File attachments |
| Bill | Vendor bills/invoices |
| BillPayment | Payments to vendors |
| Budget | Budget planning |
| Class | Transaction classification |
| CompanyInfo | Company details |
| CreditMemo | Customer credits |
| Customer | Customer records |
| CustomerType | Customer categories |
| Department | Departmental tracking |
| Deposit | Bank deposits |
| Employee | Employee records |
| Estimate | Sales estimates/quotes |
| ExchangeRate | Currency exchange |
| Invoice | Customer invoices |
| Item | Products and services |
| JournalEntry | GL journal entries |
| Payment | Customer payments |
| PaymentMethod | Payment types |
| Preferences | Company preferences |
| Purchase | Expenses/checks |
| PurchaseOrder | Purchase orders |
| RefundReceipt | Customer refunds |
| SalesReceipt | Point-of-sale receipts |
| TaxAgency | Tax authorities |
| TaxCode | Tax codes |
| TaxRate | Tax rates |
| Term | Payment terms |
| TimeActivity | Time tracking |
| Transfer | Bank transfers |
| Vendor | Vendor records |
| VendorCredit | Vendor credits |

---

## MISSING: Account Operations

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_account` | Create GL account | HIGH |
| `get_account` | Get account details | HIGH |
| `update_account` | Modify account | MEDIUM |
| `list_accounts` | List all accounts (vs COA query) | HIGH |
| `delete_account` | Deactivate account | LOW |

---

## MISSING: Bill Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_bill` | Get bill details | HIGH |
| `update_bill` | Modify bill | HIGH |
| `delete_bill` | Void/delete bill | MEDIUM |
| `list_bills` | List bills | HIGH |
| `get_bills_by_vendor` | Bills for vendor | HIGH |

---

## MISSING: BillPayment Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_bill_payment` | Get payment details | MEDIUM |
| `update_bill_payment` | Modify payment | LOW |
| `delete_bill_payment` | Void payment | MEDIUM |
| `list_bill_payments` | List AP payments | HIGH |

---

## MISSING: Class Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_class` | Create class | HIGH |
| `get_class` | Get class details | MEDIUM |
| `update_class` | Modify class | MEDIUM |
| `list_classes` | List all classes | HIGH |
| `delete_class` | Deactivate class | LOW |

---

## MISSING: CompanyInfo Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_company_info` | Get company details | HIGH |
| `update_company_info` | Update company | LOW |

---

## MISSING: CreditMemo Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_credit_memo` | Get credit memo | HIGH |
| `update_credit_memo` | Modify credit | MEDIUM |
| `delete_credit_memo` | Void credit | MEDIUM |
| `list_credit_memos` | List credits | HIGH |
| `send_credit_memo` | Email credit memo | MEDIUM |

---

## MISSING: Department Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_department` | Create department | HIGH |
| `get_department` | Get department | MEDIUM |
| `update_department` | Modify department | MEDIUM |
| `list_departments` | List departments | HIGH |

---

## MISSING: Deposit Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_deposit` | Create bank deposit | HIGH |
| `get_deposit` | Get deposit details | HIGH |
| `update_deposit` | Modify deposit | MEDIUM |
| `delete_deposit` | Void deposit | MEDIUM |
| `list_deposits` | List deposits | HIGH |

---

## MISSING: Employee Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_employee` | Create employee | HIGH |
| `get_employee` | Get employee | HIGH |
| `update_employee` | Modify employee | MEDIUM |
| `list_employees` | List employees | HIGH |

---

## MISSING: Estimate Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `update_estimate` | Modify estimate | HIGH |
| `delete_estimate` | Void estimate | MEDIUM |
| `list_estimates` | List estimates | HIGH |
| `send_estimate` | Email estimate | HIGH |
| `convert_to_invoice` | Estimate → Invoice | HIGH |

---

## MISSING: ExchangeRate Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_exchange_rate` | Get currency rate | MEDIUM |
| `update_exchange_rate` | Set rate | LOW |

---

## MISSING: Invoice Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `update_invoice` | Modify invoice | HIGH |
| `delete_invoice` | Delete draft | MEDIUM |
| `get_invoice_pdf` | Download PDF | HIGH |

---

## MISSING: Item Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `update_item` | Modify item | HIGH |
| `delete_item` | Deactivate item | LOW |

---

## MISSING: JournalEntry Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_journal_entry` | Get JE details | HIGH |
| `update_journal_entry` | Modify JE | MEDIUM |
| `delete_journal_entry` | Void JE | MEDIUM |
| `list_journal_entries` | List all JEs | HIGH |
| `reverse_journal_entry` | Create reversing JE | HIGH |

---

## MISSING: Payment Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `update_payment` | Modify payment | MEDIUM |
| `delete_payment` | Void payment | MEDIUM |
| `list_payments` | List payments | HIGH |

---

## MISSING: PaymentMethod Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_payment_method` | Create payment type | MEDIUM |
| `get_payment_method` | Get payment type | LOW |
| `update_payment_method` | Modify payment type | LOW |
| `list_payment_methods` | List payment types | HIGH |

---

## MISSING: Preferences Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_preferences` | Get company prefs | HIGH |
| `update_preferences` | Update prefs | LOW |

---

## MISSING: Purchase Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_purchase` | Get expense details | HIGH |
| `update_purchase` | Modify expense | MEDIUM |
| `delete_purchase` | Void expense | MEDIUM |
| `list_purchases` | List expenses | HIGH |

---

## MISSING: PurchaseOrder Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_purchase_order` | Get PO details | HIGH |
| `update_purchase_order` | Modify PO | HIGH |
| `delete_purchase_order` | Cancel PO | MEDIUM |
| `list_purchase_orders` | List POs | HIGH |
| `receive_purchase_order` | Convert to bill | HIGH |

---

## MISSING: RefundReceipt Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_refund_receipt` | Create refund | HIGH |
| `get_refund_receipt` | Get refund | MEDIUM |
| `update_refund_receipt` | Modify refund | LOW |
| `delete_refund_receipt` | Void refund | MEDIUM |
| `list_refund_receipts` | List refunds | HIGH |

---

## MISSING: SalesReceipt Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_sales_receipt` | Get receipt | HIGH |
| `update_sales_receipt` | Modify receipt | MEDIUM |
| `delete_sales_receipt` | Void receipt | MEDIUM |
| `list_sales_receipts` | List receipts | HIGH |
| `send_sales_receipt` | Email receipt | MEDIUM |

---

## MISSING: TaxAgency Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_tax_agency` | Create tax authority | MEDIUM |
| `get_tax_agency` | Get agency | LOW |
| `list_tax_agencies` | List agencies | MEDIUM |

---

## MISSING: TaxCode Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_tax_code` | Create tax code | MEDIUM |
| `get_tax_code` | Get tax code | LOW |
| `list_tax_codes` | List codes | HIGH |

---

## MISSING: TaxRate Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_tax_rate` | Create rate | MEDIUM |
| `get_tax_rate` | Get rate | LOW |
| `list_tax_rates` | List rates | HIGH |

---

## MISSING: Term Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_term` | Create payment term | MEDIUM |
| `get_term` | Get term | LOW |
| `list_terms` | List terms (NET 30, etc.) | HIGH |

---

## MISSING: TimeActivity Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_time_activity` | Get time entry | MEDIUM |
| `update_time_activity` | Modify time | MEDIUM |
| `delete_time_activity` | Delete time | LOW |
| `list_time_activities` | List time entries | HIGH |

---

## MISSING: Transfer Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_transfer` | Bank-to-bank transfer | HIGH |
| `get_transfer` | Get transfer | MEDIUM |
| `update_transfer` | Modify transfer | LOW |
| `delete_transfer` | Void transfer | MEDIUM |
| `list_transfers` | List transfers | HIGH |

---

## MISSING: Vendor Operations (Expand)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `update_vendor` | Modify vendor | HIGH |
| `delete_vendor` | Deactivate vendor | LOW |

---

## MISSING: VendorCredit Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_vendor_credit` | Create vendor credit | HIGH |
| `get_vendor_credit` | Get credit | HIGH |
| `update_vendor_credit` | Modify credit | MEDIUM |
| `delete_vendor_credit` | Void credit | MEDIUM |
| `list_vendor_credits` | List credits | HIGH |

---

## MISSING: Reports (Expand)

| Report | Finance Use Case | Priority |
|--------|------------------|----------|
| `get_cash_flow` | Cash flow statement | HIGH |
| `get_general_ledger` | GL detail | HIGH |
| `get_trial_balance` | Trial balance | HIGH |
| `get_aged_payables` | AP aging | HIGH |
| `get_aged_receivables` | AR aging | HIGH |
| `get_customer_balance` | Customer balances | HIGH |
| `get_vendor_balance` | Vendor balances | HIGH |
| `get_transaction_list` | Transaction detail | HIGH |
| `get_profit_loss_by_class` | P&L by class | MEDIUM |
| `get_profit_loss_by_customer` | P&L by customer | MEDIUM |
| `get_expenses_by_vendor` | Vendor expense | MEDIUM |
| `get_ap_aging_summary` | AP summary | HIGH |
| `get_ar_aging_summary` | AR summary | HIGH |
| `get_inventory_valuation` | Inventory report | MEDIUM |
| `get_sales_by_customer` | Sales analysis | MEDIUM |
| `get_sales_by_product` | Product analysis | MEDIUM |

---

## MISSING: Batch Operations (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `batch_create` | Create multiple entities | HIGH |
| `batch_update` | Update multiple entities | HIGH |
| `batch_delete` | Delete multiple entities | MEDIUM |
| `batch_query` | Query multiple entities | HIGH |

---

## MISSING: Webhooks (NEW)

| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_webhook` | Subscribe to events | HIGH |
| `get_webhook` | Get webhook details | LOW |
| `update_webhook` | Modify webhook | LOW |
| `delete_webhook` | Unsubscribe | MEDIUM |
| `list_webhooks` | List subscriptions | MEDIUM |

---

## IMPLEMENTATION BATCHES

### Batch 1: Account CRUD
1. create_account
2. get_account
3. update_account
4. list_accounts
5. delete_account

### Batch 2: Bill Completion
1. get_bill
2. update_bill
3. delete_bill
4. list_bills
5. get_bills_by_vendor

### Batch 3: JournalEntry Completion
1. get_journal_entry
2. update_journal_entry
3. delete_journal_entry
4. list_journal_entries
5. reverse_journal_entry

### Batch 4: VendorCredit (NEW)
1. create_vendor_credit
2. get_vendor_credit
3. update_vendor_credit
4. delete_vendor_credit
5. list_vendor_credits

### Batch 5: Deposit (NEW)
1. create_deposit
2. get_deposit
3. update_deposit
4. delete_deposit
5. list_deposits

### Batch 6: Transfer (NEW)
1. create_transfer
2. get_transfer
3. update_transfer
4. delete_transfer
5. list_transfers

### Batch 7: Employee (NEW)
1. create_employee
2. get_employee
3. update_employee
4. list_employees
5. (combined with next)

### Batch 8: Class & Department
1. create_class
2. list_classes
3. create_department
4. list_departments
5. get_company_info

### Batch 9: PurchaseOrder Completion
1. get_purchase_order
2. update_purchase_order
3. delete_purchase_order
4. list_purchase_orders
5. receive_purchase_order

### Batch 10: Purchase (Expense) Completion
1. get_purchase
2. update_purchase
3. delete_purchase
4. list_purchases
5. (combined with next)

### Batch 11: RefundReceipt (NEW)
1. create_refund_receipt
2. get_refund_receipt
3. update_refund_receipt
4. delete_refund_receipt
5. list_refund_receipts

### Batch 12: Estimate Completion
1. update_estimate
2. delete_estimate
3. list_estimates
4. send_estimate
5. convert_to_invoice

### Batch 13: SalesReceipt Completion
1. get_sales_receipt
2. update_sales_receipt
3. delete_sales_receipt
4. list_sales_receipts
5. send_sales_receipt

### Batch 14: CreditMemo Completion
1. get_credit_memo
2. update_credit_memo
3. delete_credit_memo
4. list_credit_memos
5. send_credit_memo

### Batch 15: Payment Completion
1. update_payment
2. delete_payment
3. list_payments
4. list_bill_payments
5. delete_bill_payment

### Batch 16: Invoice Completion
1. update_invoice
2. delete_invoice
3. get_invoice_pdf
4. update_vendor
5. delete_vendor

### Batch 17: Item Completion
1. update_item
2. delete_item
3. list_payment_methods
4. list_terms
5. list_tax_codes

### Batch 18: Tax Entities
1. create_tax_agency
2. list_tax_agencies
3. create_tax_rate
4. list_tax_rates
5. create_tax_code

### Batch 19: Core Reports
1. get_cash_flow
2. get_general_ledger
3. get_trial_balance
4. get_aged_payables
5. get_aged_receivables

### Batch 20: Analysis Reports
1. get_customer_balance
2. get_vendor_balance
3. get_transaction_list
4. get_ap_aging_summary
5. get_ar_aging_summary

### Batch 21: More Reports
1. get_profit_loss_by_class
2. get_profit_loss_by_customer
3. get_expenses_by_vendor
4. get_sales_by_customer
5. get_sales_by_product

### Batch 22: Time & Preferences
1. get_time_activity
2. update_time_activity
3. delete_time_activity
4. list_time_activities
5. get_preferences

### Batch 23: Batch Operations
1. batch_create
2. batch_update
3. batch_delete
4. batch_query
5. (combined with webhooks)

### Batch 24: Webhooks
1. create_webhook
2. get_webhook
3. update_webhook
4. delete_webhook
5. list_webhooks

---

## SUMMARY

| Category | Current | Missing | Total After |
|----------|---------|---------|-------------|
| Account | 1 | 4 | 5 |
| Bill | 1 | 5 | 6 |
| BillPayment | 1 | 4 | 5 |
| Class | 0 | 5 | 5 |
| CompanyInfo | 0 | 2 | 2 |
| CreditMemo | 1 | 4 | 5 |
| Customer | 4 | 0 | 4 |
| Department | 0 | 4 | 4 |
| Deposit | 0 | 5 | 5 |
| Employee | 0 | 4 | 4 |
| Estimate | 2 | 4 | 6 |
| Invoice | 6 | 3 | 9 |
| Item | 3 | 2 | 5 |
| JournalEntry | 1 | 4 | 5 |
| Payment | 3 | 3 | 6 |
| Purchase | 1 | 4 | 5 |
| PurchaseOrder | 1 | 5 | 6 |
| RefundReceipt | 0 | 5 | 5 |
| SalesReceipt | 1 | 5 | 6 |
| Tax (Agency/Code/Rate) | 0 | 6 | 6 |
| Term | 0 | 3 | 3 |
| TimeActivity | 1 | 4 | 5 |
| Transfer | 0 | 5 | 5 |
| Vendor | 3 | 2 | 5 |
| VendorCredit | 0 | 5 | 5 |
| Reports | 4 | 16 | 20 |
| Batch | 0 | 4 | 4 |
| Webhooks | 0 | 5 | 5 |
| **TOTAL** | **40** | **~120** | **~160** |

---

## FINANCE WORKFLOW COVERAGE

After full implementation:

| Workflow | Status |
|----------|--------|
| Full AP cycle (bills, payments, credits) | ✅ Complete |
| Full AR cycle (invoices, payments, credits) | ✅ Complete |
| Journal entries & GL | ✅ Complete |
| Bank deposits & transfers | ✅ Complete |
| Purchase orders & receiving | ✅ Complete |
| Estimates & quotes | ✅ Complete |
| Point-of-sale | ✅ Complete |
| Time tracking & billing | ✅ Complete |
| Multi-class tracking | ✅ Complete |
| Department tracking | ✅ Complete |
| Tax management | ✅ Complete |
| All financial reports | ✅ Complete |
| Batch operations | ✅ Complete |
| Real-time webhooks | ✅ Complete |

**This would be the most comprehensive QuickBooks integration ever built.**
