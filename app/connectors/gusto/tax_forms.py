"""
Gusto connector - Tax forms operations
"""

from typing import Any

from app.http_client import http_client


class GustoTaxFormsMixin:
    """Gusto tax forms operations mixin"""

    def list_tax_forms(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List tax forms from Gusto (W-2s and 1099s)"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]
        year = args["year"]
        form_type = args.get("form_type", "w2")

        if form_type == "1099":
            url = f"{self.base_url}/v1/companies/{company_id}/forms/1099s/{year}"
        else:
            url = f"{self.base_url}/v1/companies/{company_id}/forms/w2s/{year}"

        result = http_client.get(
            url=url,
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        forms = result if isinstance(result, list) else result.get("forms", [])
        return {
            "forms": forms,
            "count": len(forms),
            "form_type": form_type,
            "year": year,
        }
