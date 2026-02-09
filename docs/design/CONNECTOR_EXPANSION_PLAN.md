# Connector Expansion Plan: Finance-First Approach

## Philosophy
Every endpoint must support a real finance workflow. No "API completeness for completeness sake."

---

## PART 1: ACCOUNTS PAYABLE (AP) WORKFLOWS

### Scenario: Invoice Receipt → Payment

**Current State:**
- Bill.com: 9 endpoints (create vendor, create bill, approve, pay)
- NetSuite: 15 endpoints (vendor bills, POs, payments)

**Missing for Complete AP:**

#### Bill.com - Batch 1 (Invoice Management)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `GET /v3/bills/{id}/attachments` | View invoice PDF/images |
| 2 | `POST /v3/bills/{id}/attachments` | Attach invoice documents |
| 3 | `GET /v3/bills/duplicates` | Duplicate invoice detection |
| 4 | `POST /v3/bills/bulk-approve` | Batch approval for month-end |
| 5 | `GET /v3/approval-policies` | Get approval routing rules |

#### Bill.com - Batch 2 (Payment Operations)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `GET /v3/payments/{id}/check-image` | Audit trail for check payments |
| 7 | `POST /v3/payments/void` | Void issued payment |
| 8 | `POST /v3/payments/stop` | Stop payment on check |
| 9 | `GET /v3/payments/pending-approval` | Payment approval queue |
| 10 | `POST /v3/payments/bulk-approve` | Batch payment approval |

#### Bill.com - Batch 3 (Vendor Management)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 11 | `GET /v3/vendors/{id}/1099` | 1099 reporting data |
| 12 | `PUT /v3/vendors/{id}/payment-terms` | Update NET 30/60/90 |
| 13 | `GET /v3/vendors/{id}/payment-history` | Vendor payment analysis |
| 14 | `POST /v3/vendors/{id}/bank-account` | Add vendor ACH info |
| 15 | `GET /v3/vendors/w9-status` | W9 compliance tracking |

#### Bill.com - Batch 4 (PO Matching)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 16 | `POST /v3/purchase-orders` | Create PO |
| 17 | `GET /v3/purchase-orders` | List POs |
| 18 | `POST /v3/bills/{id}/match-po` | 3-way match |
| 19 | `GET /v3/purchase-orders/{id}/receipts` | Goods receipt |
| 20 | `GET /v3/bills/unmatched` | Bills without PO match |

#### NetSuite - Batch 1 (Invoice/Bill Expansion)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `GET /vendor-bills` | List all vendor bills |
| 2 | `GET /vendor-bills/{id}` | Get bill details |
| 3 | `PUT /vendor-bills/{id}` | Update bill (corrections) |
| 4 | `POST /vendor-bills/{id}/void` | Void bill |
| 5 | `GET /vendor-bills/pending-approval` | Approval queue |

#### NetSuite - Batch 2 (Vendor Credits)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `POST /vendor-credits` | Create vendor credit |
| 7 | `GET /vendor-credits` | List credits |
| 8 | `POST /vendor-credits/{id}/apply` | Apply credit to bill |
| 9 | `GET /vendor-bills/{id}/credits` | Credits applied to bill |
| 10 | `POST /vendor-returns` | Create vendor return |

---

## PART 2: ACCOUNTS RECEIVABLE (AR) WORKFLOWS

### Scenario: Lockbox Processing (Maria Santos)

**Current State:**
- Recurly: 12 endpoints (subscriptions, invoices, apply_payment)

**Missing for Complete Lockbox:**

#### Recurly - Batch 1 (Payment Application)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `POST /invoices/{id}/refund` | Process refund |
| 2 | `GET /invoices/{id}/transactions` | All transactions on invoice |
| 3 | `POST /invoices/{id}/write-off` | Write off bad debt |
| 4 | `GET /accounts/{code}/balance` | Customer balance inquiry |
| 5 | `POST /accounts/{code}/credit` | Apply account credit |

