"""
HubSpot connector for Stargate Lite.

Handles OAuth 2.0 and CRM operations for contacts, deals, and companies.
"""

from .companies import CompaniesMixin


class HubSpotConnector(CompaniesMixin):
    """HubSpot CRM API connector with full CRUD operations."""

    pass


__all__ = ["HubSpotConnector"]
