"""
QuickBooks Online Deep Link Generator

Generates direct URLs to open specific records in the QBO web interface.
These links allow users to jump directly to invoices, bills, vendors, etc.

URL Pattern: https://app.qbo.intuit.com/app/{entity_type}?txnId={id}
             https://app.qbo.intuit.com/app/{entity_type}detail?nameId={id}

Note: User must be logged into the correct QBO company for links to work.
"""

# Base URL for QuickBooks Online web app
QBO_BASE_URL = "https://app.qbo.intuit.com/app"


def invoice_link(entity_id: str | int) -> str:
    """Generate deep link to an Invoice."""
    return f"{QBO_BASE_URL}/invoice?txnId={entity_id}"


def bill_link(entity_id: str | int) -> str:
    """Generate deep link to a Bill."""
    return f"{QBO_BASE_URL}/bill?txnId={entity_id}"


def bill_payment_link(entity_id: str | int) -> str:
    """Generate deep link to a Bill Payment."""
    return f"{QBO_BASE_URL}/billpayment?txnId={entity_id}"


def payment_link(entity_id: str | int) -> str:
    """Generate deep link to a Payment (received)."""
    return f"{QBO_BASE_URL}/recvpayment?txnId={entity_id}"


def journal_entry_link(entity_id: str | int) -> str:
    """Generate deep link to a Journal Entry."""
    return f"{QBO_BASE_URL}/journal?txnId={entity_id}"


def estimate_link(entity_id: str | int) -> str:
    """Generate deep link to an Estimate."""
    return f"{QBO_BASE_URL}/estimate?txnId={entity_id}"


def purchase_order_link(entity_id: str | int) -> str:
    """Generate deep link to a Purchase Order."""
    return f"{QBO_BASE_URL}/purchaseorder?txnId={entity_id}"


def expense_link(entity_id: str | int) -> str:
    """Generate deep link to an Expense."""
    return f"{QBO_BASE_URL}/expense?txnId={entity_id}"


def credit_memo_link(entity_id: str | int) -> str:
    """Generate deep link to a Credit Memo."""
    return f"{QBO_BASE_URL}/creditmemo?txnId={entity_id}"


def refund_receipt_link(entity_id: str | int) -> str:
    """Generate deep link to a Refund Receipt."""
    return f"{QBO_BASE_URL}/refundreceipt?txnId={entity_id}"


def sales_receipt_link(entity_id: str | int) -> str:
    """Generate deep link to a Sales Receipt."""
    return f"{QBO_BASE_URL}/salesreceipt?txnId={entity_id}"


def deposit_link(entity_id: str | int) -> str:
    """Generate deep link to a Deposit."""
    return f"{QBO_BASE_URL}/deposit?txnId={entity_id}"


def transfer_link(entity_id: str | int) -> str:
    """Generate deep link to a Transfer."""
    return f"{QBO_BASE_URL}/transfer?txnId={entity_id}"


# --- Name-based entities (use nameId instead of txnId) ---


def vendor_link(entity_id: str | int) -> str:
    """Generate deep link to a Vendor."""
    return f"{QBO_BASE_URL}/vendordetail?nameId={entity_id}"


def customer_link(entity_id: str | int) -> str:
    """Generate deep link to a Customer."""
    return f"{QBO_BASE_URL}/customerdetail?nameId={entity_id}"


def employee_link(entity_id: str | int) -> str:
    """Generate deep link to an Employee."""
    return f"{QBO_BASE_URL}/employeedetail?nameId={entity_id}"


# --- Chart of Accounts ---


def account_link(entity_id: str | int) -> str:
    """Generate deep link to an Account in Chart of Accounts."""
    return f"{QBO_BASE_URL}/register?accountId={entity_id}"


# --- Items ---


def item_link(entity_id: str | int) -> str:
    """Generate deep link to an Item (product/service)."""
    return f"{QBO_BASE_URL}/item?itemId={entity_id}"