#### Recurly - Batch 2 (Dunning & Collections)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `GET /invoices/past-due` | Aging report data |
| 7 | `POST /invoices/{id}/dunning-pause` | Pause dunning |
| 8 | `GET /accounts/{code}/dunning-campaigns` | Dunning status |
| 9 | `POST /invoices/{id}/collection-note` | Add collection note |
| 10 | `GET /invoices/collection-status` | Collection queue |

#### Recurly - Batch 3 (Billing Info)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 11 | `GET /accounts/{code}/billing-info` | Payment method on file |
| 12 | `PUT /accounts/{code}/billing-info` | Update payment method |
| 13 | `POST /accounts/{code}/billing-info/verify` | Verify card/bank |
| 14 | `GET /accounts/{code}/shipping-addresses` | Shipping for invoices |
| 15 | `DELETE /accounts/{code}/billing-info` | Remove payment method |

#### Recurly - Batch 4 (Coupons & Discounts)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 16 | `POST /coupons` | Create discount code |
| 17 | `GET /coupons` | List active coupons |
| 18 | `GET /coupons/{id}/redemptions` | Coupon usage report |
| 19 | `POST /coupons/{id}/restore` | Reactivate coupon |
| 20 | `DELETE /coupons/{id}` | Deactivate coupon |

#### Recurly - Batch 5 (Add-ons & Usage)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 21 | `POST /add-ons` | Create billable add-on |
| 22 | `GET /subscriptions/{id}/add-ons` | Add-ons on subscription |
| 23 | `POST /subscriptions/{id}/usage` | Record metered usage |
| 24 | `GET /subscriptions/{id}/usage` | Usage history |
| 25 | `POST /subscriptions/{id}/pending-changes` | Preview billing changes |

---

## PART 3: GENERAL LEDGER & CLOSE

### Scenario: Month-End Close

**Current State:**
- NetSuite: Journal entries, vendor bills
- QuickBooks: 45 endpoints

**Missing for Complete GL:**

#### NetSuite - Batch 3 (Journal Entries Expansion)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `GET /journal-entries` | List all JEs |
| 2 | `PUT /journal-entries/{id}` | Correct JE |
| 3 | `POST /journal-entries/{id}/reverse` | Reversing entry |
| 4 | `POST /journal-entries/{id}/void` | Void entry |
| 5 | `GET /journal-entries/pending-approval` | JE approval queue |

#### NetSuite - Batch 4 (Chart of Accounts)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `GET /accounts` | Chart of accounts |
| 7 | `GET /accounts/{id}` | Account details |
| 8 | `GET /accounts/{id}/balance` | Account balance |
| 9 | `GET /accounts/{id}/transactions` | Account ledger |
| 10 | `POST /accounts` | Create new account |

#### NetSuite - Batch 5 (Financial Reports)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 11 | `GET /reports/trial-balance` | Trial balance |
| 12 | `GET /reports/balance-sheet` | Balance sheet |
| 13 | `GET /reports/income-statement` | P&L |
| 14 | `GET /reports/cash-flow` | Cash flow statement |
| 15 | `GET /reports/aged-payables` | AP aging |

#### NetSuite - Batch 6 (Reconciliation)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 16 | `GET /bank-reconciliations` | List reconciliations |
| 17 | `POST /bank-reconciliations` | Create reconciliation |
| 18 | `GET /bank-reconciliations/{id}/transactions` | Transactions to match |
| 19 | `POST /bank-reconciliations/{id}/match` | Match transaction |
| 20 | `POST /bank-reconciliations/{id}/complete` | Complete reconciliation |

#### QuickBooks - Batch 1 (Reports)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `GET /reports/BalanceSheet` | Balance sheet |
| 2 | `GET /reports/ProfitAndLoss` | P&L |
| 3 | `GET /reports/CashFlow` | Cash flow |
| 4 | `GET /reports/TrialBalance` | Trial balance |
| 5 | `GET /reports/AgedPayables` | AP aging |

#### QuickBooks - Batch 2 (More Reports)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `GET /reports/AgedReceivables` | AR aging |
| 7 | `GET /reports/GeneralLedger` | GL detail |
| 8 | `GET /reports/VendorBalance` | Vendor balances |
| 9 | `GET /reports/CustomerBalance` | Customer balances |
| 10 | `GET /reports/TransactionList` | Transaction detail |

