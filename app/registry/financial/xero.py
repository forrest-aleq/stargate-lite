"""
Xero Accounting Capability Registry - 60+ capabilities for full accounting automation.

Reference: https://developer.xero.com/documentation/api/accounting/overview

Categories:
- Organization: org info, connections
- Contacts: customers and suppliers
- Invoices: sales invoices (AR)
- Bills: supplier bills (AP)
- Payments: payment recording
- Credit Notes: credits and allocations
- Bank: bank accounts and transactions
- Reports: financial reporting
- Journals: GL journal entries
"""

from app.connectors.xero import xero_connector

XERO_CAPABILITIES = {
    # ==================== ORGANIZATION ====================
    "xero.organization.get": {
        "handler": xero_connector.get_organization,
        "tool_name": "xero.get_organization",
        "description": "Get details of the connected Xero organization",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.connections.list": {
        "handler": xero_connector.list_connections,
        "tool_name": "xero.list_connections",
        "description": "List all Xero organizations the user has connected",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== CONTACTS ====================
    "xero.contact.list": {
        "handler": xero_connector.list_contacts,
        "tool_name": "xero.list_contacts",
        "description": "List contacts (customers and suppliers) with filtering",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.contact.get": {
        "handler": xero_connector.get_contact,
        "tool_name": "xero.get_contact",
        "description": "Get a specific contact by ID or contact number",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.contact.create": {
        "handler": xero_connector.create_contact,
        "tool_name": "xero.create_contact",
        "description": "Create a new customer or supplier contact",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.contact.update": {
        "handler": xero_connector.update_contact,
        "tool_name": "xero.update_contact",
        "description": "Update an existing contact",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.contact.archive": {
        "handler": xero_connector.archive_contact,
        "tool_name": "xero.archive_contact",
        "description": "Archive (soft delete) a contact",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.contact.search": {
        "handler": xero_connector.search_contacts,
        "tool_name": "xero.search_contacts",
        "description": "Search contacts by name, email, or account number",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.contact.history": {
        "handler": xero_connector.get_contact_history,
        "tool_name": "xero.get_contact_history",
        "description": "Get activity history for a contact",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== INVOICES (AR) ====================
    "xero.invoice.list": {
        "handler": xero_connector.list_invoices,
        "tool_name": "xero.list_invoices",
        "description": "List sales invoices with filtering and pagination",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.invoice.get": {
        "handler": xero_connector.get_invoice,
        "tool_name": "xero.get_invoice",
        "description": "Get a specific invoice by ID or invoice number",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.invoice.create": {
        "handler": xero_connector.create_invoice,
        "tool_name": "xero.create_invoice",
        "description": "Create a new sales invoice",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.invoice.update": {
        "handler": xero_connector.update_invoice,
        "tool_name": "xero.update_invoice",
        "description": "Update an existing invoice (DRAFT/SUBMITTED only)",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.invoice.void": {
        "handler": xero_connector.void_invoice,
        "tool_name": "xero.void_invoice",
        "description": "Void an invoice",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.invoice.email": {
        "handler": xero_connector.email_invoice,
        "tool_name": "xero.email_invoice",
        "description": "Email an invoice to the customer",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.invoice.pdf": {
        "handler": xero_connector.get_invoice_pdf,
        "tool_name": "xero.get_invoice_pdf",
        "description": "Get the online invoice URL/PDF link",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.invoice.outstanding": {
        "handler": xero_connector.get_outstanding_invoices,
        "tool_name": "xero.get_outstanding_invoices",
        "description": "Get all outstanding (unpaid) invoices",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.ar.aging": {
        "handler": xero_connector.get_ar_aging,
        "tool_name": "xero.get_ar_aging",
        "description": "Get accounts receivable aging summary with buckets",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== BILLS (AP) ====================
    "xero.bill.list": {
        "handler": xero_connector.list_bills,
        "tool_name": "xero.list_bills",
        "description": "List supplier bills with filtering and pagination",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bill.get": {
        "handler": xero_connector.get_bill,
        "tool_name": "xero.get_bill",
        "description": "Get a specific bill by ID",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bill.create": {
        "handler": xero_connector.create_bill,
        "tool_name": "xero.create_bill",
        "description": "Create a new supplier bill",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bill.update": {
        "handler": xero_connector.update_bill,
        "tool_name": "xero.update_bill",
        "description": "Update an existing bill (DRAFT/SUBMITTED only)",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bill.void": {
        "handler": xero_connector.void_bill,
        "tool_name": "xero.void_bill",
        "description": "Void a bill",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bill.outstanding": {
        "handler": xero_connector.get_outstanding_bills,
        "tool_name": "xero.get_outstanding_bills",
        "description": "Get all outstanding (unpaid) bills",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.ap.aging": {
        "handler": xero_connector.get_ap_aging,
        "tool_name": "xero.get_ap_aging",
        "description": "Get accounts payable aging summary with buckets",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== PAYMENTS ====================
    "xero.payment.list": {
        "handler": xero_connector.list_payments,
        "tool_name": "xero.list_payments",
        "description": "List payments with filtering",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.payment.get": {
        "handler": xero_connector.get_payment,
        "tool_name": "xero.get_payment",
        "description": "Get a specific payment by ID",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.payment.create": {
        "handler": xero_connector.create_payment,
        "tool_name": "xero.create_payment",
        "description": "Create a payment for an invoice",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.payment.create_bill": {
        "handler": xero_connector.create_bill_payment,
        "tool_name": "xero.create_bill_payment",
        "description": "Create a payment for a bill (AP payment)",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.payment.delete": {
        "handler": xero_connector.delete_payment,
        "tool_name": "xero.delete_payment",
        "description": "Delete (reverse) an unreconciled payment",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.payment.history": {
        "handler": xero_connector.get_payment_history,
        "tool_name": "xero.get_payment_history",
        "description": "Get history for a payment",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.payment.batch": {
        "handler": xero_connector.create_batch_payment,
        "tool_name": "xero.create_batch_payment",
        "description": "Create batch payment for multiple bills",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== CREDIT NOTES ====================
    "xero.creditnote.list": {
        "handler": xero_connector.list_credit_notes,
        "tool_name": "xero.list_credit_notes",
        "description": "List credit notes with filtering",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.creditnote.get": {
        "handler": xero_connector.get_credit_note,
        "tool_name": "xero.get_credit_note",
        "description": "Get a specific credit note by ID",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.creditnote.create_customer": {
        "handler": xero_connector.create_customer_credit_note,
        "tool_name": "xero.create_customer_credit_note",
        "description": "Create a customer credit note (reduces AR)",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.creditnote.create_supplier": {
        "handler": xero_connector.create_supplier_credit_note,
        "tool_name": "xero.create_supplier_credit_note",
        "description": "Create a supplier credit note (reduces AP)",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.creditnote.allocate": {
        "handler": xero_connector.allocate_credit_note,
        "tool_name": "xero.allocate_credit_note",
        "description": "Allocate a credit note to invoices",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.creditnote.void": {
        "handler": xero_connector.void_credit_note,
        "tool_name": "xero.void_credit_note",
        "description": "Void a credit note",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== BANK ACCOUNTS ====================
    "xero.bank.accounts.list": {
        "handler": xero_connector.list_bank_accounts,
        "tool_name": "xero.list_bank_accounts",
        "description": "List all bank accounts",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bank.account.get": {
        "handler": xero_connector.get_bank_account,
        "tool_name": "xero.get_bank_account",
        "description": "Get a specific bank account",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== BANK TRANSACTIONS ====================
    "xero.bank.transactions.list": {
        "handler": xero_connector.list_bank_transactions,
        "tool_name": "xero.list_bank_transactions",
        "description": "List bank transactions with filtering",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bank.transaction.get": {
        "handler": xero_connector.get_bank_transaction,
        "tool_name": "xero.get_bank_transaction",
        "description": "Get a specific bank transaction",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bank.transaction.create": {
        "handler": xero_connector.create_bank_transaction,
        "tool_name": "xero.create_bank_transaction",
        "description": "Create a bank transaction (spend or receive)",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bank.spend": {
        "handler": xero_connector.create_spend_transaction,
        "tool_name": "xero.create_spend_transaction",
        "description": "Create a spend (money out) transaction",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bank.receive": {
        "handler": xero_connector.create_receive_transaction,
        "tool_name": "xero.create_receive_transaction",
        "description": "Create a receive (money in) transaction",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bank.transaction.delete": {
        "handler": xero_connector.delete_bank_transaction,
        "tool_name": "xero.delete_bank_transaction",
        "description": "Delete a bank transaction",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bank.statement": {
        "handler": xero_connector.get_bank_statement,
        "tool_name": "xero.get_bank_statement",
        "description": "Get bank statement lines for an account",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== BANK TRANSFERS ====================
    "xero.bank.transfers.list": {
        "handler": xero_connector.get_bank_transfers,
        "tool_name": "xero.get_bank_transfers",
        "description": "List bank transfers between accounts",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.bank.transfer.create": {
        "handler": xero_connector.create_bank_transfer,
        "tool_name": "xero.create_bank_transfer",
        "description": "Create a bank transfer between accounts",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== REPORTS ====================
    "xero.report.profit_loss": {
        "handler": xero_connector.get_profit_and_loss,
        "tool_name": "xero.get_profit_and_loss",
        "description": "Get Profit and Loss report",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.report.balance_sheet": {
        "handler": xero_connector.get_balance_sheet,
        "tool_name": "xero.get_balance_sheet",
        "description": "Get Balance Sheet report",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.report.trial_balance": {
        "handler": xero_connector.get_trial_balance,
        "tool_name": "xero.get_trial_balance",
        "description": "Get Trial Balance report",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.report.aged_receivables": {
        "handler": xero_connector.get_aged_receivables,
        "tool_name": "xero.get_aged_receivables",
        "description": "Get Aged Receivables by Contact report",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.report.aged_payables": {
        "handler": xero_connector.get_aged_payables,
        "tool_name": "xero.get_aged_payables",
        "description": "Get Aged Payables by Contact report",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.report.budget_summary": {
        "handler": xero_connector.get_budget_summary,
        "tool_name": "xero.get_budget_summary",
        "description": "Get Budget Summary report",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== CHART OF ACCOUNTS ====================
    "xero.accounts.list": {
        "handler": xero_connector.list_accounts,
        "tool_name": "xero.list_accounts",
        "description": "List chart of accounts",
        "requires_oauth": True,
        "service": "xero",
    },
    # ==================== JOURNALS ====================
    "xero.journal.list": {
        "handler": xero_connector.list_manual_journals,
        "tool_name": "xero.list_manual_journals",
        "description": "List manual journal entries",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.journal.get": {
        "handler": xero_connector.get_manual_journal,
        "tool_name": "xero.get_manual_journal",
        "description": "Get a specific manual journal entry",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.journal.create": {
        "handler": xero_connector.create_manual_journal,
        "tool_name": "xero.create_manual_journal",
        "description": "Create a manual journal entry",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.journal.void": {
        "handler": xero_connector.void_manual_journal,
        "tool_name": "xero.void_manual_journal",
        "description": "Void a manual journal entry",
        "requires_oauth": True,
        "service": "xero",
    },
    "xero.journals.system": {
        "handler": xero_connector.list_journals,
        "tool_name": "xero.list_journals",
        "description": "List all system journals (including auto-generated)",
        "requires_oauth": True,
        "service": "xero",
    },
}
