"""
Square connector - Location operations
"""

from typing import Any

from app.http_client import http_client


class SquareLocationsMixin:
    """Square location operations mixin"""

    def list_locations(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List Square locations"""
        cred = self._get_access_token(org_id, user_id)

        result = http_client.get(
            url=f"{self.base_url}/locations",
            service="square",
            headers=self._get_headers(cred["access_token"]),
        )

        locations = result.get("locations", [])
        return {
            "locations": [
                {
                    "id": loc["id"],
                    "name": loc.get("name"),
                    "address": loc.get("address"),
                    "timezone": loc.get("timezone"),
                    "currency": loc.get("currency"),
                }
                for loc in locations
            ],
            "count": len(locations),
        }

    def get_location(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get location details"""
        cred = self._get_access_token(org_id, user_id)
        location_id = args["location_id"]

        result = http_client.get(
            url=f"{self.base_url}/locations/{location_id}",
            service="square",
            headers=self._get_headers(cred["access_token"]),
        )

        loc = result.get("location", result)
        return {
            "id": loc["id"],
            "name": loc.get("name"),
            "address": loc.get("address"),
            "timezone": loc.get("timezone"),
            "currency": loc.get("currency"),
            "business_name": loc.get("business_name"),
            "status": loc.get("status"),
        }
