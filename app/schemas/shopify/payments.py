"""Shopify Payment Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

SHOPIFY_TRANSACTIONS_LIST = CapabilitySchema(
    capability_key="shopify.transactions.list",
    service="shopify",
    category="payments",
    description="List transactions for an order",
    parameters={
        "order_id": ParameterSchema(type="string", required=True, description="Shopify order ID"),
    },
    returns={
        "transactions": ReturnFieldSchema(
            type="array",
            description="Transactions with id, kind, gateway, amount, status",
        ),
        "count": ReturnFieldSchema(type="integer", description="Transaction count"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["shopify.orders.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SHOPIFY_REFUNDS_CREATE = CapabilitySchema(
    capability_key="shopify.refunds.create",
    service="shopify",
    category="payments",
    description="Create a refund for an order",
    parameters={
        "order_id": ParameterSchema(type="string", required=True, description="Order ID to refund"),
        "notify": ParameterSchema(type="boolean", required=False, description="Email customer"),
        "note": ParameterSchema(type="string", required=False, description="Internal refund note"),
        "shipping": ParameterSchema(
            type="object", required=False, description="Shipping refund amount"
        ),
        "refund_line_items": ParameterSchema(
            type="array",
            required=False,
            description="Line items to refund with quantity and restock",
        ),
        "transactions": ParameterSchema(
            type="array", required=False, description="Payment transactions to refund"
        ),
    },
    returns={
        "refund_id": ReturnFieldSchema(type="string", description="Refund ID"),
        "total_refunded": ReturnFieldSchema(type="string", description="Amount refunded"),
        "status": ReturnFieldSchema(type="string", description="Refund status"),
    },
    idempotent=False,
    has_side_effects=True,
)

SHOPIFY_PAYOUTS_LIST = CapabilitySchema(
    capability_key="shopify.payouts.list",
    service="shopify",
    category="payments",
    description="List Shopify Payments payouts",
    description_detailed=(
        "Lists payouts from Shopify Payments to your bank account. Useful for reconciling deposits."
    ),
    parameters={
        "status": ParameterSchema(
            type="string",
            required=False,
            enum=["scheduled", "in_transit", "paid", "failed", "canceled"],
            description="Payout status filter",
        ),
        "date_min": ParameterSchema(
            type="string", required=False, description="Filter payouts after this date"
        ),
        "date_max": ParameterSchema(
            type="string", required=False, description="Filter payouts before this date"
        ),
    },
    returns={
        "payouts": ReturnFieldSchema(
            type="array", description="Payouts with id, date, amount, status"
        ),
        "count": ReturnFieldSchema(type="integer", description="Payout count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["shopify.balance_transactions.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SHOPIFY_BALANCE_TRANSACTIONS_LIST = CapabilitySchema(
    capability_key="shopify.balance_transactions.list",
    service="shopify",
    category="payments",
    description="List balance transactions for a payout",
    parameters={
        "payout_id": ParameterSchema(type="string", required=True, description="Shopify payout ID"),
    },
    returns={
        "transactions": ReturnFieldSchema(
            type="array", description="Transactions included in payout (charges, refunds, fees)"
        ),
        "count": ReturnFieldSchema(type="integer", description="Transaction count"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["shopify.payouts.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

PAYMENT_SCHEMAS = {
    "shopify.payouts.list": SHOPIFY_PAYOUTS_LIST,
}
