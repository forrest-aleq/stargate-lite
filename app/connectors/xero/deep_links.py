"""
Xero Deep Link Generator

Generates direct URLs to open specific records in the Xero web interface.
These links allow users to jump directly to invoices, bills, contacts, etc.

URL Pattern: https://go.xero.com/{path}

Reference: https://developer.xero.com/documentation/guides/how-to-guides/deep-link-xero

Note: User must be logged into the correct Xero organisation for links to work.
      For multi-org support, upgrade to shortcode-based URLs:
      https://go.xero.com/organisationlogin/default.aspx?shortcode=!{code}&redirecturl=/{path}
"""

# Base URL for Xero web app
XERO_BASE_URL = "https://go.xero.com"


def invoice_link(invoice_id: str | None) -> str | None:
    """Generate deep link to a sales invoice (AR)."""
    if not invoice_id:
        return None
    return f"{XERO_BASE_URL}/AccountsReceivable/View.aspx?InvoiceID={invoice_id}"


def bill_link(invoice_id: str | None) -> str | None:
    """Generate deep link to a bill (AP).

    Bills in Xero are invoices with Type=ACCPAY.
    The Xero UI uses InvoiceID in the URL.
    """
    if not invoice_id:
        return None
    return f"{XERO_BASE_URL}/AccountsPayable/View.aspx?InvoiceID={invoice_id}"


def contact_link(contact_id: str | None) -> str | None:
    """Generate deep link to a contact."""
    if not contact_id:
        return None
    return f"{XERO_BASE_URL}/Contacts/View.aspx?contactID={contact_id}"


def credit_note_link(credit_note_id: str | None, cn_type: str | None = None) -> str | None:
    """Generate deep link to a credit note.

    Routes to AR or AP view based on type:
    - ACCRECCREDIT → AccountsReceivable
    - ACCPAYCREDIT → AccountsPayable
    """
    if not credit_note_id:
        return None
    if cn_type == "ACCPAYCREDIT":
        return f"{XERO_BASE_URL}/AccountsPayable/ViewCreditNote.aspx?CreditNoteID={credit_note_id}"
    # Default to AR (ACCRECCREDIT)
    return f"{XERO_BASE_URL}/AccountsReceivable/ViewCreditNote.aspx?CreditNoteID={credit_note_id}"


def bank_transaction_link(transaction_id: str | None) -> str | None:
    """Generate deep link to a bank transaction."""
    if not transaction_id:
        return None
    return f"{XERO_BASE_URL}/Bank/View.aspx?bankTransactionID={transaction_id}"


def bank_account_link(account_id: str | None) -> str | None:
    """Generate deep link to a bank account."""
    if not account_id:
        return None
    return f"{XERO_BASE_URL}/Bank/BankAccount.aspx?accountID={account_id}"


def bank_transfer_link(transfer_id: str | None) -> str | None:
    """Generate deep link to a bank transfer."""
    if not transfer_id:
        return None
    return f"{XERO_BASE_URL}/Bank/ViewTransfer.aspx?bankTransferID={transfer_id}"


def manual_journal_link(journal_id: str | None) -> str | None:
    """Generate deep link to a manual journal entry."""
    if not journal_id:
        return None
    return f"{XERO_BASE_URL}/ManualJournals/View.aspx?ManualJournalID={journal_id}"


def payment_link(invoice_id: str | None, invoice_type: str | None = None) -> str | None:
    """Generate deep link for a payment.

    Payments don't have their own page in Xero — link to the parent
    invoice or bill instead.
    """
    if not invoice_id:
        return None
    if invoice_type == "ACCPAY":
        return bill_link(invoice_id)
    return invoice_link(invoice_id)


def chart_of_accounts_link() -> str:
    """Generate deep link to the Chart of Accounts page.

    Xero has no per-account deep link — links to the full CoA list.
    """
    return f"{XERO_BASE_URL}/ChartOfAccounts"
