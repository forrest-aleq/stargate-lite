"""
HubSpot notes mixin for note (engagement) operations.
"""

from typing import Any

from app.http_client import http_client

from .owners import OwnersMixin


class NotesMixin(OwnersMixin):
    """Mixin with note operations."""

    def create_note(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a note in HubSpot"""
        cred = self._get_access_token(org_id, user_id)

        properties = {
            "hs_note_body": args.get("body"),
            "hs_timestamp": args.get("timestamp"),
            "hubspot_owner_id": args.get("owner_id"),
        }
        properties = {k: v for k, v in properties.items() if v is not None}

        url = f"{self.BASE_URL}/crm/v3/objects/notes"
        result = http_client.post(
            url=url,
            service="hubspot",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json={"properties": properties},
        )

        return {
            "note_id": f"hs:{result['id']}",
            "body": result["properties"].get("hs_note_body"),
            "created_at": result["createdAt"],
        }

    def list_notes(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List notes from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        limit = args.get("limit", 100)

        url = f"{self.BASE_URL}/crm/v3/objects/notes"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
            params={"limit": limit, "properties": "hs_note_body,hs_timestamp"},
        )

        notes = [
            {
                "note_id": f"hs:{n['id']}",
                "body": n["properties"].get("hs_note_body"),
                "timestamp": n["properties"].get("hs_timestamp"),
            }
            for n in result.get("results", [])
        ]

        return {"notes": notes, "count": len(notes)}

    def get_note(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get note details from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        note_id = args.get("note_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v3/objects/notes/{note_id}"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
            params={"properties": "hs_note_body,hs_timestamp,hubspot_owner_id"},
        )

        return {
            "note_id": f"hs:{result['id']}",
            "body": result["properties"].get("hs_note_body"),
            "timestamp": result["properties"].get("hs_timestamp"),
            "owner_id": result["properties"].get("hubspot_owner_id"),
        }
