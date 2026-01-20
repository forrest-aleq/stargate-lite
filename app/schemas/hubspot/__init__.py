"""
HubSpot CRM Capability Schemas.

Rich metadata for CRM operations via HubSpot API.
"""

from app.schemas.base import CapabilitySchema

from .companies import HUBSPOT_COMPANY_SCHEMAS
from .contacts import HUBSPOT_CONTACT_SCHEMAS
from .deals import HUBSPOT_DEAL_SCHEMAS

HUBSPOT_SCHEMAS: dict[str, CapabilitySchema] = {
    **HUBSPOT_CONTACT_SCHEMAS,
    **HUBSPOT_DEAL_SCHEMAS,
    **HUBSPOT_COMPANY_SCHEMAS,
}

__all__ = ["HUBSPOT_SCHEMAS"]
