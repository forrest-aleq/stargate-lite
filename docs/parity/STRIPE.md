# Stripe API Parity Analysis

**Goal:** The most comprehensive Stripe integration ever built.

**Source:** [Stripe API Reference](https://docs.stripe.com/api)

---

## CURRENT IMPLEMENTATION: 61 Methods

### What We Have

| Resource | Methods | Status |
|----------|---------|--------|
| PaymentIntent | create, retrieve | ✅ |
| Customer | create, retrieve, update, delete, list, search | ✅ |
| Invoice | create, retrieve, update, finalize, pay, send, void, list, delete | ✅ |
| Subscription | create, retrieve, update, cancel, list | ✅ |
| Refund | create, retrieve, update, cancel, list | ✅ |
| Balance | retrieve | ✅ |
| Payout | list, retrieve | ✅ |
| BalanceTransaction | list | ✅ |
| Transfer | create, list | ✅ |
| PaymentMethod | create, retrieve, update, list, attach, detach | ✅ |
| Product | create, retrieve, update, delete, list, search | ✅ |
| Price | create, retrieve, update, list, search | ✅ |
| CheckoutSession | create, retrieve, expire, list, list_line_items | ✅ |
| Dispute | retrieve, update, close, list | ✅ |
| Charge | retrieve, list | ✅ |

---

## MISSING: Core Payments

### PaymentIntent (Expand)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `list` | List all payment intents | HIGH |
| `update` | Update pending payment | HIGH |
| `confirm` | Confirm payment server-side | HIGH |
| `capture` | Capture authorized payment | HIGH |
| `cancel` | Cancel payment intent | HIGH |
| `search` | Search payments | MEDIUM |
| `increment_authorization` | Increase auth amount | LOW |
| `apply_customer_balance` | Use customer credit | MEDIUM |
| `verify_microdeposits` | Bank verification | MEDIUM |

### SetupIntent (NEW - Payment Method Setup)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Save card without charging | HIGH |
| `retrieve` | Get setup status | HIGH |
| `update` | Update setup intent | MEDIUM |
| `confirm` | Confirm setup | HIGH |
| `cancel` | Cancel setup | MEDIUM |
| `list` | List setup intents | MEDIUM |
| `verify_microdeposits` | Verify bank account | MEDIUM |

### PaymentLink (NEW - No-Code Payments)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create payment link | HIGH |
| `retrieve` | Get link details | MEDIUM |
| `update` | Update link | MEDIUM |
| `list` | List payment links | MEDIUM |
| `list_line_items` | Get link items | LOW |

---

## MISSING: Billing & Subscriptions

### Coupon (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create discount | HIGH |
| `retrieve` | Get coupon | MEDIUM |
| `update` | Modify coupon | MEDIUM |
| `delete` | Remove coupon | MEDIUM |
| `list` | List coupons | MEDIUM |

### PromotionCode (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create promo code | HIGH |
| `retrieve` | Get promo code | MEDIUM |
| `update` | Update promo code | MEDIUM |
| `list` | List promo codes | MEDIUM |

### SubscriptionItem (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Add item to subscription | HIGH |
| `retrieve` | Get subscription item | MEDIUM |
| `update` | Update item (quantity) | HIGH |
| `delete` | Remove item | HIGH |
| `list` | List items | MEDIUM |
| `create_usage_record` | Record metered usage | HIGH |
| `list_usage_record_summaries` | Get usage | HIGH |

### SubscriptionSchedule (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Schedule subscription changes | HIGH |
| `retrieve` | Get schedule | MEDIUM |
| `update` | Update schedule | MEDIUM |
| `cancel` | Cancel schedule | MEDIUM |
| `release` | Release schedule | LOW |
| `list` | List schedules | MEDIUM |

### Quote (NEW - Sales Quotes)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create sales quote | HIGH |
| `retrieve` | Get quote | MEDIUM |
| `update` | Update quote | MEDIUM |
| `finalize` | Lock quote | HIGH |
| `accept` | Accept quote | HIGH |
| `cancel` | Cancel quote | MEDIUM |
| `list` | List quotes | MEDIUM |
| `pdf` | Download quote PDF | HIGH |
| `list_line_items` | Get quote items | MEDIUM |

### InvoiceItem (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Add line item | HIGH |
| `retrieve` | Get line item | LOW |
| `update` | Update line item | MEDIUM |
| `delete` | Remove line item | MEDIUM |
| `list` | List items | MEDIUM |

### CreditNote (NEW - Invoice Credits)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Issue credit note | HIGH |
| `preview` | Preview credit | HIGH |
| `retrieve` | Get credit note | MEDIUM |
| `update` | Update credit | MEDIUM |
| `void` | Void credit note | MEDIUM |
| `list` | List credit notes | MEDIUM |
| `list_line_items` | Get credit items | LOW |

### CustomerBalanceTransaction (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Adjust customer credit | HIGH |
| `retrieve` | Get transaction | LOW |
| `update` | Update transaction | LOW |
| `list` | List transactions | MEDIUM |

### CustomerCashBalanceTransaction (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get cash balance txn | LOW |
| `list` | List cash balance txns | MEDIUM |

### TaxID (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Add tax ID to customer | HIGH |
| `retrieve` | Get tax ID | LOW |
| `delete` | Remove tax ID | LOW |
| `list` | List tax IDs | MEDIUM |

---

## MISSING: Treasury (Banking-as-a-Service)

### FinancialAccount (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create financial account | HIGH |
| `retrieve` | Get account | HIGH |
| `update` | Update account | MEDIUM |
| `list` | List accounts | HIGH |
| `retrieve_features` | Get enabled features | MEDIUM |
| `update_features` | Enable features | MEDIUM |

### Transaction (Treasury)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get transaction | HIGH |
| `list` | List transactions | HIGH |

### TransactionEntry
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get entry | LOW |
| `list` | List entries | MEDIUM |

### OutboundTransfer (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Send money out | HIGH |
| `retrieve` | Get transfer status | HIGH |
| `cancel` | Cancel transfer | HIGH |
| `list` | List transfers | HIGH |

### OutboundPayment (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Pay vendor | HIGH |
| `retrieve` | Get payment status | HIGH |
| `cancel` | Cancel payment | HIGH |
| `list` | List payments | HIGH |

### InboundTransfer (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Pull money in | HIGH |
| `retrieve` | Get transfer status | HIGH |
| `cancel` | Cancel transfer | MEDIUM |
| `list` | List transfers | HIGH |

### ReceivedCredit (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get received credit | MEDIUM |
| `list` | List received credits | HIGH |

### ReceivedDebit (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get received debit | MEDIUM |
| `list` | List received debits | HIGH |

### CreditReversal (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Reverse credit | MEDIUM |
| `retrieve` | Get reversal | LOW |
| `list` | List reversals | MEDIUM |

### DebitReversal (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Reverse debit | MEDIUM |
| `retrieve` | Get reversal | LOW |
| `list` | List reversals | MEDIUM |

---

## MISSING: Connect (Multi-Party Payments)

### Account (Connected Accounts)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create connected account | HIGH |
| `retrieve` | Get account | HIGH |
| `update` | Update account | HIGH |
| `delete` | Delete account | MEDIUM |
| `list` | List accounts | HIGH |
| `reject` | Reject account | LOW |

### AccountLink (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Onboarding link | HIGH |

### AccountSession (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Embedded onboarding | HIGH |

### LoginLink (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Dashboard access | MEDIUM |

### ExternalAccount (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Add bank account | HIGH |
| `retrieve` | Get account | MEDIUM |
| `update` | Update account | MEDIUM |
| `delete` | Remove account | MEDIUM |
| `list` | List accounts | HIGH |

### Person (NEW - KYC)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Add business owner | HIGH |
| `retrieve` | Get person | MEDIUM |
| `update` | Update person | MEDIUM |
| `delete` | Remove person | LOW |
| `list` | List persons | MEDIUM |

### ApplicationFee (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get platform fee | MEDIUM |
| `list` | List fees | MEDIUM |

### ApplicationFeeRefund (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Refund platform fee | MEDIUM |
| `retrieve` | Get refund | LOW |
| `update` | Update refund | LOW |
| `list` | List refunds | LOW |

### TransferReversal (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Reverse transfer | MEDIUM |
| `retrieve` | Get reversal | LOW |
| `update` | Update reversal | LOW |
| `list` | List reversals | LOW |

### Capability (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get capability | MEDIUM |
| `update` | Request capability | MEDIUM |
| `list` | List capabilities | MEDIUM |

---

## MISSING: Issuing (Card Programs)

### Cardholder (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create cardholder | HIGH |
| `retrieve` | Get cardholder | MEDIUM |
| `update` | Update cardholder | MEDIUM |
| `list` | List cardholders | HIGH |

### Card (Issuing)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Issue card | HIGH |
| `retrieve` | Get card | HIGH |
| `update` | Update card (status) | HIGH |
| `list` | List cards | HIGH |

### Authorization (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get authorization | HIGH |
| `update` | Approve/decline | HIGH |
| `approve` | Approve auth | HIGH |
| `decline` | Decline auth | HIGH |
| `list` | List authorizations | HIGH |

### Transaction (Issuing)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get transaction | HIGH |
| `update` | Update transaction | LOW |
| `list` | List transactions | HIGH |

### Dispute (Issuing)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create dispute | MEDIUM |
| `retrieve` | Get dispute | MEDIUM |
| `submit` | Submit dispute | MEDIUM |
| `list` | List disputes | MEDIUM |

### PersonalizationDesign (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Custom card design | LOW |
| `retrieve` | Get design | LOW |
| `update` | Update design | LOW |
| `list` | List designs | LOW |

### PhysicalBundle (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get bundle | LOW |
| `list` | List bundles | LOW |

### Token (Issuing)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get token | LOW |
| `update` | Update token | LOW |
| `list` | List tokens | LOW |

---

## MISSING: Terminal (In-Person Payments)

### Reader (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Register reader | HIGH |
| `retrieve` | Get reader | MEDIUM |
| `update` | Update reader | MEDIUM |
| `delete` | Remove reader | LOW |
| `list` | List readers | HIGH |
| `cancel_action` | Cancel pending action | MEDIUM |
| `process_payment_intent` | Start payment | HIGH |
| `process_setup_intent` | Save card | MEDIUM |
| `set_reader_display` | Show on screen | MEDIUM |
| `refund_payment` | Process refund | HIGH |

### Location (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create location | MEDIUM |
| `retrieve` | Get location | LOW |
| `update` | Update location | LOW |
| `delete` | Remove location | LOW |
| `list` | List locations | MEDIUM |

### Configuration (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create config | LOW |
| `retrieve` | Get config | LOW |
| `update` | Update config | LOW |
| `delete` | Remove config | LOW |
| `list` | List configs | LOW |

### ConnectionToken (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Get connection token | HIGH |

---

## MISSING: Reporting & Analytics

### ReportRun (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Generate report | HIGH |
| `retrieve` | Get report | HIGH |
| `list` | List reports | MEDIUM |

### ReportType (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get report type | LOW |
| `list` | List report types | LOW |

### ScheduledQueryRun (Sigma)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get query run | MEDIUM |
| `list` | List query runs | MEDIUM |

---

## MISSING: Tax

### TaxCalculation (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Calculate tax | HIGH |
| `retrieve` | Get calculation | MEDIUM |
| `list_line_items` | Get tax breakdown | MEDIUM |

### TaxTransaction (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create_from_calculation` | Record tax | HIGH |
| `retrieve` | Get transaction | MEDIUM |
| `create_reversal` | Reverse tax | MEDIUM |
| `list_line_items` | Get line items | LOW |

### TaxRegistration (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Add tax registration | HIGH |
| `retrieve` | Get registration | LOW |
| `update` | Update registration | LOW |
| `list` | List registrations | MEDIUM |

### TaxSettings (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get settings | LOW |
| `update` | Update settings | LOW |

### TaxRate (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create tax rate | MEDIUM |
| `retrieve` | Get rate | LOW |
| `update` | Update rate | LOW |
| `list` | List rates | MEDIUM |

---

## MISSING: Identity Verification

### VerificationSession (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Start KYC | HIGH |
| `retrieve` | Get session | HIGH |
| `update` | Update session | LOW |
| `cancel` | Cancel session | LOW |
| `list` | List sessions | MEDIUM |
| `redact` | Delete PII | LOW |

### VerificationReport (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get report | HIGH |
| `list` | List reports | MEDIUM |

---

## MISSING: Webhooks & Events

### Event (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get event | HIGH |
| `list` | List events | HIGH |

### WebhookEndpoint (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create webhook | HIGH |
| `retrieve` | Get webhook | MEDIUM |
| `update` | Update webhook | MEDIUM |
| `delete` | Remove webhook | MEDIUM |
| `list` | List webhooks | HIGH |

---

## MISSING: Files & Documents

### File (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Upload file | HIGH |
| `retrieve` | Get file | MEDIUM |
| `list` | List files | MEDIUM |

### FileLink (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create download link | MEDIUM |
| `retrieve` | Get link | LOW |
| `update` | Update link | LOW |
| `list` | List links | LOW |

---

## MISSING: Financial Connections (Plaid alternative)

### Account (Financial Connections)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get account | HIGH |
| `disconnect` | Disconnect account | MEDIUM |
| `list` | List accounts | HIGH |
| `list_owners` | Get account owners | MEDIUM |
| `refresh` | Refresh data | MEDIUM |
| `subscribe` | Subscribe to updates | MEDIUM |
| `unsubscribe` | Unsubscribe | LOW |

### Session (Financial Connections)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Start connection flow | HIGH |
| `retrieve` | Get session | MEDIUM |

### Transaction (Financial Connections)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get transaction | HIGH |
| `list` | List transactions | HIGH |

---

## MISSING: Miscellaneous

### CountrySpec (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get country requirements | LOW |
| `list` | List countries | LOW |

### Mandate (NEW)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `retrieve` | Get mandate | MEDIUM |

### Source (Legacy)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create source | LOW |
| `retrieve` | Get source | LOW |
| `update` | Update source | LOW |

### TestClock (NEW - Testing)
| Method | Finance Use Case | Priority |
|--------|------------------|----------|
| `create` | Create test clock | HIGH |
| `retrieve` | Get clock | MEDIUM |
| `delete` | Delete clock | LOW |
| `advance` | Advance time | HIGH |
| `list` | List clocks | MEDIUM |

---

## IMPLEMENTATION BATCHES

### Batch 1: Payment Completion (HIGH Priority)
1. PaymentIntent.list
2. PaymentIntent.update
3. PaymentIntent.confirm
4. PaymentIntent.capture
5. PaymentIntent.cancel

### Batch 2: Setup Intents (Save Cards)
1. SetupIntent.create
2. SetupIntent.retrieve
3. SetupIntent.update
4. SetupIntent.confirm
5. SetupIntent.cancel

### Batch 3: Billing Expansion
1. Coupon.create
2. Coupon.retrieve
3. Coupon.list
4. PromotionCode.create
5. PromotionCode.list

### Batch 4: Subscription Items & Usage
1. SubscriptionItem.create
2. SubscriptionItem.update
3. SubscriptionItem.delete
4. SubscriptionItem.create_usage_record
5. SubscriptionItem.list_usage_record_summaries

### Batch 5: Quotes
1. Quote.create
2. Quote.retrieve
3. Quote.finalize
4. Quote.accept
5. Quote.pdf

### Batch 6: Credit Notes
1. CreditNote.create
2. CreditNote.preview
3. CreditNote.retrieve
4. CreditNote.list
5. CreditNote.void

### Batch 7: Invoice Items
1. InvoiceItem.create
2. InvoiceItem.retrieve
3. InvoiceItem.update
4. InvoiceItem.delete
5. InvoiceItem.list

### Batch 8: Customer Balance
1. CustomerBalanceTransaction.create
2. CustomerBalanceTransaction.list
3. TaxID.create
4. TaxID.list
5. TaxID.delete

### Batch 9: Connect Accounts
1. Account.create
2. Account.retrieve
3. Account.update
4. Account.list
5. AccountLink.create

### Batch 10: Connect Onboarding
1. AccountSession.create
2. LoginLink.create
3. Capability.list
4. Capability.update
5. Person.create

### Batch 11: Connect External Accounts
1. ExternalAccount.create
2. ExternalAccount.retrieve
3. ExternalAccount.update
4. ExternalAccount.delete
5. ExternalAccount.list

### Batch 12: Connect Fees
1. ApplicationFee.retrieve
2. ApplicationFee.list
3. ApplicationFeeRefund.create
4. TransferReversal.create
5. TransferReversal.list

### Batch 13: Treasury Core
1. FinancialAccount.create
2. FinancialAccount.retrieve
3. FinancialAccount.list
4. Transaction.retrieve (Treasury)
5. Transaction.list (Treasury)

### Batch 14: Treasury Outbound
1. OutboundTransfer.create
2. OutboundTransfer.retrieve
3. OutboundTransfer.cancel
4. OutboundTransfer.list
5. OutboundPayment.create

### Batch 15: Treasury Outbound (cont)
1. OutboundPayment.retrieve
2. OutboundPayment.cancel
3. OutboundPayment.list
4. InboundTransfer.create
5. InboundTransfer.list

### Batch 16: Treasury Received
1. ReceivedCredit.retrieve
2. ReceivedCredit.list
3. ReceivedDebit.retrieve
4. ReceivedDebit.list
5. CreditReversal.create

### Batch 17: Issuing Cards
1. Cardholder.create
2. Cardholder.retrieve
3. Cardholder.update
4. Cardholder.list
5. Card.create (Issuing)

### Batch 18: Issuing Cards (cont)
1. Card.retrieve (Issuing)
2. Card.update (Issuing)
3. Card.list (Issuing)
4. Authorization.retrieve
5. Authorization.list

### Batch 19: Issuing Auth Control
1. Authorization.approve
2. Authorization.decline
3. Authorization.update
4. Transaction.retrieve (Issuing)
5. Transaction.list (Issuing)

### Batch 20: Terminal
1. ConnectionToken.create
2. Reader.create
3. Reader.retrieve
4. Reader.list
5. Reader.process_payment_intent

### Batch 21: Terminal (cont)
1. Reader.process_setup_intent
2. Reader.refund_payment
3. Reader.cancel_action
4. Location.create
5. Location.list

### Batch 22: Reporting
1. ReportRun.create
2. ReportRun.retrieve
3. ReportRun.list
4. ReportType.list
5. ScheduledQueryRun.list

### Batch 23: Tax
1. TaxCalculation.create
2. TaxCalculation.retrieve
3. TaxTransaction.create_from_calculation
4. TaxRegistration.create
5. TaxRate.create

### Batch 24: Identity
1. VerificationSession.create
2. VerificationSession.retrieve
3. VerificationSession.list
4. VerificationReport.retrieve
5. VerificationReport.list

### Batch 25: Events & Webhooks
1. Event.retrieve
2. Event.list
3. WebhookEndpoint.create
4. WebhookEndpoint.list
5. WebhookEndpoint.delete

### Batch 26: Files
1. File.create
2. File.retrieve
3. File.list
4. FileLink.create
5. FileLink.list

### Batch 27: Financial Connections
1. Session.create (FC)
2. Session.retrieve (FC)
3. Account.retrieve (FC)
4. Account.list (FC)
5. Transaction.list (FC)

### Batch 28: Payment Links
1. PaymentLink.create
2. PaymentLink.retrieve
3. PaymentLink.update
4. PaymentLink.list
5. PaymentLink.list_line_items

### Batch 29: Subscription Schedules
1. SubscriptionSchedule.create
2. SubscriptionSchedule.retrieve
3. SubscriptionSchedule.update
4. SubscriptionSchedule.cancel
5. SubscriptionSchedule.list

### Batch 30: Test Clocks & Misc
1. TestClock.create
2. TestClock.advance
3. TestClock.list
4. Mandate.retrieve
5. CountrySpec.list

---

## SUMMARY

| Category | Current | Missing | Total After |
|----------|---------|---------|-------------|
| Core Payments | 2 | 9 | 11 |
| Setup Intents | 0 | 7 | 7 |
| Payment Links | 0 | 5 | 5 |
| Billing | 25 | 40 | 65 |
| Treasury | 0 | 25 | 25 |
| Connect | 2 | 25 | 27 |
| Issuing | 0 | 25 | 25 |
| Terminal | 0 | 15 | 15 |
| Reporting | 0 | 5 | 5 |
| Tax | 0 | 10 | 10 |
| Identity | 0 | 6 | 6 |
| Webhooks/Events | 0 | 7 | 7 |
| Files | 0 | 5 | 5 |
| Financial Connections | 0 | 10 | 10 |
| Misc | 0 | 5 | 5 |
| **TOTAL** | **61** | **~200** | **~261** |

---

## FINANCE WORKFLOW COVERAGE

After full implementation:

| Workflow | Status |
|----------|--------|
| Accept payments | ✅ Complete |
| Recurring billing | ✅ Complete |
| Invoicing | ✅ Complete |
| Refunds & disputes | ✅ Complete |
| Sales quotes | ✅ Complete |
| Discounts & promos | ✅ Complete |
| Usage-based billing | ✅ Complete |
| Tax calculation | ✅ Complete |
| Multi-party payments (Connect) | ✅ Complete |
| Embedded finance (Treasury) | ✅ Complete |
| Corporate cards (Issuing) | ✅ Complete |
| In-person payments (Terminal) | ✅ Complete |
| Bank connections | ✅ Complete |
| Identity verification | ✅ Complete |
| Financial reporting | ✅ Complete |

**This would be the most comprehensive Stripe integration ever built.**
