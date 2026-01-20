"""
Plaid Capability Schemas.

Rich metadata for banking data aggregation, transactions, auth, transfers.
"""

from app.schemas.base import CapabilitySchema

from .accounts import PLAID_ACCOUNTS_SCHEMAS
from .core import PLAID_CORE_SCHEMAS
from .transfers import PLAID_TRANSFERS_SCHEMAS

PLAID_SCHEMAS: dict[str, CapabilitySchema] = {
    **PLAID_CORE_SCHEMAS,
    **PLAID_ACCOUNTS_SCHEMAS,
    **PLAID_TRANSFERS_SCHEMAS,
}

__all__ = ["PLAID_SCHEMAS"]
