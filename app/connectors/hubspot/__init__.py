"""
HubSpot connector for Stargate Lite.

Handles OAuth 2.0 and CRM operations for contacts, deals, companies,
tickets, associations, pipelines, owners, notes, and properties.
"""

from .properties import PropertiesMixin


class HubSpotConnector(PropertiesMixin):
    """HubSpot CRM API connector with full CRUD operations."""

    pass


__all__ = ["HubSpotConnector"]
