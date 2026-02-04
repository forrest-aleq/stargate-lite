"""
HubSpot tickets mixin for ticket CRUD operations.
"""

from typing import Any

from app.http_client import http_client

from .companies import CompaniesMixin


class TicketsMixin(CompaniesMixin):
    """Mixin with ticket operations."""

    def create_ticket(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a ticket in HubSpot"""
        cred = self._get_access_token(org_id, user_id)

        properties = {
            "subject": args.get("subject"),
            "content": args.get("content"),
            "hs_pipeline": args.get("pipeline"),
            "hs_pipeline_stage": args.get("pipeline_stage"),
            "hs_ticket_priority": args.get("priority"),
        }
        properties = {k: v for k, v in properties.items() if v is not None}

        url = f"{self.BASE_URL}/crm/v3/objects/tickets"
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
            "ticket_id": f"hs:{result['id']}",
            "subject": result["properties"].get("subject"),
            "created_at": result["createdAt"],
        }

    def get_ticket(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get ticket details from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        ticket_id = args.get("ticket_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v3/objects/tickets/{ticket_id}"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )

        return {
            "ticket_id": f"hs:{result['id']}",
            "subject": result["properties"].get("subject"),
            "content": result["properties"].get("content"),
            "status": result["properties"].get("hs_pipeline_stage"),
            "priority": result["properties"].get("hs_ticket_priority"),
        }

    def list_tickets(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List tickets from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        limit = args.get("limit", 100)

        url = f"{self.BASE_URL}/crm/v3/objects/tickets"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
            params={"limit": limit},
        )

        tickets = [
            {
                "ticket_id": f"hs:{t['id']}",
                "subject": t["properties"].get("subject"),
                "status": t["properties"].get("hs_pipeline_stage"),
            }
            for t in result.get("results", [])
        ]

        return {"tickets": tickets, "count": len(tickets)}

    def update_ticket(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a ticket in HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        ticket_id = args.get("ticket_id", "").replace("hs:", "")

        properties: dict[str, Any] = {}
        if args.get("subject"):
            properties["subject"] = args["subject"]
        if args.get("content"):
            properties["content"] = args["content"]
        if args.get("pipeline_stage"):
            properties["hs_pipeline_stage"] = args["pipeline_stage"]
        if args.get("priority"):
            properties["hs_ticket_priority"] = args["priority"]

        url = f"{self.BASE_URL}/crm/v3/objects/tickets/{ticket_id}"
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
            "ticket_id": f"hs:{result['id']}",
            "subject": result["properties"].get("subject"),
            "updated_at": result.get("updatedAt"),
        }

    def delete_ticket(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a ticket from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        ticket_id = args.get("ticket_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v3/objects/tickets/{ticket_id}"
        http_client.delete(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )

        return {"ticket_id": f"hs:{ticket_id}", "status": "deleted"}

    def search_tickets(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search tickets in HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        query = args.get("query", "")
        limit = args.get("limit", 10)

        url = f"{self.BASE_URL}/crm/v3/objects/tickets/search"
        result = http_client.post(
            url=url,
            service="hubspot",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "limit": limit,
                "properties": ["subject", "content", "hs_pipeline_stage"],
            },
        )

        tickets = [
            {
                "ticket_id": f"hs:{t['id']}",
                "subject": t["properties"].get("subject"),
                "status": t["properties"].get("hs_pipeline_stage"),
            }
            for t in result.get("results", [])
        ]

        return {"query": query, "tickets": tickets, "count": len(tickets)}
