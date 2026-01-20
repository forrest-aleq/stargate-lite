"""
HubSpot companies mixin for company CRUD operations.
"""

from typing import Any

from app.http_client import http_client

from .deals import DealsMixin


class CompaniesMixin(DealsMixin):
    """Mixin with company operations."""

    def create_company(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a company in HubSpot"""
        cred = self._get_access_token(org_id, user_id)

        properties = {
            "name": args.get("company_name"),
            "domain": args.get("domain"),
            "industry": args.get("industry"),
            "phone": args.get("phone"),
        }

        # Remove None values
        properties = {k: v for k, v in properties.items() if v is not None}

        url = f"{self.BASE_URL}/crm/v3/objects/companies"
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
            "company_id": f"hs:{result['id']}",
            "company_name": result["properties"].get("name"),
            "domain": result["properties"].get("domain"),
            "created_at": result["createdAt"],
        }

    def get_company(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get company details from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args.get("company_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v3/objects/companies/{company_id}"
        result = http_client.get(
            url=url, service="hubspot", headers={"Authorization": f"Bearer {cred['access_token']}"}
        )

        return {
            "company_id": f"hs:{result['id']}",
            "company_name": result["properties"].get("name"),
            "domain": result["properties"].get("domain"),
            "industry": result["properties"].get("industry"),
        }

    def list_companies(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List companies from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        limit = args.get("limit", 100)

        url = f"{self.BASE_URL}/crm/v3/objects/companies"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
            params={"limit": limit},
        )

        companies = [
            {
                "company_id": f"hs:{c['id']}",
                "company_name": c["properties"].get("name"),
                "domain": c["properties"].get("domain"),
            }
            for c in result.get("results", [])
        ]

        return {"companies": companies, "count": len(companies)}

    def update_company(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a company in HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args.get("company_id", "").replace("hs:", "")

        properties = {}
        if args.get("company_name"):
            properties["name"] = args["company_name"]
        if args.get("domain"):
            properties["domain"] = args["domain"]
        if args.get("industry"):
            properties["industry"] = args["industry"]
        if args.get("phone"):
            properties["phone"] = args["phone"]

        url = f"{self.BASE_URL}/crm/v3/objects/companies/{company_id}"
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
            "company_id": f"hs:{result['id']}",
            "company_name": result["properties"].get("name"),
            "domain": result["properties"].get("domain"),
            "updated_at": result.get("updatedAt"),
        }

    def delete_company(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a company from HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args.get("company_id", "").replace("hs:", "")

        url = f"{self.BASE_URL}/crm/v3/objects/companies/{company_id}"
        http_client.delete(
            url=url, service="hubspot", headers={"Authorization": f"Bearer {cred['access_token']}"}
        )

        return {"company_id": f"hs:{company_id}", "status": "deleted"}

    def search_companies(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search companies in HubSpot"""
        cred = self._get_access_token(org_id, user_id)
        query = args.get("query", "")
        limit = args.get("limit", 10)

        url = f"{self.BASE_URL}/crm/v3/objects/companies/search"
        search_body = {
            "query": query,
            "limit": limit,
            "properties": ["name", "domain", "industry", "phone"],
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

        companies = [
            {
                "company_id": f"hs:{c['id']}",
                "company_name": c["properties"].get("name"),
                "domain": c["properties"].get("domain"),
            }
            for c in result.get("results", [])
        ]

        return {"query": query, "companies": companies, "count": len(companies)}
