"""
Gusto connector - Payroll operations
"""

from typing import Any
from urllib.parse import urlencode

from app.http_client import http_client


class GustoPayrollMixin:
    """Gusto payroll operations mixin"""

    def list_payrolls(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List payroll runs from Gusto"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]

        params = {}
        if args.get("start_date"):
            params["start_date"] = args["start_date"]
        if args.get("end_date"):
            params["end_date"] = args["end_date"]
        if args.get("processed"):
            params["processed"] = "true"

        url = f"{self.base_url}/v1/companies/{company_id}/payrolls"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        payrolls = result if isinstance(result, list) else result.get("payrolls", [])
        return {
            "payrolls": [
                {
                    "id": p["uuid"],
                    "pay_period": p.get("pay_period"),
                    "check_date": p.get("check_date"),
                    "totals": p.get("totals"),
                    "status": "processed" if p.get("processed") else "unprocessed",
                }
                for p in payrolls
            ],
            "count": len(payrolls),
        }

    def get_payroll(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get payroll details"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]
        payroll_id = args["payroll_id"]

        result = http_client.get(
            url=f"{self.base_url}/v1/companies/{company_id}/payrolls/{payroll_id}",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "id": result["uuid"],
            "pay_period": result.get("pay_period"),
            "check_date": result.get("check_date"),
            "processed": result.get("processed", False),
            "totals": result.get("totals"),
            "employee_compensations": result.get("employee_compensations", []),
        }

    def calculate_payroll(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Calculate payroll (preview before submitting)"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]
        payroll_id = args["payroll_id"]

        result = http_client.put(
            url=f"{self.base_url}/v1/companies/{company_id}/payrolls/{payroll_id}/calculate",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
            json={},
        )

        return {
            "payroll_id": result["uuid"],
            "totals": result.get("totals"),
            "employee_compensations": result.get("employee_compensations", []),
        }

    def submit_payroll(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Submit payroll for processing"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]
        payroll_id = args["payroll_id"]

        result = http_client.put(
            url=f"{self.base_url}/v1/companies/{company_id}/payrolls/{payroll_id}/submit",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
            json={},
        )

        return {
            "payroll_id": result["uuid"],
            "status": "processed" if result.get("processed") else "submitted",
        }
