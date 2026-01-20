"""
HubSpot contacts mixin for contact CRUD operations.
"""

from typing import Any

from app.http_client import http_client

from .base import HubSpotBase


class ContactsMixin(HubSpotBase):
    """Mixin with contact operations."""

    def create_contact(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a contact in HubSpot"""
        cred = self._get_access_token(org_id, user_id)

        # Build contact properties
        properties = {
            "email": args.get("email"),
            "firstname": args.get("first_name"),
            "lastname": args.get("last_name"),
            "phone": args.get("phone"),
            "company": args.get("company"),
        }

        # Remove None values
        properties = {k: v for k, v in properties.items() if v is not None}

        url = f"{self.BASE_URL}/crm/v3/objects/contacts"
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
            "contact_id": f"hs:{result['id']}",
            "email": result["properties"].get("email"),
            "first_name": result["properties"].get("firstname"),
            "last_name": result["properties"].get("lastname"),
            "created_at": result["createdAt"],
        }

    def get_contact(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get contact details from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        contact_id = args.get("contact_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}"
        result = http_client.get(
            url=url, service="hubspot", headers={"Authorization": f"Bearer {cred['access_token']}"}
        )

        return {
            "contact_id": f"hs:{result['id']}",
            "email": result["properties"].get("email"),
            "first_name": result["properties"].get("firstname"),
            "last_name": result["properties"].get("lastname"),
            "company": result["properties"].get("company"),
        }

    def list_contacts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List contacts from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        limit = args.get("limit", 100)

        url = f"{self.BASE_URL}/crm/v3/objects/contacts"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
            params={"limit": limit},
        )

        contacts = [
            {
                "contact_id": f"hs:{c['id']}",
                "email": c["properties"].get("email"),
                "first_name": c["properties"].get("firstname"),
                "last_name": c["properties"].get("lastname"),
            }
            for c in result.get("results", [])
        ]

        return {"contacts": contacts, "count": len(contacts)}

    def update_contact(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a contact in HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        contact_id = args.get("contact_id", "").replace("hs:", "")

        properties = {}
        if args.get("email"):
            properties["email"] = args["email"]
        if args.get("first_name"):
            properties["firstname"] = args["first_name"]
        if args.get("last_name"):
            properties["lastname"] = args["last_name"]
        if args.get("phone"):
            properties["phone"] = args["phone"]
        if args.get("company"):
            properties["company"] = args["company"]

        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}"
        result = http_client.patch(
            url=url,
            service="hubspot",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json={"properties": properties},
        )

        return {
            "contact_id": f"hs:{result['id']}",
            "email": result["properties"].get("email"),
            "first_name": result["properties"].get("firstname"),
            "last_name": result["properties"].get("lastname"),
            "updated_at": result.get("updatedAt"),
        }

    def delete_contact(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a contact from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        contact_id = args.get("contact_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}"
        http_client.delete(
            url=url, service="hubspot", headers={"Authorization": f"Bearer {cred['access_token']}"}
        )

        return {"contact_id": f"hs:{contact_id}", "status": "deleted"}

    def search_contacts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search contacts in HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        query = args.get("query", "")
        limit = args.get("limit", 10)

        url = f"{self.BASE_URL}/crm/v3/objects/contacts/search"
        search_body = {
            "query": query,
            "limit": limit,
            "properties": ["email", "firstname", "lastname", "company", "phone"],
        }

        result = http_client.post(
            url=url,
            service="hubspot",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json=search_body,
        )

        contacts = [
            {
                "contact_id": f"hs:{c['id']}",
                "email": c["properties"].get("email"),
                "first_name": c["properties"].get("firstname"),
                "last_name": c["properties"].get("lastname"),
            }
            for c in result.get("results", [])
        ]

        return {"query": query, "contacts": contacts, "count": len(contacts)}
