"""
Zoho Books connector package.

Implements dynamic operation execution for every endpoint in the generated
OpenAPI manifest.
"""

from app.connectors.zoho_books.base import ZohoBooksConnector
from app.connectors.zoho_books.manifest import (
    get_operation_count,
    get_operation_map,
    get_operations,
    get_recommended_scopes,
)

zoho_books_connector = ZohoBooksConnector()

__all__ = [
    "ZohoBooksConnector",
    "get_operation_count",
    "get_operation_map",
    "get_operations",
    "get_recommended_scopes",
    "zoho_books_connector",
]