---

## PART 4: TREASURY & BANKING

### Scenario: Cash Position & Multi-Entity

**Current State:**
- Plaid: 11 endpoints (accounts, balances, transactions)
- Mercury: 6 endpoints (basic banking)

**Missing for Complete Treasury:**

#### Plaid - Batch 1 (Account Details)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `POST /accounts/balance/get` | Real-time balance |
| 2 | `POST /institutions/get_by_id` | Bank name/details |
| 3 | `POST /accounts/get` | All linked accounts |
| 4 | `POST /identity/get` | Account holder info |
| 5 | `POST /auth/get` | ACH routing/account numbers |

#### Plaid - Batch 2 (Transaction Enrichment)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `POST /transactions/sync` | Incremental transaction sync |
| 7 | `POST /transactions/enrich` | Categorize transactions |
| 8 | `POST /transactions/recurring/get` | Recurring payment detection |
| 9 | `POST /categories/get` | Transaction categories |
| 10 | `POST /investments/holdings/get` | Investment positions |

#### Plaid - Batch 3 (Payments)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 11 | `POST /payment_initiation/payment/create` | Initiate payment |
| 12 | `POST /payment_initiation/payment/get` | Payment status |
| 13 | `POST /transfer/authorization/create` | Pre-authorize transfer |
| 14 | `POST /transfer/create` | Execute transfer |
| 15 | `POST /transfer/get` | Transfer status |

#### Mercury - Batch 1 (Enhanced Banking)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `GET /accounts/{id}/statements` | Bank statements |
| 2 | `GET /accounts/{id}/balance-history` | Historical balances |
| 3 | `POST /payments/scheduled` | Schedule future payment |
| 4 | `GET /payments/pending` | Pending payments |
| 5 | `POST /payments/bulk` | Bulk payment file |

#### Mercury - Batch 2 (Cards & Expense)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `GET /cards` | List corporate cards |
| 7 | `GET /cards/{id}/transactions` | Card transactions |
| 8 | `POST /cards/{id}/limit` | Set spending limit |
| 9 | `POST /cards/{id}/freeze` | Freeze card |
| 10 | `GET /categories` | Transaction categories |

---

## PART 5: COMMUNICATION & NOTIFICATIONS

### Scenario: Approval Notifications, Status Updates

**Current State:**
- Slack: 6 endpoints (send message, DM, file, channel)
- Gmail: 9 endpoints (send, read, drafts)

**Missing for Finance Workflows:**

#### Slack - Batch 1 (Rich Messaging)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `chat.update` | Update approval status in message |
| 2 | `chat.delete` | Remove outdated notification |
| 3 | `reactions.add` | Add approval reaction |
| 4 | `reactions.get` | Check if approved via reaction |
| 5 | `chat.postEphemeral` | Private notification |

#### Slack - Batch 2 (Interactive)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `views.open` | Open approval modal |
| 7 | `views.update` | Update modal content |
| 8 | `views.push` | Multi-step approval flow |
| 9 | `dialog.open` | Quick input dialog |
| 10 | `chat.unfurl` | Rich invoice preview |

#### Slack - Batch 3 (User & Channel)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 11 | `users.info` | Get approver details |
| 12 | `users.lookupByEmail` | Find user by email |
| 13 | `conversations.members` | Finance team members |
| 14 | `conversations.info` | Channel details |
| 15 | `usergroups.users.list` | @finance-team members |

#### Slack - Batch 4 (Search & Pins)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 16 | `search.messages` | Find past approvals |
| 17 | `pins.add` | Pin important updates |
| 18 | `pins.list` | Get pinned items |
| 19 | `bookmarks.add` | Bookmark invoice link |
| 20 | `reminders.add` | Payment reminder |

#### Gmail - Batch 1 (Organization)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `labels.create` | Create "Invoices" label |
| 2 | `labels.list` | List all labels |
| 3 | `messages.modify` | Add/remove labels |
| 4 | `messages.trash` | Archive processed |
| 5 | `messages.batchModify` | Bulk organize |

