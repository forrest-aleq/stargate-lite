"""
QuickBooks Sales Capability Schemas.

Rich metadata for estimates, sales receipts, credit memos, time activities, and refunds.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

ESTIMATE_CREATE = CapabilitySchema(
    capability_key="estimate.create",
    service="quickbooks",
    category="sales",
    description="Create an estimate in QuickBooks",
    description_detailed=(
        "Creates a quote/estimate for a customer. Estimates can be converted to invoices "
        "and are useful for quoting before work begins."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Line items",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Estimate date",
        ),
        "expiration_date": ParameterSchema(
            type="string",
            required=False,
            description="Quote expiration date",
        ),
        "customer_memo": ParameterSchema(
            type="string",
            required=False,
            description="Message",
        ),
    },
    returns={
        "estimate_id": ReturnFieldSchema(type="string", description="Estimate ID"),
        "doc_number": ReturnFieldSchema(type="string", description="Estimate number"),
        "total_amount": ReturnFieldSchema(type="number", description="Total"),
        "customer_id": ReturnFieldSchema(type="string", description="Customer"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this estimate in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/estimate?txnId=100",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.customer.search", "item.list"],
        typically_followed_by=["qb.invoice.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

ESTIMATE_GET = CapabilitySchema(
    capability_key="estimate.get",
    service="quickbooks",
    category="sales",
    description="Get estimate details from QuickBooks",
    parameters={
        "estimate_id": ParameterSchema(
            type="string",
            required=True,
            description="Estimate ID",
        ),
    },
    returns={
        "estimate_id": ReturnFieldSchema(type="string", description="Estimate ID"),
        "doc_number": ReturnFieldSchema(type="string", description="Number"),
        "customer_id": ReturnFieldSchema(type="string", description="Customer"),
        "total_amount": ReturnFieldSchema(type="number", description="Total"),
        "expiration_date": ReturnFieldSchema(type="string", description="Expires"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this estimate in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/estimate?txnId=100",
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

SALES_RECEIPT_CREATE = CapabilitySchema(
    capability_key="salesreceipt.create",
    service="quickbooks",
    category="sales",
    description="Create a sales receipt in QuickBooks",
    description_detailed=(
        "Creates a sales receipt for immediate payment transactions. Unlike invoices, "
        "sales receipts are used when payment is received at time of sale."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Line items",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Sale date",
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method name",
        ),
    },
    returns={
        "sales_receipt_id": ReturnFieldSchema(type="string", description="Receipt ID"),
        "doc_number": ReturnFieldSchema(type="string", description="Receipt number"),
        "total_amount": ReturnFieldSchema(type="number", description="Total"),
        "customer_id": ReturnFieldSchema(type="string", description="Customer"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this sales receipt in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/salesreceipt?txnId=200",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

CREDIT_MEMO_CREATE = CapabilitySchema(
    capability_key="creditmemo.create",
    service="quickbooks",
    category="sales",
    description="Create a credit memo in QuickBooks",
    description_detailed=(
        "Creates a credit memo to reduce a customer's balance. Can be applied to "
        "outstanding invoices or remain as available credit."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Credit line items",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Date",
        ),
    },
    returns={
        "credit_memo_id": ReturnFieldSchema(type="string", description="Credit memo ID"),
        "doc_number": ReturnFieldSchema(type="string", description="Number"),
        "total_amount": ReturnFieldSchema(type="number", description="Credit amount"),
        "customer_id": ReturnFieldSchema(type="string", description="Customer"),
        "balance": ReturnFieldSchema(type="number", description="Unapplied balance"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this credit memo in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/creditmemo?txnId=300",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        related_capabilities=["qb.invoice.void", "refundreceipt.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

TIME_ACTIVITY_CREATE = CapabilitySchema(
    capability_key="timeactivity.create",
    service="quickbooks",
    category="sales",
    description="Create a time activity in QuickBooks",
    description_detailed=(
        "Records time worked by an employee or vendor. Can be marked billable "
        "and linked to a customer for invoicing."
    ),
    parameters={
        "hours": ParameterSchema(
            type="integer",
            required=True,
            description="Hours worked",
        ),
        "minutes": ParameterSchema(
            type="integer",
            required=False,
            description="Minutes worked",
            default=0,
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Date",
        ),
        "employee_id": ParameterSchema(
            type="string",
            required=False,
            description="Employee",
        ),
        "customer_id": ParameterSchema(
            type="string",
            required=False,
            description="Customer",
        ),
        "item_id": ParameterSchema(
            type="string",
            required=False,
            description="Service item",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Work done",
        ),
        "billable": ParameterSchema(
            type="boolean",
            required=False,
            description="Is billable",
        ),
    },
    returns={
        "time_activity_id": ReturnFieldSchema(type="string", description="Activity ID"),
        "hours": ReturnFieldSchema(type="integer", description="Hours"),
        "minutes": ReturnFieldSchema(type="integer", description="Minutes"),
        "txn_date": ReturnFieldSchema(type="string", description="Date"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

REFUND_RECEIPT_CREATE = CapabilitySchema(
    capability_key="refundreceipt.create",
    service="quickbooks",
    category="sales",
    description="Create a refund receipt",
    description_detailed=(
        "Creates a refund receipt to record money returned to a customer. "
        "Typically used after a sales receipt for returns."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=False,
            description="Items refunded",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Refund date",
        ),
        "deposit_account_id": ParameterSchema(
            type="string",
            required=False,
            description="Account refund comes from",
        ),
        "payment_method_id": ParameterSchema(
            type="string",
            required=False,
            description="Payment method reference ID",
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="Private note",
        ),
    },
    returns={
        "refund_receipt_id": ReturnFieldSchema(type="string", description="Refund ID"),
        "customer_id": ReturnFieldSchema(type="string", description="Customer"),
        "total_amount": ReturnFieldSchema(type="number", description="Refund amount"),
        "txn_date": ReturnFieldSchema(type="string", description="Date"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this refund receipt in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/refundreceipt?txnId=400",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

SALES_SCHEMAS: dict[str, CapabilitySchema] = {
    "estimate.create": ESTIMATE_CREATE,
    "estimate.get": ESTIMATE_GET,
    "salesreceipt.create": SALES_RECEIPT_CREATE,
    "creditmemo.create": CREDIT_MEMO_CREATE,
    "timeactivity.create": TIME_ACTIVITY_CREATE,
    "refundreceipt.create": REFUND_RECEIPT_CREATE,
}
