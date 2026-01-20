"""Square Payout Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
)

SQUARE_PAYOUTS_LIST = CapabilitySchema(
    capability_key="square.payouts.list",
    service="square",
    category="payouts",
    description="List payouts from Square",
    description_detailed="Lists payouts to your bank account. Use for reconciliation.",
    parameters={
        "location_id": ParameterSchema(
            type="string", required=False, description="Filter by location ID"
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            enum=["SENT", "FAILED", "PAID"],
            description="Payout status filter",
        ),
        "begin_time": ParameterSchema(
            type="string", required=False, description="Filter payouts after this time"
        ),
        "end_time": ParameterSchema(
            type="string", required=False, description="Filter payouts before this time"
        ),
        "cursor": ParameterSchema(
            type="string", required=False, description="Pagination cursor"
        ),
        "limit": ParameterSchema(
            type="integer", required=False, description="Maximum payouts to return"
        ),
    },
    returns={
        "payouts": ReturnFieldSchema(
            type="array",
            description="Payouts with id, status, amount, arrival_date",
        ),
        "cursor": ReturnFieldSchema(type="string", description="Pagination cursor"),
    },
    idempotent=True,
    has_side_effects=False,
)

PAYOUT_SCHEMAS = {
    "square.payouts.list": SQUARE_PAYOUTS_LIST,
}
