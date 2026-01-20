"""
NetSuite Capability Schemas.

Comprehensive schema definitions for NetSuite ERP operations.
Supports both TBA (OAuth 1.0) and OAuth 2.0 authentication.
"""

from app.schemas.base import CapabilitySchema

from .accounting import NETSUITE_ACCOUNTING_SCHEMAS
from .journals import NETSUITE_JOURNAL_SCHEMAS
from .payments import NETSUITE_PAYMENT_SCHEMAS
from .vendor_bills import NETSUITE_VENDORBILL_SCHEMAS
from .vendors import NETSUITE_VENDOR_SCHEMAS

# Aggregate all NetSuite schemas
NETSUITE_SCHEMAS: dict[str, CapabilitySchema] = {
    **NETSUITE_JOURNAL_SCHEMAS,
    **NETSUITE_VENDORBILL_SCHEMAS,
    **NETSUITE_VENDOR_SCHEMAS,
    **NETSUITE_PAYMENT_SCHEMAS,
    **NETSUITE_ACCOUNTING_SCHEMAS,
}

__all__ = ["NETSUITE_SCHEMAS"]
