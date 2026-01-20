"""
Stripe Invoice Capability Schemas.

Rich metadata for invoice operations.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

INVOICE_CREATE = CapabilitySchema(
    capability_key="stripe.invoice.create",
    service="stripe",
    category="invoices",
    description="Create an invoice in Stripe",
    description_detailed=(
        "Creates a draft invoice for a customer. Invoices are automatically created "
        "for subscriptions, but you can also create one-off invoices manually."
    ),
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
            example="cus_ABC123",
        ),
        "auto_advance": ParameterSchema(
            type="boolean",
            required=False,
            description="Auto-finalize and send invoice",
            default=True,
        ),
        "collection_method": ParameterSchema(
            type="string",
            required=False,
            description="How to collect payment",
            enum=["charge_automatically", "send_invoice"],
            default="charge_automatically",
        ),
        "days_until_due": ParameterSchema(
            type="integer",
            required=False,
            description="Days until payment is due (if send_invoice)",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Invoice description",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your own use",
        ),
        "default_payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method for this invoice",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Invoice ID",
            example="in_ABC123",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Invoice status (draft, open, paid, etc.)",
        ),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
        "amount_due": ReturnFieldSchema(type="integer", description="Amount due in cents"),
        "currency": ReturnFieldSchema(type="string", description="Currency code"),
        "hosted_invoice_url": ReturnFieldSchema(type="string", description="Payment page URL"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.customer.create"],
        typically_followed_by=["stripe.invoice.finalize", "stripe.invoice.send"],
    ),
    idempotent=False,
    has_side_effects=True,
)

INVOICE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.invoice.retrieve",
    service="stripe",
    category="invoices",
    description="Retrieve an invoice in Stripe",
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "status": ReturnFieldSchema(type="string", description="Invoice status"),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
        "amount_due": ReturnFieldSchema(type="integer", description="Amount due"),
        "amount_paid": ReturnFieldSchema(type="integer", description="Amount paid"),
        "amount_remaining": ReturnFieldSchema(type="integer", description="Amount remaining"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "due_date": ReturnFieldSchema(type="integer", description="Due date timestamp"),
        "hosted_invoice_url": ReturnFieldSchema(type="string", description="Payment URL"),
        "invoice_pdf": ReturnFieldSchema(type="string", description="PDF download URL"),
        "lines": ReturnFieldSchema(type="object", description="Invoice line items"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

INVOICE_UPDATE = CapabilitySchema(
    capability_key="stripe.invoice.update",
    service="stripe",
    category="invoices",
    description="Update an invoice in Stripe",
    description_detailed="Updates a draft invoice. Cannot update finalized invoices.",
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID to update",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Update description",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Update metadata",
        ),
        "days_until_due": ParameterSchema(
            type="integer",
            required=False,
            description="Update days until due",
        ),
        "default_payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Update payment method",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Cannot update finalized invoice",
            recovery_hint="Only draft invoices can be updated",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

INVOICE_FINALIZE = CapabilitySchema(
    capability_key="stripe.invoice.finalize",
    service="stripe",
    category="invoices",
    description="Finalize an invoice in Stripe",
    description_detailed=(
        "Finalizes a draft invoice, transitioning it to 'open' status. "
        "Finalized invoices can no longer be edited and are ready for payment."
    ),
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID to finalize",
        ),
        "auto_advance": ParameterSchema(
            type="boolean",
            required=False,
            description="Auto-advance to next status",
            default=True,
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'open'"),
        "hosted_invoice_url": ReturnFieldSchema(type="string", description="Payment URL"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invoice already finalized or has no line items",
            recovery_hint="Check invoice status and ensure it has items",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.invoice.create"],
        typically_followed_by=["stripe.invoice.send", "stripe.invoice.pay"],
    ),
    idempotent=False,
    has_side_effects=True,
)

INVOICE_PAY = CapabilitySchema(
    capability_key="stripe.invoice.pay",
    service="stripe",
    category="invoices",
    description="Pay an invoice in Stripe",
    description_detailed=(
        "Attempts to pay an open invoice using the customer's default payment method "
        "or a specified payment method."
    ),
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID to pay",
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method to use (uses default if not specified)",
        ),
        "source": ParameterSchema(
            type="string",
            required=False,
            description="Card source to use (deprecated, use payment_method)",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'paid'"),
        "amount_paid": ReturnFieldSchema(type="integer", description="Amount paid"),
        "payment_intent": ReturnFieldSchema(type="string", description="PaymentIntent ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Payment failed or no payment method available",
            recovery_hint="Attach payment method to customer and retry",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.invoice.finalize"],
    ),
    idempotent=False,
    has_side_effects=True,
)

INVOICE_SEND = CapabilitySchema(
    capability_key="stripe.invoice.send",
    service="stripe",
    category="invoices",
    description="Send an invoice in Stripe",
    description_detailed=(
        "Sends an open invoice to the customer via email. The invoice must be "
        "finalized before it can be sent."
    ),
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID to send",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "hosted_invoice_url": ReturnFieldSchema(type="string", description="Payment URL"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invoice not finalized or no customer email",
            recovery_hint="Finalize invoice and ensure customer has email",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.invoice.finalize"],
    ),
    idempotent=False,
    has_side_effects=True,
)

INVOICE_VOID = CapabilitySchema(
    capability_key="stripe.invoice.void",
    service="stripe",
    category="invoices",
    description="Void an invoice in Stripe",
    description_detailed=(
        "Voids an open invoice. Voided invoices cannot be paid and are marked as void."
    ),
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID to void",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'void'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invoice already paid or voided",
            recovery_hint="Only open invoices can be voided",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

INVOICE_LIST = CapabilitySchema(
    capability_key="stripe.invoice.list",
    service="stripe",
    category="invoices",
    description="List invoices in Stripe",
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer ID",
        ),
        "subscription": ParameterSchema(
            type="string",
            required=False,
            description="Filter by subscription ID",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["draft", "open", "paid", "uncollectible", "void"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return (1-100)",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of invoices"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results available"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

INVOICE_DELETE = CapabilitySchema(
    capability_key="stripe.invoice.delete",
    service="stripe",
    category="invoices",
    description="Delete a draft invoice in Stripe",
    description_detailed="Permanently deletes a draft invoice. Only draft invoices can be deleted.",
    parameters={
        "invoice_id": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted invoice ID"),
        "deleted": ReturnFieldSchema(type="boolean", description="True if deleted"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Only draft invoices can be deleted",
            recovery_hint="Void the invoice instead if it's finalized",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

INVOICE_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.invoice.create": INVOICE_CREATE,
    "stripe.invoice.retrieve": INVOICE_RETRIEVE,
    "stripe.invoice.update": INVOICE_UPDATE,
    "stripe.invoice.finalize": INVOICE_FINALIZE,
    "stripe.invoice.pay": INVOICE_PAY,
    "stripe.invoice.send": INVOICE_SEND,
    "stripe.invoice.void": INVOICE_VOID,
    "stripe.invoice.list": INVOICE_LIST,
    "stripe.invoice.delete": INVOICE_DELETE,
}
