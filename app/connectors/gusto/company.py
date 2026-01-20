"""
Gusto connector - Company operations
"""

from typing import Any

from app.http_client import http_client


class GustoCompanyMixin:
    """Gusto company operations mixin"""

    def get_company(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get company information"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]

        result = http_client.get(
            url=f"{self.base_url}/v1/companies/{company_id}",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "id": result["uuid"],
            "name": result.get("name"),
            "ein": result.get("ein"),
            "entity_type": result.get("entity_type"),
            "locations": result.get("locations", []),
        }

    def list_companies(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List companies accessible to the user"""
        cred = self._get_access_token(org_id, user_id)

        result = http_client.get(
            url=f"{self.base_url}/v1/companies",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        companies = result if isinstance(result, list) else result.get("companies", [])
        return {
            "companies": [
                {
                    "id": c["uuid"],
                    "name": c.get("name"),
                }
                for c in companies
            ],
            "count": len(companies),
        }

    def list_locations(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List company locations"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]

        result = http_client.get(
            url=f"{self.base_url}/v1/companies/{company_id}/locations",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        locations = result if isinstance(result, list) else result.get("locations", [])
        return {
            "locations": locations,
            "count": len(locations),
        }
