"""
Gmail Capability Schemas.

Rich metadata for email operations via Gmail API.
"""

from app.schemas.base import CapabilitySchema

from .actions import GMAIL_ACTION_SCHEMAS
from .core import GMAIL_CORE_SCHEMAS
from .threads import GMAIL_THREAD_SCHEMAS

GMAIL_SCHEMAS: dict[str, CapabilitySchema] = {
    **GMAIL_CORE_SCHEMAS,
    **GMAIL_ACTION_SCHEMAS,
    **GMAIL_THREAD_SCHEMAS,
}

__all__ = ["GMAIL_SCHEMAS"]
