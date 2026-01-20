"""
Sage Intacct Capability Registry.

Registers all Sage Intacct capabilities for the execution engine.
Total: 48 capabilities across GL, AP, AR, and Cash Management.
"""

from app.connectors.sage_intacct import SageIntacctConnector

_connector = SageIntacctConnector()

SAGE_INTACCT_CAPABILITIES = {
    # ==================== Company ====================
    "sage_intacct.company.get": {
        "handler": _connector.get_company_info,
        "tool_name": "sage_intacct.get_company_info",
        "description": "Get Sage Intacct company information",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== General Ledger - Accounts ====================
    "sage_intacct.accounts.list": {
        "handler": _connector.list_accounts,
        "tool_name": "sage_intacct.list_accounts",
        "description": "List chart of accounts from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.accounts.get": {
        "handler": _connector.get_account,
        "tool_name": "sage_intacct.get_account",
        "description": "Get a specific GL account from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.accounts.create": {
        "handler": _connector.create_account,
        "tool_name": "sage_intacct.create_account",
        "description": "Create a new GL account in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.accounts.update": {
        "handler": _connector.update_account,
        "tool_name": "sage_intacct.update_account",
        "description": "Update a GL account in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== General Ledger - Journal Entries ====================
    "sage_intacct.journals.list": {
        "handler": _connector.list_journal_entries,
        "tool_name": "sage_intacct.list_journal_entries",
        "description": "List journal entries from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.journals.get": {
        "handler": _connector.get_journal_entry,
        "tool_name": "sage_intacct.get_journal_entry",
        "description": "Get a specific journal entry from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.journals.create": {
        "handler": _connector.create_journal_entry,
        "tool_name": "sage_intacct.create_journal_entry",
        "description": "Create a journal entry in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.journals.post": {
        "handler": _connector.post_journal_entry,
        "tool_name": "sage_intacct.post_journal_entry",
        "description": "Post a draft journal entry in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.journals.reverse": {
        "handler": _connector.reverse_journal_entry,
        "tool_name": "sage_intacct.reverse_journal_entry",
        "description": "Create a reversing journal entry in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== General Ledger - Reports ====================
    "sage_intacct.reports.trial_balance": {
        "handler": _connector.get_trial_balance,
        "tool_name": "sage_intacct.get_trial_balance",
        "description": "Get trial balance report from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Accounts Payable - Vendors ====================
    "sage_intacct.vendors.list": {
        "handler": _connector.list_vendors,
        "tool_name": "sage_intacct.list_vendors",
        "description": "List vendors from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.vendors.get": {
        "handler": _connector.get_vendor,
        "tool_name": "sage_intacct.get_vendor",
        "description": "Get a specific vendor from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.vendors.create": {
        "handler": _connector.create_vendor,
        "tool_name": "sage_intacct.create_vendor",
        "description": "Create a vendor in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.vendors.update": {
        "handler": _connector.update_vendor,
        "tool_name": "sage_intacct.update_vendor",
        "description": "Update a vendor in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Accounts Payable - Bills ====================
    "sage_intacct.bills.list": {
        "handler": _connector.list_bills,
        "tool_name": "sage_intacct.list_bills",
        "description": "List AP bills from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.bills.get": {
        "handler": _connector.get_bill,
        "tool_name": "sage_intacct.get_bill",
        "description": "Get a specific AP bill from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.bills.create": {
        "handler": _connector.create_bill,
        "tool_name": "sage_intacct.create_bill",
        "description": "Create an AP bill in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.bills.post": {
        "handler": _connector.post_bill,
        "tool_name": "sage_intacct.post_bill",
        "description": "Post a draft AP bill in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Accounts Payable - Payments ====================
    "sage_intacct.bill_payments.list": {
        "handler": _connector.list_bill_payments,
        "tool_name": "sage_intacct.list_bill_payments",
        "description": "List bill payments from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.bill_payments.create": {
        "handler": _connector.create_bill_payment,
        "tool_name": "sage_intacct.create_bill_payment",
        "description": "Create a bill payment in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Accounts Payable - Aging ====================
    "sage_intacct.reports.ap_aging": {
        "handler": _connector.get_ap_aging,
        "tool_name": "sage_intacct.get_ap_aging",
        "description": "Get AP aging report from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Accounts Receivable - Customers ====================
    "sage_intacct.customers.list": {
        "handler": _connector.list_customers,
        "tool_name": "sage_intacct.list_customers",
        "description": "List customers from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.customers.get": {
        "handler": _connector.get_customer,
        "tool_name": "sage_intacct.get_customer",
        "description": "Get a specific customer from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.customers.create": {
        "handler": _connector.create_customer,
        "tool_name": "sage_intacct.create_customer",
        "description": "Create a customer in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.customers.update": {
        "handler": _connector.update_customer,
        "tool_name": "sage_intacct.update_customer",
        "description": "Update a customer in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Accounts Receivable - Invoices ====================
    "sage_intacct.invoices.list": {
        "handler": _connector.list_ar_invoices,
        "tool_name": "sage_intacct.list_ar_invoices",
        "description": "List AR invoices from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.invoices.get": {
        "handler": _connector.get_ar_invoice,
        "tool_name": "sage_intacct.get_ar_invoice",
        "description": "Get a specific AR invoice from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.invoices.create": {
        "handler": _connector.create_ar_invoice,
        "tool_name": "sage_intacct.create_ar_invoice",
        "description": "Create an AR invoice in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.invoices.post": {
        "handler": _connector.post_ar_invoice,
        "tool_name": "sage_intacct.post_ar_invoice",
        "description": "Post a draft AR invoice in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.invoices.void": {
        "handler": _connector.void_ar_invoice,
        "tool_name": "sage_intacct.void_ar_invoice",
        "description": "Void an AR invoice in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Accounts Receivable - Payments ====================
    "sage_intacct.ar_payments.list": {
        "handler": _connector.list_ar_payments,
        "tool_name": "sage_intacct.list_ar_payments",
        "description": "List AR payments (customer payments) from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.ar_payments.create": {
        "handler": _connector.create_ar_payment,
        "tool_name": "sage_intacct.create_ar_payment",
        "description": "Record an AR payment in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Accounts Receivable - Aging & Credit Memos ====================
    "sage_intacct.reports.ar_aging": {
        "handler": _connector.get_ar_aging,
        "tool_name": "sage_intacct.get_ar_aging",
        "description": "Get AR aging report from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.credit_memos.create": {
        "handler": _connector.create_credit_memo,
        "tool_name": "sage_intacct.create_credit_memo",
        "description": "Create an AR credit memo in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Cash Management - Bank Accounts ====================
    "sage_intacct.bank_accounts.list": {
        "handler": _connector.list_bank_accounts,
        "tool_name": "sage_intacct.list_bank_accounts",
        "description": "List bank accounts from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.bank_accounts.get": {
        "handler": _connector.get_bank_account,
        "tool_name": "sage_intacct.get_bank_account",
        "description": "Get a specific bank account from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.bank_accounts.balance": {
        "handler": _connector.get_bank_account_balance,
        "tool_name": "sage_intacct.get_bank_account_balance",
        "description": "Get bank account balance from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Cash Management - Transactions ====================
    "sage_intacct.bank_transactions.list": {
        "handler": _connector.list_bank_transactions,
        "tool_name": "sage_intacct.list_bank_transactions",
        "description": "List bank transactions from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.deposits.create": {
        "handler": _connector.create_deposit,
        "tool_name": "sage_intacct.create_deposit",
        "description": "Create a bank deposit in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.transfers.create": {
        "handler": _connector.create_bank_transfer,
        "tool_name": "sage_intacct.create_bank_transfer",
        "description": "Create a bank transfer in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Cash Management - Reconciliation ====================
    "sage_intacct.reconciliation.get": {
        "handler": _connector.reconcile_bank_account,
        "tool_name": "sage_intacct.reconcile_bank_account",
        "description": "Get bank reconciliation data from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    "sage_intacct.reconciliation.clear": {
        "handler": _connector.mark_transactions_cleared,
        "tool_name": "sage_intacct.mark_transactions_cleared",
        "description": "Mark bank transactions as cleared in Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
    # ==================== Cash Management - Reports ====================
    "sage_intacct.reports.cash_flow": {
        "handler": _connector.get_cash_flow_statement,
        "tool_name": "sage_intacct.get_cash_flow_statement",
        "description": "Get cash flow statement from Sage Intacct",
        "requires_oauth": True,
        "service": "sage_intacct",
    },
}
