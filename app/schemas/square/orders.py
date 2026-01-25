"""Square Order Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
)

SQUARE_ORDERS_LIST = CapabilitySchema(
    capability_key="square.orders.list",
    service="square",
    category="orders",
    description="Search/list orders from Square",
    parameters={
        "location_ids": ParameterSchema(
            type="array", required=True, description="Location IDs to search"
        ),
        "query": ParameterSchema(type="object", required=False, description="Search query filters"),
        "limit": ParameterSchema(
            type="integer", required=False, description="Maximum orders to return"
        ),
        "cursor": ParameterSchema(type="string", required=False, description="Pagination cursor"),
    },
    returns={
        "orders": ReturnFieldSchema(
            type="array",
            description="Orders with id, location_id, line_items, total_money, state",
        ),
        "cursor": ReturnFieldSchema(type="string", description="Pagination cursor"),
    },
    idempotent=True,
    has_side_effects=False,
)

SQUARE_ORDERS_GET = CapabilitySchema(
    capability_key="square.orders.get",
    service="square",
    category="orders",
    description="Get order details from Square",
    parameters={
        "order_id": ParameterSchema(type="string", required=True, description="Square order ID"),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Order ID"),
        "location_id": ReturnFieldSchema(type="string", description="Location"),
        "line_items": ReturnFieldSchema(type="array", description="Order items"),
        "total_money": ReturnFieldSchema(type="object", description="Total"),
        "total_tax_money": ReturnFieldSchema(type="object", description="Tax"),
        "total_discount_money": ReturnFieldSchema(type="object", description="Discounts"),
        "state": ReturnFieldSchema(type="string", description="OPEN, COMPLETED, etc."),
        "tenders": ReturnFieldSchema(type="array", description="Payment tenders"),
        "refunds": ReturnFieldSchema(type="array", description="Refunds"),
    },
    idempotent=True,
    has_side_effects=False,
)

SQUARE_ORDERS_CREATE = CapabilitySchema(
    capability_key="square.orders.create",
    service="square",
    category="orders",
    description="Create an order in Square",
    parameters={
        "idempotency_key": ParameterSchema(
            type="string", required=True, description="Unique key for idempotency"
        ),
        "location_id": ParameterSchema(
            type="string", required=True, description="Location ID for the order"
        ),
        "line_items": ParameterSchema(type="array", required=False, description="Order line items"),
        "reference_id": ParameterSchema(
            type="string", required=False, description="External reference ID"
        ),
    },
    returns={
        "order_id": ReturnFieldSchema(type="string", description="Created order ID"),
        "state": ReturnFieldSchema(type="string", description="Order state"),
    },
    idempotent=True,
    has_side_effects=True,
)

SQUARE_ORDERS_UPDATE = CapabilitySchema(
    capability_key="square.orders.update",
    service="square",
    category="orders",
    description="Update an order in Square",
    parameters={
        "order_id": ParameterSchema(type="string", required=True, description="Square order ID"),
        "fields_to_clear": ParameterSchema(
            type="array", required=False, description="Fields to clear from the order"
        ),
        "order": ParameterSchema(
            type="object", required=False, description="Order fields to update"
        ),
        "idempotency_key": ParameterSchema(
            type="string", required=False, description="Unique key for idempotency"
        ),
    },
    returns={
        "order_id": ReturnFieldSchema(type="string", description="Updated order ID"),
        "version": ReturnFieldSchema(type="integer", description="New order version"),
    },
    idempotent=True,
    has_side_effects=True,
)

ORDER_SCHEMAS = {
    "square.orders.list": SQUARE_ORDERS_LIST,
    "square.orders.get": SQUARE_ORDERS_GET,
    "square.orders.create": SQUARE_ORDERS_CREATE,
    "square.orders.update": SQUARE_ORDERS_UPDATE,
}
