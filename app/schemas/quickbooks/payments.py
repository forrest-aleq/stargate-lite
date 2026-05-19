"""
QuickBooks Payment Capability Schemas.

Rich metadata for customer payment operations.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

PAYMENT_CREATE = CapabilitySchema(
    capability_key="qb.payment.create",
    service="quickbooks",
    category="payments",
    description="Create a payment (customer payment) in QuickBooks",
    description_detailed=(
        "Records a payment received from a customer. Can be applied to specific invoices "
        "using invoice_ids, or recorded as unapplied payment."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
            example="qb:123",
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Payment amount",
            example=500.00,
        ),
        "invoice_ids": ParameterSchema(
            type="array",
            required=False,
            description="Invoice IDs to apply payment to",
            items_type="string",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Payment date (YYYY-MM-DD)",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(type="string", description="Payment ID"),
        "amount": ReturnFieldSchema(type="number", description="Amount"),
        "customer_id": ReturnFieldSchema(type="string", description="Customer ID"),
        "txn_date": ReturnFieldSchema(type="string", description="Transaction date"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this payment in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/recvpayment?txnId=456",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid customer_id or invoice_ids",
            recovery_hint="Verify IDs exist",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.invoice.list_outstanding", "qb.customer.get"],
        typically_followed_by=["qb.invoice.get", "payment.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

PAYMENT_GET = CapabilitySchema(
    capability_key="qb.payment.get",
    service="quickbooks",
    category="payments",
    description="Get payment details from QuickBooks",
    parameters={
        "payment_id": ParameterSchema(
            type="string",
            required=True,
            description="Payment ID",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(type="string", description="Payment ID"),
        "amount": ReturnFieldSchema(type="number", description="Amount"),
        "customer_id": ReturnFieldSchema(type="string", description="Customer ID"),
        "txn_date": ReturnFieldSchema(type="string", description="Date"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this payment in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/recvpayment?txnId=456",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

PAYMENT_APPLY_TO_INVOICE = CapabilitySchema(
    capability_key="payment.apply_to_invoice",
    service="quickbooks",
    category="payments",
    description="Apply payment to specific invoice(s) with multi-invoice allocation",
    description_detailed=(
        "Creates a payment and applies it to one or more invoices with specific amounts. "
        "Enables complex payment allocation scenarios where a single payment covers "
        "multiple invoices."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "invoice_allocations": ParameterSchema(
            type="array",
            required=True,
            description="Array of {invoice_id, amount} for each invoice",
            items_type="object",
            example=[
                {"invoice_id": "qb:123", "amount": 300.00},
                {"invoice_id": "qb:124", "amount": 200.00},
            ],
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method",
            default="check",
            enum=["check", "cash", "credit_card", "bank_transfer", "debit_card"],
        ),
        "reference": ParameterSchema(
            type="string",
            required=False,
            description="Reference number or note",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Payment date",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(type="string", description="Payment ID"),
        "customer_id": ReturnFieldSchema(type="string", description="Customer"),
        "total_amount": ReturnFieldSchema(type="number", description="Total paid"),
        "invoice_allocations": ReturnFieldSchema(
            type="array",
            description="How payment was allocated",
        ),
        "status": ReturnFieldSchema(type="string", description="'applied'"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this payment in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/recvpayment?txnId=456",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Amount exceeds invoice balance",
            recovery_hint="Check invoice balances with qb.invoice.list_outstanding",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.invoice.list_outstanding"],
        typically_followed_by=["qb.invoice.get"],
        related_capabilities=["qb.payment.create", "payment.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

PAYMENT_LIST = CapabilitySchema(
    capability_key="payment.list",
    service="quickbooks",
    category="payments",
    description="List customer payments with optional filters",
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results to return",
            default=100,
        ),
    },
    returns={
        "payments": ReturnFieldSchema(
            type="array",
            description="List of payment objects (each includes deep_link URL to QBO)",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number returned"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

PAYMENT_SCHEMAS: dict[str, CapabilitySchema] = {
    "qb.payment.create": PAYMENT_CREATE,
    "qb.payment.get": PAYMENT_GET,
    "payment.apply_to_invoice": PAYMENT_APPLY_TO_INVOICE,
    "payment.list": PAYMENT_LIST,
}
