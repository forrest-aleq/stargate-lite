"""
HubSpot properties mixin for property schema operations.
"""

from typing import Any

from app.http_client import http_client

from .notes import NotesMixin


class PropertiesMixin(NotesMixin):
    """Mixin with property operations."""

    def list_properties(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List properties for an object type"""
        cred = self._get_access_token(org_id, user_id)
        object_type = args.get("object_type", "contacts")

        url = f"{self.BASE_URL}/crm/v3/properties/{object_type}"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )

        properties = [
            {
                "name": p.get("name"),
                "label": p.get("label"),
                "type": p.get("type"),
                "field_type": p.get("fieldType"),
                "group_name": p.get("groupName"),
            }
            for p in result.get("results", [])
        ]

        return {
            "object_type": object_type,
            "properties": properties,
            "count": len(properties),
        }
