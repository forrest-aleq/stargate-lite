"""Shopify Fulfillment Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

SHOPIFY_FULFILLMENT_CREATE = CapabilitySchema(
    capability_key="shopify.fulfillment.create",
    service="shopify",
    category="fulfillment",
    description="Create a fulfillment for an order",
    parameters={
        "line_items_by_fulfillment_order": ParameterSchema(
            type="array",
            required=True,
            description="Fulfillment order IDs and line items to fulfill",
        ),
        "tracking_info": ParameterSchema(
            type="object", required=False, description="Tracking number and URL"
        ),
        "notify_customer": ParameterSchema(
            type="boolean", required=False, description="Send shipment notification to customer"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Fulfillment ID"),
        "order_id": ReturnFieldSchema(type="string", description="Order ID"),
        "status": ReturnFieldSchema(type="string", description="Fulfillment status"),
        "tracking_number": ReturnFieldSchema(type="string", description="Tracking number"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["shopify.orders.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)

FULFILLMENT_SCHEMAS = {
    "shopify.fulfillment.create": SHOPIFY_FULFILLMENT_CREATE,
}
