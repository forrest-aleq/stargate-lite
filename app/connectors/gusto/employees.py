"""
Gusto connector - Employee operations
"""

from typing import Any
from urllib.parse import urlencode

from app.http_client import http_client


class GustoEmployeesMixin:
    """Gusto employee operations mixin"""

    def list_employees(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List employees from Gusto"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]

        params = {}
        if args.get("terminated"):
            params["terminated"] = "true"

        url = f"{self.base_url}/v1/companies/{company_id}/employees"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        employees = result if isinstance(result, list) else result.get("employees", [])
        return {
            "employees": [
                {
                    "id": e["uuid"],
                    "first_name": e.get("first_name"),
                    "last_name": e.get("last_name"),
                    "email": e.get("email"),
                    "department": e.get("department"),
                }
                for e in employees
            ],
            "count": len(employees),
        }

    def get_employee(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get employee details"""
        cred = self._get_access_token(org_id, user_id)
        employee_id = args["employee_id"]

        result = http_client.get(
            url=f"{self.base_url}/v1/employees/{employee_id}",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "id": result["uuid"],
            "first_name": result.get("first_name"),
            "last_name": result.get("last_name"),
            "email": result.get("email"),
            "ssn": result.get("ssn_last_four"),
            "date_of_birth": result.get("date_of_birth"),
            "jobs": result.get("jobs", []),
            "compensations": result.get("compensations", []),
            "home_address": result.get("home_address"),
        }

    def create_employee(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an employee in Gusto"""
        cred = self._get_access_token(org_id, user_id)
        company_id = args["company_id"]

        employee_data = {
            "first_name": args["first_name"],
            "last_name": args["last_name"],
            "email": args["email"],
        }
        if args.get("date_of_birth"):
            employee_data["date_of_birth"] = args["date_of_birth"]
        if args.get("ssn"):
            employee_data["ssn"] = args["ssn"]

        result = http_client.post(
            url=f"{self.base_url}/v1/companies/{company_id}/employees",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
            json=employee_data,
        )

        return {
            "id": result["uuid"],
            "status": "created",
        }

    def update_employee(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an employee in Gusto"""
        cred = self._get_access_token(org_id, user_id)
        employee_id = args["employee_id"]

        update_data = {"version": args["version"]}
        for field in ["first_name", "last_name", "email", "date_of_birth"]:
            if args.get(field):
                update_data[field] = args[field]

        result = http_client.put(
            url=f"{self.base_url}/v1/employees/{employee_id}",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
            json=update_data,
        )

        return {
            "id": result["uuid"],
            "version": result.get("version"),
        }

    def terminate_employee(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Terminate an employee in Gusto"""
        cred = self._get_access_token(org_id, user_id)
        employee_id = args["employee_id"]

        termination_data = {
            "effective_date": args["effective_date"],
        }
        if args.get("run_termination_payroll") is not None:
            termination_data["run_termination_payroll"] = args["run_termination_payroll"]

        result = http_client.post(
            url=f"{self.base_url}/v1/employees/{employee_id}/terminations",
            service="gusto",
            headers=self._get_headers(cred["access_token"]),
            json=termination_data,
        )

        return {
            "id": result.get("uuid"),
            "employee_id": employee_id,
            "effective_date": result.get("effective_date"),
        }
