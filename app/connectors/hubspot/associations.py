"""
HubSpot associations mixin for managing object associations.
"""

from typing import Any

from app.http_client import http_client

from .tickets import TicketsMixin


class AssociationsMixin(TicketsMixin):
    """Mixin with association operations."""

    def create_association(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an association between two objects"""
        cred = self._get_access_token(org_id, user_id)

        from_type = args.get("from_type")  # e.g., "contacts"
        from_id = args.get("from_id", "").replace("hs:", "")
        to_type = args.get("to_type")  # e.g., "companies"
        to_id = args.get("to_id", "").replace("hs:", "")
        association_type = args.get("association_type")

        url = f"{self.BASE_URL}/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}"

        result = http_client.put(
            url=url,
            service="hubspot",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json=[
                {
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": association_type,
                }
            ],
        )

        return {
            "from_id": f"hs:{from_id}",
            "to_id": f"hs:{to_id}",
            "status": "created",
            "labels": result.get("labels", []),
        }

    def list_associations(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List associations for an object"""
        cred = self._get_access_token(org_id, user_id)

        from_type = args.get("from_type")
        from_id = args.get("from_id", "").replace("hs:", "")
        to_type = args.get("to_type")

        url = f"{self.BASE_URL}/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}"

        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )

        associations = [
            {
                "to_id": f"hs:{a.get('toObjectId')}",
                "labels": a.get("associationTypes", []),
            }
            for a in result.get("results", [])
        ]

        return {
            "from_id": f"hs:{from_id}",
            "to_type": to_type,
            "associations": associations,
            "count": len(associations),
        }

    def delete_association(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete an association between two objects"""
        cred = self._get_access_token(org_id, user_id)

        from_type = args.get("from_type")
        from_id = args.get("from_id", "").replace("hs:", "")
        to_type = args.get("to_type")
        to_id = args.get("to_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}"

        http_client.delete(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )

        return {
            "from_id": f"hs:{from_id}",
            "to_id": f"hs:{to_id}",
            "status": "deleted",
        }
