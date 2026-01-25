"""
Gusto connector - Contractor operations
"""

from typing import Any
from urllib.parse import urlencode

from app.http_client import http_client


class GustoContractorsMixin:
    """Gusto contractor operations mixin"""

    def list_contractors(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List contractors from Gusto"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]

        result = http_client.get(
            url=f"{self.base_url}/v1/companies/{company_id}/contractors",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        contractors = result if isinstance(result, list) else result.get("contractors", [])
        return {
            "contractors": [
                {
                    "id": c["uuid"],
                    "first_name": c.get("first_name"),
                    "last_name": c.get("last_name"),
                    "email": c.get("email"),
                    "type": c.get("type"),
                }
                for c in contractors
            ],
            "count": len(contractors),
        }

    def get_contractor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get contractor details"""
        cred = self._get_access_token(org_id, user_id)
        contractor_id = args["contractor_id"]

        result = http_client.get(
            url=f"{self.base_url}/v1/contractors/{contractor_id}",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "id": result["uuid"],
            "first_name": result.get("first_name"),
            "last_name": result.get("last_name"),
            "email": result.get("email"),
            "type": result.get("type"),
            "business_name": result.get("business_name"),
        }

    def create_contractor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a contractor in Gusto"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]

        contractor_data = {
            "first_name": args["first_name"],
            "last_name": args["last_name"],
            "start_date": args["start_date"],
        }
        if args.get("type"):
            contractor_data["type"] = args["type"]
        if args.get("wage_type"):
            contractor_data["wage_type"] = args["wage_type"]
        if args.get("hourly_rate"):
            contractor_data["hourly_rate"] = args["hourly_rate"]
        if args.get("self_onboarding") is not None:
            contractor_data["self_onboarding"] = args["self_onboarding"]

        result = http_client.post(
            url=f"{self.base_url}/v1/companies/{company_id}/contractors",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
            json=contractor_data,
        )

        return {
            "id": result["uuid"],
        }

    def list_contractor_payments(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List contractor payments from Gusto"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]

        params = {}
        if args.get("start_date"):
            params["start_date"] = args["start_date"]
        if args.get("end_date"):
            params["end_date"] = args["end_date"]
        if args.get("contractor_id"):
            params["contractor_uuid"] = args["contractor_id"]

        url = f"{self.base_url}/v1/companies/{company_id}/contractor_payments"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        payments = result if isinstance(result, list) else result.get("contractor_payments", [])
        return {
            "payments": payments,
            "count": len(payments),
        }
