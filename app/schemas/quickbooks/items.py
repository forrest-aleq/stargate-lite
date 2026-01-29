"""
QuickBooks Item Capability Schemas.

Rich metadata for item (product/service) operations.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

ITEM_CREATE = CapabilitySchema(
    capability_key="item.create",
    service="quickbooks",
    category="items",
    description="Create an item/product in QuickBooks",
    description_detailed=(
        "Creates a new item (product or service) that can be used on invoices and sales. "
        "Items can be Services, Inventory, or NonInventory types."
    ),
    parameters={
        "item_name": ParameterSchema(
            type="string",
            required=True,
            description="Item name (must be unique)",
            example="Consulting Services",
        ),
        "item_type": ParameterSchema(
            type="string",
            required=False,
            description="Type of item",
            default="Service",
            enum=["Service", "Inventory", "NonInventory"],
        ),
        "unit_price": ParameterSchema(
            type="number",
            required=False,
            description="Default unit price",
            example=150.00,
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Item description",
        ),
        "income_account_id": ParameterSchema(
            type="string",
            required=False,
            description="Income account for sales",
        ),
        "expense_account_id": ParameterSchema(
            type="string",
            required=False,
            description="Expense account for purchases",
        ),
    },
    returns={
        "item_id": ReturnFieldSchema(type="string", description="Item ID"),
        "name": ReturnFieldSchema(type="string", description="Item name"),
        "type": ReturnFieldSchema(type="string", description="Item type"),
        "unit_price": ReturnFieldSchema(type="number", description="Unit price"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this item in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/item?itemId=1",
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
            description="Duplicate item name",
            recovery_hint="Use item.list to check existing items",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["qb.invoice.create", "estimate.create"],
        related_capabilities=["item.list", "item.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)

ITEM_GET = CapabilitySchema(
    capability_key="item.get",
    service="quickbooks",
    category="items",
    description="Get item details from QuickBooks",
    parameters={
        "item_id": ParameterSchema(
            type="string",
            required=True,
            description="Item ID with 'qb:' prefix",
        ),
    },
    returns={
        "item_id": ReturnFieldSchema(type="string", description="Item ID"),
        "name": ReturnFieldSchema(type="string", description="Item name"),
        "type": ReturnFieldSchema(type="string", description="Item type"),
        "unit_price": ReturnFieldSchema(type="number", description="Unit price"),
        "description": ReturnFieldSchema(type="string", description="Description"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this item in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/item?itemId=1",
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

ITEM_LIST = CapabilitySchema(
    capability_key="item.list",
    service="quickbooks",
    category="items",
    description="List items from QuickBooks",
    parameters={
        "item_type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by item type",
            enum=["Service", "Inventory", "NonInventory"],
        ),
        "active_only": ParameterSchema(
            type="boolean",
            required=False,
            description="Only return active items",
            default=False,
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results to return",
            default=100,
        ),
    },
    returns={
        "items": ReturnFieldSchema(
            type="array",
            description="List of item objects (each includes deep_link URL to QBO)",
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
        typically_followed_by=["qb.invoice.create", "estimate.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

ITEM_SCHEMAS: dict[str, CapabilitySchema] = {
    "item.create": ITEM_CREATE,
    "item.get": ITEM_GET,
    "item.list": ITEM_LIST,
}
