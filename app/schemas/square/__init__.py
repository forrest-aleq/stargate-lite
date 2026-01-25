"""
Square Capability Schemas.

Rich metadata for Square payments and commerce operations.
Finance teams use Square for payment processing, invoicing, and POS reconciliation.

API Docs: https://developer.squareup.com/reference/square
"""

from app.schemas.base import CapabilitySchema
from app.schemas.square.customers import CUSTOMER_SCHEMAS
from app.schemas.square.invoices import INVOICE_SCHEMAS
from app.schemas.square.locations import LOCATION_SCHEMAS
from app.schemas.square.orders import ORDER_SCHEMAS
from app.schemas.square.payments import PAYMENT_SCHEMAS
from app.schemas.square.payouts import PAYOUT_SCHEMAS

# Export all schemas
SQUARE_SCHEMAS: dict[str, CapabilitySchema] = {
    **LOCATION_SCHEMAS,
    **PAYMENT_SCHEMAS,
    **ORDER_SCHEMAS,
    **CUSTOMER_SCHEMAS,
    **INVOICE_SCHEMAS,
    **PAYOUT_SCHEMAS,
}

__all__ = ["SQUARE_SCHEMAS"]
