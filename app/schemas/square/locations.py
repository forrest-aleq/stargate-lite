"""Square Location Capability Schemas."""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ReturnFieldSchema,
    WorkflowHints,
)

SQUARE_LOCATIONS_LIST = CapabilitySchema(
    capability_key="square.locations.list",
    service="square",
    category="locations",
    description="List Square locations (stores)",
    parameters={},
    returns={
        "locations": ReturnFieldSchema(
            type="array",
            description="Locations with id, name, address, timezone, currency",
        ),
        "count": ReturnFieldSchema(type="integer", description="Location count"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Square OAuth not configured",
            recovery_hint="User must connect Square account",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["square.payments.list", "square.orders.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

LOCATION_SCHEMAS = {
    "square.locations.list": SQUARE_LOCATIONS_LIST,
}
