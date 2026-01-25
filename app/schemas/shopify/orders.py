"""Shopify Order Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

SHOPIFY_ORDERS_LIST = CapabilitySchema(
    capability_key="shopify.orders.list",
    service="shopify",
    category="orders",
    description="List orders from Shopify",
    parameters={
        "status": ParameterSchema(
            type="string",
            required=False,
            enum=["open", "closed", "cancelled", "any"],
            description="Order status filter",
        ),
        "financial_status": ParameterSchema(
            type="string",
            required=False,
            enum=["pending", "authorized", "paid", "refunded", "voided"],
            description="Financial status filter",
        ),
        "fulfillment_status": ParameterSchema(
            type="string",
            required=False,
            enum=["shipped", "partial", "unshipped", "unfulfilled"],
            description="Fulfillment status filter",
        ),
        "created_at_min": ParameterSchema(
            type="string", required=False, description="Filter orders created after this date"
        ),
        "created_at_max": ParameterSchema(
            type="string", required=False, description="Filter orders created before this date"
        ),
        "limit": ParameterSchema(type="integer", required=False, description="Max 250"),
    },
    returns={
        "orders": ReturnFieldSchema(
            type="array",
            description="Orders with id, name, total_price, financial_status, line_items",
        ),
        "count": ReturnFieldSchema(type="integer", description="Order count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["shopify.orders.get", "shopify.transactions.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SHOPIFY_ORDER_GET = CapabilitySchema(
    capability_key="shopify.order.get",
    service="shopify",
    category="orders",
    description="Get order details from Shopify",
    parameters={
        "order_id": ParameterSchema(type="string", required=True, description="Shopify order ID"),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Order ID"),
        "name": ReturnFieldSchema(type="string", description="Order number (#1001)"),
        "email": ReturnFieldSchema(type="string", description="Customer email"),
        "created_at": ReturnFieldSchema(type="string", description="Created timestamp"),
        "total_price": ReturnFieldSchema(type="string", description="Total price"),
        "subtotal_price": ReturnFieldSchema(type="string", description="Subtotal"),
        "total_tax": ReturnFieldSchema(type="string", description="Tax amount"),
        "total_discounts": ReturnFieldSchema(type="string", description="Discounts"),
        "financial_status": ReturnFieldSchema(type="string", description="Payment status"),
        "fulfillment_status": ReturnFieldSchema(type="string", description="Fulfillment"),
        "line_items": ReturnFieldSchema(type="array", description="Order items"),
        "shipping_lines": ReturnFieldSchema(type="array", description="Shipping"),
        "refunds": ReturnFieldSchema(type="array", description="Any refunds"),
    },
    idempotent=True,
    has_side_effects=False,
)

SHOPIFY_ORDERS_COUNT = CapabilitySchema(
    capability_key="shopify.orders.count",
    service="shopify",
    category="orders",
    description="Get order count from Shopify",
    parameters={
        "status": ParameterSchema(type="string", required=False, description="Order status filter"),
        "financial_status": ParameterSchema(
            type="string", required=False, description="Financial status filter"
        ),
        "created_at_min": ParameterSchema(
            type="string", required=False, description="Filter orders created after this date"
        ),
        "created_at_max": ParameterSchema(
            type="string", required=False, description="Filter orders created before this date"
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Order count"),
    },
    idempotent=True,
    has_side_effects=False,
)

SHOPIFY_ORDER_CREATE = CapabilitySchema(
    capability_key="shopify.order.create",
    service="shopify",
    category="orders",
    description="Create an order in Shopify",
    parameters={
        "line_items": ParameterSchema(
            type="array", required=True, description="Order line items with title, price, quantity"
        ),
        "customer": ParameterSchema(
            type="object", required=False, description="Customer info (id or email)"
        ),
        "billing_address": ParameterSchema(
            type="object", required=False, description="Billing address"
        ),
        "shipping_address": ParameterSchema(
            type="object", required=False, description="Shipping address"
        ),
        "financial_status": ParameterSchema(
            type="string",
            required=False,
            enum=["pending", "authorized", "paid"],
            description="Payment status",
        ),
        "send_receipt": ParameterSchema(
            type="boolean", required=False, description="Send receipt email to customer"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Created order ID"),
        "name": ReturnFieldSchema(type="string", description="Order number"),
        "total_price": ReturnFieldSchema(type="string", description="Total price"),
    },
    idempotent=False,
    has_side_effects=True,
)

SHOPIFY_ORDER_UPDATE = CapabilitySchema(
    capability_key="shopify.order.update",
    service="shopify",
    category="orders",
    description="Update an order in Shopify",
    parameters={
        "order_id": ParameterSchema(type="string", required=True, description="Shopify order ID"),
        "note": ParameterSchema(type="string", required=False, description="Order note"),
        "tags": ParameterSchema(type="string", required=False, description="Comma-separated tags"),
        "email": ParameterSchema(type="string", required=False, description="Customer email"),
        "shipping_address": ParameterSchema(
            type="object", required=False, description="Updated shipping address"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Order ID"),
        "updated_at": ReturnFieldSchema(type="string", description="Update timestamp"),
    },
    idempotent=True,
    has_side_effects=True,
)

SHOPIFY_ORDER_CANCEL = CapabilitySchema(
    capability_key="shopify.order.cancel",
    service="shopify",
    category="orders",
    description="Cancel an order in Shopify",
    parameters={
        "order_id": ParameterSchema(type="string", required=True, description="Shopify order ID"),
        "reason": ParameterSchema(
            type="string",
            required=False,
            enum=["customer", "fraud", "inventory", "declined", "other"],
            description="Cancellation reason",
        ),
        "restock": ParameterSchema(type="boolean", required=False, description="Restock inventory"),
        "email": ParameterSchema(
            type="boolean", required=False, description="Send cancellation email to customer"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Order ID"),
        "cancelled_at": ReturnFieldSchema(type="string", description="Cancellation timestamp"),
    },
    idempotent=True,
    has_side_effects=True,
)

ORDER_SCHEMAS = {
    "shopify.orders.list": SHOPIFY_ORDERS_LIST,
    "shopify.order.get": SHOPIFY_ORDER_GET,
    "shopify.orders.count": SHOPIFY_ORDERS_COUNT,
    "shopify.order.create": SHOPIFY_ORDER_CREATE,
    "shopify.order.update": SHOPIFY_ORDER_UPDATE,
    "shopify.order.cancel": SHOPIFY_ORDER_CANCEL,
}
