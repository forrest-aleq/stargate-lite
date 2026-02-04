"""
HubSpot owners mixin for owner operations.
"""

from typing import Any

from app.http_client import http_client

from .pipelines import PipelinesMixin


class OwnersMixin(PipelinesMixin):
    """Mixin with owner operations."""

    def list_owners(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List owners in HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        limit = args.get("limit", 100)

        url = f"{self.BASE_URL}/crm/v3/owners"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
            params={"limit": limit},
        )

        owners = [
            {
                "owner_id": o["id"],
                "email": o.get("email"),
                "first_name": o.get("firstName"),
                "last_name": o.get("lastName"),
            }
            for o in result.get("results", [])
        ]

        return {"owners": owners, "count": len(owners)}

    def get_owner(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get owner details from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        owner_id = args.get("owner_id")

        url = f"{self.BASE_URL}/crm/v3/owners/{owner_id}"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )

        return {
            "owner_id": result["id"],
            "email": result.get("email"),
            "first_name": result.get("firstName"),
            "last_name": result.get("lastName"),
            "user_id": result.get("userId"),
        }
