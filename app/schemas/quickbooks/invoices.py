"""
QuickBooks Invoice Capability Schemas.

Rich metadata for invoice operations.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    UsageExample,
    WorkflowHints,
)

INVOICE_CREATE = CapabilitySchema(
    capability_key="qb.invoice.create",
    service="quickbooks",
    category="invoices",
    description="Create an invoice in QuickBooks",
    description_detailed=(
        "Creates a new invoice (accounts receivable) for a customer. An invoice represents "
        "money owed to you for goods or services. Requires a valid customer_id and line items. "
        "The invoice can be sent via email using invoice.send after creation."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="QuickBooks customer ID (with 'qb:' prefix)",
            example="qb:123",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Array of line items with Amount, Description, and detail type",
            items_type="object",
            example=[
                {
                    "Amount": 100.00,
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "ItemRef": {"value": "1"},
                        "Qty": 1,
                        "UnitPrice": 100.00,
                    },
                }
            ],
        ),
        "due_date": ParameterSchema(
            type="string",
            required=False,
            description="Payment due date (YYYY-MM-DD)",
            example="2026-02-15",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Invoice date (defaults to today)",
            example="2026-01-15",
        ),
        "customer_memo": ParameterSchema(
            type="string",
            required=False,
            description="Message displayed on invoice to customer",
        ),
    },
    returns={
        "invoice_id": ReturnFieldSchema(
            type="string",
            description="QuickBooks invoice ID with 'qb:' prefix",
            example="qb:789",
        ),
        "doc_number": ReturnFieldSchema(
            type="string",
            description="Invoice number",
            example="1001",
        ),
        "total_amount": ReturnFieldSchema(
            type="number",
            description="Total invoice amount",
            example=100.00,
        ),
        "balance": ReturnFieldSchema(
            type="number",
            description="Outstanding balance",
            example=100.00,
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Invoice status",
            example="pending",
        ),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this invoice in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/invoice?txnId=789",
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
            description="Invalid customer_id or line items",
            recovery_hint="Verify customer exists with qb.customer.get",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.customer.search", "qb.customer.create", "item.list"],
        typically_followed_by=["qb.invoice.send", "qb.invoice.get"],
        related_capabilities=["qb.invoice.list", "qb.payment.create"],
    ),
    examples=[
        UsageExample(
            description="Create an invoice for consulting services",
            args={
                "customer_id": "qb:123",
                "line_items": [
                    {
                        "Amount": 500.00,
                        "DetailType": "SalesItemLineDetail",
                        "Description": "Consulting services - January 2026",
                        "SalesItemLineDetail": {
                            "ItemRef": {"value": "1"},
                            "Qty": 5,
                            "UnitPrice": 100,
                        },
                    }
                ],
                "due_date": "2026-02-15",
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

INVOICE_GET = CapabilitySchema(
    capability_key="qb.invoice.get",
    service="quickbooks",
    category="invoices",
    description="Get invoice details from QuickBooks",
    description_detailed=(
        "Retrieves complete invoice details including line items, balance, and email status. "
        "Use to check payment status or get invoice details before sending."
    ),
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID with 'qb:' prefix",
            example="qb:789",
        ),
    },
    returns={
        "invoice_id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "doc_number": ReturnFieldSchema(type="string", description="Invoice number"),
        "customer_id": ReturnFieldSchema(type="string", description="Customer ID"),
        "total_amount": ReturnFieldSchema(type="number", description="Total amount"),
        "balance": ReturnFieldSchema(type="number", description="Outstanding balance"),
        "due_date": ReturnFieldSchema(type="string", description="Due date"),
        "email_status": ReturnFieldSchema(type="string", description="Email delivery status"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this invoice in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/invoice?txnId=789",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Invoice not found",
            recovery_hint="Verify invoice_id with invoice.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.invoice.create", "qb.invoice.list"],
        typically_followed_by=["qb.invoice.send", "qb.payment.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

INVOICE_SEND = CapabilitySchema(
    capability_key="qb.invoice.send",
    service="quickbooks",
    category="invoices",
    description="Send invoice via email through QuickBooks",
    description_detailed=(
        "Sends an invoice to the customer via email using QuickBooks' email service. "
        "The email will be sent from your QuickBooks account and include a link for "
        "online payment."
    ),
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID to send",
            example="qb:789",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Override email address (uses customer's email if not provided)",
            example="billing@customer.com",
        ),
    },
    returns={
        "invoice_id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "email_sent": ReturnFieldSchema(type="boolean", description="True if sent"),
        "sent_to": ReturnFieldSchema(type="string", description="Recipient email"),
        "email_status": ReturnFieldSchema(type="string", description="Delivery status"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this invoice in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/invoice?txnId=789",
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
            description="No email address available",
            recovery_hint="Provide email parameter or update customer email",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.invoice.create", "qb.invoice.get"],
        typically_followed_by=["qb.invoice.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)

INVOICE_VOID = CapabilitySchema(
    capability_key="qb.invoice.void",
    service="quickbooks",
    category="invoices",
    description="Void an invoice in QuickBooks",
    description_detailed=(
        "Voids an existing invoice, setting its balance to zero. Use this instead of "
        "deleting to maintain audit trail. Cannot void invoices with payments applied."
    ),
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID to void",
            example="qb:789",
        ),
        "void_reason": ParameterSchema(
            type="string",
            required=False,
            description="Reason for voiding (stored in private note)",
            default="Voided via API",
        ),
    },
    returns={
        "invoice_id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "voided": ReturnFieldSchema(type="boolean", description="True if voided"),
        "balance": ReturnFieldSchema(type="number", description="Balance (should be 0)"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this invoice in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/invoice?txnId=789",
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
            description="Cannot void invoice with payments",
            recovery_hint="Delete associated payments first",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.invoice.get"],
        related_capabilities=["creditmemo.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

INVOICE_LIST = CapabilitySchema(
    capability_key="qb.invoice.list",
    service="quickbooks",
    category="invoices",
    description="List invoices from QuickBooks",
    description_detailed=(
        "Returns a list of invoices with optional filtering by customer or payment status. "
        "For outstanding invoices specifically, use qb.invoice.list_outstanding."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer ID",
        ),
        "unpaid_only": ParameterSchema(
            type="boolean",
            required=False,
            description="Only return invoices with balance > 0",
            default=False,
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results",
            default=100,
        ),
    },
    returns={
        "invoices": ReturnFieldSchema(
            type="array",
            description="List of invoice objects (each includes deep_link URL to QBO)",
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
    workflow=WorkflowHints(
        typically_followed_by=["qb.invoice.get", "qb.payment.create"],
        related_capabilities=["qb.invoice.list_outstanding"],
    ),
    idempotent=True,
    has_side_effects=False,
)

INVOICE_LIST_OUTSTANDING = CapabilitySchema(
    capability_key="qb.invoice.list_outstanding",
    service="quickbooks",
    category="invoices",
    description="List outstanding invoices (Balance > 0) - CRITICAL for payment allocation",
    description_detailed=(
        "Returns only invoices with outstanding balances. Essential for MARS payment "
        "allocation workflows - identifies which invoices need payment."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results",
            default=100,
        ),
    },
    returns={
        "invoices": ReturnFieldSchema(
            type="array",
            description="Outstanding invoice objects (each includes deep_link URL to QBO)",
        ),
        "total_outstanding": ReturnFieldSchema(
            type="number",
            description="Sum of all outstanding balances",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of invoices"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["payment.apply_to_invoice", "qb.payment.create"],
        related_capabilities=["qb.invoice.list", "report.ar_aging"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# Invoice aliases for MARS compatibility
INVOICE_CREATE_ALIAS = CapabilitySchema(
    capability_key="invoice.create",
    service="quickbooks",
    category="invoices",
    description="Create an invoice in QuickBooks (MARS alias)",
    description_detailed=INVOICE_CREATE.description_detailed,
    parameters=INVOICE_CREATE.parameters,
    returns=INVOICE_CREATE.returns,
    errors=INVOICE_CREATE.errors,
    workflow=INVOICE_CREATE.workflow,
    idempotent=False,
    has_side_effects=True,
)

INVOICE_GET_ALIAS = CapabilitySchema(
    capability_key="invoice.get",
    service="quickbooks",
    category="invoices",
    description="Get invoice details (MARS alias)",
    description_detailed=INVOICE_GET.description_detailed,
    parameters=INVOICE_GET.parameters,
    returns=INVOICE_GET.returns,
    errors=INVOICE_GET.errors,
    workflow=INVOICE_GET.workflow,
    idempotent=True,
    has_side_effects=False,
)

INVOICE_SEND_ALIAS = CapabilitySchema(
    capability_key="invoice.send",
    service="quickbooks",
    category="invoices",
    description="Send invoice via email (MARS alias)",
    description_detailed=INVOICE_SEND.description_detailed,
    parameters=INVOICE_SEND.parameters,
    returns=INVOICE_SEND.returns,
    errors=INVOICE_SEND.errors,
    workflow=INVOICE_SEND.workflow,
    idempotent=False,
    has_side_effects=True,
)

INVOICE_VOID_ALIAS = CapabilitySchema(
    capability_key="invoice.void",
    service="quickbooks",
    category="invoices",
    description="Void an invoice (MARS alias)",
    description_detailed=INVOICE_VOID.description_detailed,
    parameters=INVOICE_VOID.parameters,
    returns=INVOICE_VOID.returns,
    errors=INVOICE_VOID.errors,
    workflow=INVOICE_VOID.workflow,
    idempotent=False,
    has_side_effects=True,
)

INVOICE_LIST_ALIAS = CapabilitySchema(
    capability_key="invoice.list",
    service="quickbooks",
    category="invoices",
    description="List invoices (MARS alias)",
    description_detailed=INVOICE_LIST.description_detailed,
    parameters=INVOICE_LIST.parameters,
    returns=INVOICE_LIST.returns,
    errors=INVOICE_LIST.errors,
    workflow=INVOICE_LIST.workflow,
    idempotent=True,
    has_side_effects=False,
)

INVOICE_SCHEMAS: dict[str, CapabilitySchema] = {
    "qb.invoice.create": INVOICE_CREATE,
    "qb.invoice.get": INVOICE_GET,
    "qb.invoice.send": INVOICE_SEND,
    "qb.invoice.void": INVOICE_VOID,
    "qb.invoice.list": INVOICE_LIST,
    "qb.invoice.list_outstanding": INVOICE_LIST_OUTSTANDING,
    "invoice.create": INVOICE_CREATE_ALIAS,
    "invoice.get": INVOICE_GET_ALIAS,
    "invoice.send": INVOICE_SEND_ALIAS,
    "invoice.void": INVOICE_VOID_ALIAS,
    "invoice.list": INVOICE_LIST_ALIAS,
}
