"""Square Payment Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

SQUARE_PAYMENTS_LIST = CapabilitySchema(
    capability_key="square.payments.list",
    service="square",
    category="payments",
    description="List payments from Square",
    parameters={
        "location_id": ParameterSchema(
            type="string", required=False, description="Filter by location ID"
        ),
        "begin_time": ParameterSchema(
            type="string", required=False, description="Filter payments after this time"
        ),
        "end_time": ParameterSchema(
            type="string", required=False, description="Filter payments before this time"
        ),
        "sort_order": ParameterSchema(
            type="string", required=False, enum=["ASC", "DESC"], description="Sort order"
        ),
        "cursor": ParameterSchema(
            type="string", required=False, description="Pagination cursor"
        ),
        "limit": ParameterSchema(
            type="integer", required=False, description="Maximum payments to return"
        ),
    },
    returns={
        "payments": ReturnFieldSchema(
            type="array",
            description="Payments with id, amount, status, source_type, created_at",
        ),
        "cursor": ReturnFieldSchema(type="string", description="Pagination cursor"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["square.locations.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SQUARE_PAYMENTS_GET = CapabilitySchema(
    capability_key="square.payments.get",
    service="square",
    category="payments",
    description="Get payment details from Square",
    parameters={
        "payment_id": ParameterSchema(
            type="string", required=True, description="Square payment ID"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Payment ID"),
        "amount_money": ReturnFieldSchema(type="object", description="Amount with currency"),
        "status": ReturnFieldSchema(type="string", description="COMPLETED, FAILED, etc."),
        "source_type": ReturnFieldSchema(type="string", description="CARD, CASH, etc."),
        "location_id": ReturnFieldSchema(type="string", description="Location ID"),
        "order_id": ReturnFieldSchema(type="string", description="Associated order"),
        "created_at": ReturnFieldSchema(type="string", description="Created timestamp"),
        "processing_fee": ReturnFieldSchema(type="array", description="Processing fees"),
        "card_details": ReturnFieldSchema(type="object", description="Card info if card"),
    },
    idempotent=True,
    has_side_effects=False,
)

SQUARE_PAYMENTS_CREATE = CapabilitySchema(
    capability_key="square.payments.create",
    service="square",
    category="payments",
    description="Create a payment in Square",
    parameters={
        "source_id": ParameterSchema(
            type="string",
            required=True,
            description="Payment source (card nonce, card on file, etc.)",
        ),
        "amount_money": ParameterSchema(
            type="object",
            required=True,
            description="Amount with currency {amount: cents, currency: 'USD'}",
        ),
        "idempotency_key": ParameterSchema(
            type="string", required=True, description="Unique key for idempotency"
        ),
        "location_id": ParameterSchema(
            type="string", required=False, description="Location ID"
        ),
        "customer_id": ParameterSchema(
            type="string", required=False, description="Customer ID to associate"
        ),
        "reference_id": ParameterSchema(
            type="string", required=False, description="External reference ID"
        ),
        "note": ParameterSchema(type="string", required=False, description="Payment note"),
    },
    returns={
        "payment_id": ReturnFieldSchema(type="string", description="Created payment ID"),
        "status": ReturnFieldSchema(type="string", description="Payment status"),
        "receipt_url": ReturnFieldSchema(type="string", description="Receipt URL"),
    },
    idempotent=True,
    has_side_effects=True,
)

SQUARE_PAYMENTS_REFUND = CapabilitySchema(
    capability_key="square.payments.refund",
    service="square",
    category="payments",
    description="Refund a Square payment",
    parameters={
        "payment_id": ParameterSchema(
            type="string", required=True, description="Payment ID to refund"
        ),
        "idempotency_key": ParameterSchema(
            type="string", required=True, description="Unique key for idempotency"
        ),
        "amount_money": ParameterSchema(
            type="object", required=True, description="Amount to refund"
        ),
        "reason": ParameterSchema(
            type="string", required=False, description="Reason for refund"
        ),
    },
    returns={
        "refund_id": ReturnFieldSchema(type="string", description="Refund ID"),
        "status": ReturnFieldSchema(type="string", description="PENDING, COMPLETED, etc."),
        "amount_money": ReturnFieldSchema(type="object", description="Refunded amount"),
    },
    idempotent=True,
    has_side_effects=True,
)

PAYMENT_SCHEMAS = {
    "square.payments.list": SQUARE_PAYMENTS_LIST,
    "square.payments.get": SQUARE_PAYMENTS_GET,
    "square.payments.create": SQUARE_PAYMENTS_CREATE,
    "square.payments.refund": SQUARE_PAYMENTS_REFUND,
}
