"""
Stripe Tax Capability Schemas.

Rich metadata for tax calculation and compliance.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ TAX CALCULATIONS ============

TAX_CALCULATION_CREATE = CapabilitySchema(
    capability_key="stripe.tax.calculation.create",
    service="stripe",
    category="tax",
    description="Create a tax calculation",
    description_detailed=(
        "Calculates tax for a transaction. Returns the tax amounts that should "
        "be collected based on the customer's location and the items being sold."
    ),
    parameters={
        "currency": ParameterSchema(
            type="string",
            required=True,
            description="Three-letter ISO currency code",
            example="usd",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Items to calculate tax for",
            items_type="object",
            example=[{"amount": 1000, "reference": "L1"}],
        ),
        "customer_details": ParameterSchema(
            type="object",
            required=True,
            description="Customer location info",
            example={
                "address": {
                    "line1": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "postal_code": "94102",
                    "country": "US",
                },
                "address_source": "billing",
            },
        ),
        "shipping_cost": ParameterSchema(
            type="object",
            required=False,
            description="Shipping cost details",
        ),
        "tax_date": ParameterSchema(
            type="integer",
            required=False,
            description="Unix timestamp for tax rates",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Calculation ID"),
        "amount_total": ReturnFieldSchema(type="integer", description="Total amount"),
        "tax_amount_exclusive": ReturnFieldSchema(type="integer", description="Excl. tax"),
        "tax_amount_inclusive": ReturnFieldSchema(type="integer", description="Incl. tax"),
        "line_items": ReturnFieldSchema(type="object", description="Calculated items"),
        "shipping_cost": ReturnFieldSchema(type="object", description="Shipping tax"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid address or tax not configured",
            recovery_hint="Check address is complete and Tax is enabled",
        ),
    ],
    idempotent=False,
    has_side_effects=False,
)

TAX_CALCULATION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.tax.calculation.retrieve",
    service="stripe",
    category="tax",
    description="Retrieve a tax calculation",
    parameters={
        "calculation_id": ParameterSchema(
            type="string",
            required=True,
            description="Tax calculation ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Calculation ID"),
        "amount_total": ReturnFieldSchema(type="integer", description="Total"),
        "tax_amount_exclusive": ReturnFieldSchema(type="integer", description="Tax"),
        "line_items": ReturnFieldSchema(type="object", description="Items"),
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

TAX_CALCULATION_LINE_ITEMS_LIST = CapabilitySchema(
    capability_key="stripe.tax.calculation.line_items.list",
    service="stripe",
    category="tax",
    description="List line items for a tax calculation",
    parameters={
        "calculation_id": ParameterSchema(
            type="string",
            required=True,
            description="Tax calculation ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="Line items"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results"),
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

# ============ TAX TRANSACTIONS ============

TAX_TRANSACTION_CREATE_FROM_CALC = CapabilitySchema(
    capability_key="stripe.tax.transaction.create_from_calculation",
    service="stripe",
    category="tax",
    description="Create a tax transaction from a calculation",
    description_detailed=(
        "Creates a tax transaction from an existing calculation. Use this "
        "to record the tax collected when completing a payment."
    ),
    parameters={
        "calculation": ParameterSchema(
            type="string",
            required=True,
            description="Tax calculation ID",
        ),
        "reference": ParameterSchema(
            type="string",
            required=True,
            description="Your reference for this transaction",
            example="order_12345",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Transaction ID"),
        "reference": ReturnFieldSchema(type="string", description="Reference"),
        "type": ReturnFieldSchema(type="string", description="Transaction type"),
        "tax_date": ReturnFieldSchema(type="integer", description="Tax date"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Calculation already used or expired",
            recovery_hint="Create a new calculation",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.tax.calculation.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

TAX_TRANSACTION_CREATE_REVERSAL = CapabilitySchema(
    capability_key="stripe.tax.transaction.create_reversal",
    service="stripe",
    category="tax",
    description="Create a tax transaction reversal",
    description_detailed=(
        "Creates a reversal for a tax transaction. Use when refunding "
        "a payment to properly account for the tax reversal."
    ),
    parameters={
        "mode": ParameterSchema(
            type="string",
            required=True,
            description="Reversal mode",
            enum=["full", "partial"],
        ),
        "original_transaction": ParameterSchema(
            type="string",
            required=True,
            description="Original transaction ID to reverse",
        ),
        "reference": ParameterSchema(
            type="string",
            required=True,
            description="Your reference for this reversal",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=False,
            description="Line items to reverse (for partial)",
        ),
        "flat_amount": ParameterSchema(
            type="integer",
            required=False,
            description="Flat amount to reverse",
        ),
        "shipping_cost": ParameterSchema(
            type="object",
            required=False,
            description="Shipping cost to reverse",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Reversal transaction ID"),
        "type": ReturnFieldSchema(type="string", description="Should be reversal"),
        "original_transaction": ReturnFieldSchema(type="string", description="Original"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid amount or already fully reversed",
            recovery_hint="Check original transaction balance",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

TAX_TRANSACTION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.tax.transaction.retrieve",
    service="stripe",
    category="tax",
    description="Retrieve a tax transaction",
    parameters={
        "transaction_id": ParameterSchema(
            type="string",
            required=True,
            description="Tax transaction ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Transaction ID"),
        "type": ReturnFieldSchema(type="string", description="Type"),
        "reference": ReturnFieldSchema(type="string", description="Reference"),
        "tax_date": ReturnFieldSchema(type="integer", description="Tax date"),
        "line_items": ReturnFieldSchema(type="object", description="Line items"),
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

TAX_TRANSACTION_LINE_ITEMS_LIST = CapabilitySchema(
    capability_key="stripe.tax.transaction.line_items.list",
    service="stripe",
    category="tax",
    description="List line items for a tax transaction",
    parameters={
        "transaction_id": ParameterSchema(
            type="string",
            required=True,
            description="Tax transaction ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="Line items"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results"),
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

TAX_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.tax.calculation.create": TAX_CALCULATION_CREATE,
    "stripe.tax.calculation.retrieve": TAX_CALCULATION_RETRIEVE,
    "stripe.tax.calculation.line_items.list": TAX_CALCULATION_LINE_ITEMS_LIST,
    "stripe.tax.transaction.create_from_calculation": TAX_TRANSACTION_CREATE_FROM_CALC,
    "stripe.tax.transaction.create_reversal": TAX_TRANSACTION_CREATE_REVERSAL,
    "stripe.tax.transaction.retrieve": TAX_TRANSACTION_RETRIEVE,
    "stripe.tax.transaction.line_items.list": TAX_TRANSACTION_LINE_ITEMS_LIST,
}