#### Gmail - Batch 2 (Threads)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `threads.get` | Full email thread |
| 7 | `threads.list` | List threads |
| 8 | `threads.modify` | Label entire thread |
| 9 | `threads.trash` | Archive thread |
| 10 | `drafts.list` | List pending drafts |

---

## PART 6: TASK MANAGEMENT (Approvals & Workflows)

### Scenario: Invoice Approval Tracking

**Current State:**
- Linear: 10 endpoints
- Monday: 13 endpoints
- ClickUp: 12 endpoints

**Missing for Finance Workflows:**

#### Linear - Batch 1 (Workflow States)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `workflowStates.list` | Get approval statuses |
| 2 | `workflowStates.create` | Create "Pending AP" status |
| 3 | `issue.transition` | Move through workflow |
| 4 | `cycles.list` | Month-end cycles |
| 5 | `cycles.create` | Create close cycle |

#### Linear - Batch 2 (Automation)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `webhooks.create` | Webhook for approvals |
| 7 | `webhooks.list` | List webhooks |
| 8 | `attachments.create` | Attach invoice to issue |
| 9 | `attachments.list` | Get attachments |
| 10 | `issueRelations.create` | Link related issues |

#### Monday - Batch 1 (Automations)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `create_webhook` | Approval notifications |
| 2 | `delete_webhook` | Remove webhook |
| 3 | `move_item_to_group` | Move to "Approved" group |
| 4 | `duplicate_item` | Copy template |
| 5 | `archive_item` | Archive completed |

#### Monday - Batch 2 (Subitems)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `create_subitem` | Line items on invoice |
| 7 | `get_subitems` | Get line items |
| 8 | `move_item_to_board` | Transfer between boards |
| 9 | `create_doc` | Create approval doc |
| 10 | `add_file_to_column` | Attach invoice |

#### ClickUp - Batch 1 (Custom Fields)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `GET /task/{id}/field` | Get custom fields |
| 2 | `POST /task/{id}/field/{field_id}` | Set amount, vendor |
| 3 | `GET /list/{id}/field` | List custom fields |
| 4 | `POST /list/{id}/field` | Create custom field |
| 5 | `GET /task/{id}/dependency` | Task dependencies |

#### ClickUp - Batch 2 (Time & Goals)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `POST /task/{id}/time` | Log review time |
| 7 | `GET /task/{id}/time` | Time spent on approval |
| 8 | `GET /goal` | Close checklist goals |
| 9 | `POST /goal` | Create close goal |
| 10 | `PUT /goal/{id}/key_result` | Update progress |

---

## PART 7: DOCUMENT & OCR

### Scenario: Invoice OCR & Document Storage

**Current State:**
- OCR utility: 6 endpoints (basic extraction)

**Missing:**

#### OCR - Batch 1 (Enhanced Extraction)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `ocr.extract_table` | Line item extraction |
| 2 | `ocr.extract_invoice` | Structured invoice data |
| 3 | `ocr.extract_receipt` | Receipt data |
| 4 | `ocr.extract_bank_statement` | Statement parsing |
| 5 | `ocr.extract_w9` | W9 form parsing |

#### OCR - Batch 2 (Document Intelligence)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `ocr.classify_document` | Invoice vs receipt vs statement |
| 7 | `ocr.extract_check` | Check image data |
| 8 | `ocr.compare_documents` | Duplicate detection |
| 9 | `ocr.extract_po` | PO extraction |
| 10 | `ocr.validate_data` | Data quality check |

---

## PART 8: SUBSCRIPTION & BILLING (SaaS Specific)

### Scenario: Marina Billing (Dockwa)

**Current State:**
- Stripe: 61 endpoints
- Recurly: 12 endpoints

**Missing for Complete Subscription:**

#### Stripe - Batch 1 (Subscription Management)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 1 | `GET /v1/subscriptions/{id}/upcoming_invoice` | Preview next bill |
| 2 | `POST /v1/subscriptions/{id}/discount` | Apply discount |
| 3 | `DELETE /v1/subscriptions/{id}/discount` | Remove discount |
| 4 | `POST /v1/subscription_schedules` | Schedule changes |
| 5 | `GET /v1/subscription_schedules/{id}` | Get schedule |

