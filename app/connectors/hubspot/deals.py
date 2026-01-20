"""
HubSpot deals mixin for deal CRUD operations.
"""

from typing import Any

from app.http_client import http_client

from .contacts import ContactsMixin


class DealsMixin(ContactsMixin):
    """Mixin with deal operations."""

    def create_deal(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a deal in HubSpot"""
        cred = self._get_access_token(org_id, user_id)

        properties = {
            "dealname": args.get("deal_name"),
            "amount": args.get("amount"),
            "dealstage": args.get("deal_stage", "appointmentscheduled"),
            "pipeline": args.get("pipeline", "default"),
        }

        # Remove None values
        properties = {k: v for k, v in properties.items() if v is not None}

        url = f"{self.BASE_URL}/crm/v3/objects/deals"
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
            "deal_id": f"hs:{result['id']}",
            "deal_name": result["properties"].get("dealname"),
            "amount": result["properties"].get("amount"),
            "stage": result["properties"].get("dealstage"),
            "created_at": result["createdAt"],
        }

    def get_deal(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get deal details from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        deal_id = args.get("deal_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v3/objects/deals/{deal_id}"
        result = http_client.get(
            url=url, service="hubspot", headers={"Authorization": f"Bearer {cred['access_token']}"}
        )

        return {
            "deal_id": f"hs:{result['id']}",
            "deal_name": result["properties"].get("dealname"),
            "amount": result["properties"].get("amount"),
            "stage": result["properties"].get("dealstage"),
            "close_date": result["properties"].get("closedate"),
        }

    def list_deals(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List deals from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        limit = args.get("limit", 100)

        url = f"{self.BASE_URL}/crm/v3/objects/deals"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
            params={"limit": limit},
        )

        deals = [
            {
                "deal_id": f"hs:{d['id']}",
                "deal_name": d["properties"].get("dealname"),
                "amount": d["properties"].get("amount"),
                "stage": d["properties"].get("dealstage"),
            }
            for d in result.get("results", [])
        ]

        return {"deals": deals, "count": len(deals)}

    def update_deal(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a deal in HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        deal_id = args.get("deal_id", "").replace("hs:", "")

        properties = {}
        if args.get("deal_name"):
            properties["dealname"] = args["deal_name"]
        if args.get("amount") is not None:
            properties["amount"] = args["amount"]
        if args.get("deal_stage"):
            properties["dealstage"] = args["deal_stage"]
        if args.get("close_date"):
            properties["closedate"] = args["close_date"]

        url = f"{self.BASE_URL}/crm/v3/objects/deals/{deal_id}"
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
            "deal_id": f"hs:{result['id']}",
            "deal_name": result["properties"].get("dealname"),
            "amount": result["properties"].get("amount"),
            "stage": result["properties"].get("dealstage"),
            "updated_at": result.get("updatedAt"),
        }

    def delete_deal(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a deal from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        deal_id = args.get("deal_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v3/objects/deals/{deal_id}"
        http_client.delete(
            url=url, service="hubspot", headers={"Authorization": f"Bearer {cred['access_token']}"}
        )

        return {"deal_id": f"hs:{deal_id}", "status": "deleted"}

    def search_deals(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search deals in HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        query = args.get("query", "")
        limit = args.get("limit", 10)

        url = f"{self.BASE_URL}/crm/v3/objects/deals/search"
        search_body = {
            "query": query,
            "limit": limit,
            "properties": ["dealname", "amount", "dealstage", "closedate"],
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

        deals = [
            {
                "deal_id": f"hs:{d['id']}",
                "deal_name": d["properties"].get("dealname"),
                "amount": d["properties"].get("amount"),
                "stage": d["properties"].get("dealstage"),
            }
            for d in result.get("results", [])
        ]

        return {"query": query, "deals": deals, "count": len(deals)}