#### Stripe - Batch 2 (Invoicing)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 6 | `POST /v1/invoices/{id}/send` | Send invoice email |
| 7 | `POST /v1/invoices/{id}/void` | Void invoice |
| 8 | `POST /v1/invoices/{id}/mark_uncollectible` | Bad debt |
| 9 | `GET /v1/invoices/upcoming` | Upcoming invoices |
| 10 | `POST /v1/invoiceitems` | Add line item |

#### Stripe - Batch 3 (Disputes & Refunds)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 11 | `GET /v1/disputes` | List disputes |
| 12 | `POST /v1/disputes/{id}/close` | Accept dispute |
| 13 | `POST /v1/disputes/{id}` | Submit evidence |
| 14 | `POST /v1/refunds` | Process refund |
| 15 | `GET /v1/refunds/{id}` | Refund status |

#### Stripe - Batch 4 (Reporting)
| # | Endpoint | Finance Use Case |
|---|----------|------------------|
| 16 | `GET /v1/balance/history` | Balance transactions |
| 17 | `GET /v1/reporting/report_runs` | Financial reports |
| 18 | `POST /v1/reporting/report_runs` | Generate report |
| 19 | `GET /v1/sigma/scheduled_query_runs` | SQL queries |
| 20 | `GET /v1/tax/calculations` | Tax calculations |

---

## IMPLEMENTATION PRIORITY

### Phase 1: Maria Santos Scenario (Lockbox) - 2 weeks
1. Recurly Batch 1-2 (Payment application, dunning)
2. Bill.com Batch 1-2 (Attachments, payments)
3. Slack Batch 1 (Rich messaging for notifications)
4. OCR Batch 1 (Invoice extraction)

### Phase 2: Elena Martinez Scenario (Multi-Entity) - 2 weeks
1. NetSuite Batch 3-4 (JE, Chart of Accounts)
2. QuickBooks Batch 1-2 (Reports)
3. NetSuite Batch 5-6 (Reports, Reconciliation)

### Phase 3: Treasury & Banking - 2 weeks
1. Plaid Batch 1-3 (Full banking)
2. Mercury Batch 1-2 (Enhanced banking)

### Phase 4: Communication & Workflow - 2 weeks
1. Slack Batch 2-4 (Interactive, search)
2. Gmail Batch 1-2 (Organization, threads)
3. Linear/Monday/ClickUp Batch 1-2 each

### Phase 5: Complete AP/AR - 2 weeks
1. Bill.com Batch 3-4 (Vendor management, PO matching)
2. Recurly Batch 3-5 (Billing info, coupons, add-ons)
3. NetSuite Batch 1-2 (Bills, credits)

### Phase 6: Subscription & Reporting - 2 weeks
1. Stripe Batch 1-4 (Subscription, invoicing, disputes, reporting)
2. OCR Batch 2 (Document intelligence)

---

## TOTAL ENDPOINT COUNT

| Connector | Current | Adding | Total |
|-----------|---------|--------|-------|
| Bill.com | 9 | 20 | 29 |
| NetSuite | 15 | 20 | 35 |
| Recurly | 12 | 25 | 37 |
| Slack | 6 | 20 | 26 |
| Gmail | 9 | 10 | 19 |
| Plaid | 11 | 15 | 26 |
| Mercury | 6 | 10 | 16 |
| QuickBooks | 45 | 10 | 55 |
| Linear | 10 | 10 | 20 |
| Monday | 13 | 10 | 23 |
| ClickUp | 12 | 10 | 22 |
| Stripe | 61 | 20 | 81 |
| OCR | 6 | 10 | 16 |

**Grand Total: 175 new endpoints across 13 connectors**

---

## SUCCESS CRITERIA

Each endpoint is "done" when:
1. Implemented with proper error handling
2. Structured logging added
3. Registered in capability registry
4. Tested against sandbox/test environment
5. Documented in CLAUDE.md
