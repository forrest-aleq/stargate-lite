"""
QuickBooks Online connector - Reports module
"""

from typing import Any
from urllib.parse import quote, urlencode

from app.http_client import http_client


class QuickBooksReportsMixin:
    """QuickBooks reports and queries mixin"""

    base_url: str

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token - implemented in base class"""
        raise NotImplementedError

    def query_entities(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Query QuickBooks entities using SQL-like syntax"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        query = args.get("query")

        url = f"{self.base_url}/{realm_id}/query?query={quote(str(query))}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        return {
            "results": result.get("QueryResponse", {}),
            "count": result.get("QueryResponse", {}).get("maxResults", 0),
        }

    def get_profit_loss_report(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get P&L report from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        params: dict[str, Any] = {}
        if args.get("start_date"):
            params["start_date"] = args["start_date"]
        if args.get("end_date"):
            params["end_date"] = args["end_date"]
        if args.get("class_id"):
            params["class"] = args["class_id"]
        if args.get("location"):
            params["location"] = args["location"]

        query_str = urlencode(params)
        url = f"{self.base_url}/{realm_id}/reports/ProfitAndLoss?{query_str}"

        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

    def get_balance_sheet(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get balance sheet report"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        params: dict[str, Any] = {}
        end_date = args.get("as_of_date", args.get("end_date"))
        if end_date:
            params["end_date"] = end_date
        query_str = urlencode(params)
        url = f"{self.base_url}/{realm_id}/reports/BalanceSheet?{query_str}"

        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

    def get_profit_loss_detail(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get detailed P&L report"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        params = {
            k: v
            for k, v in [("start_date", args.get("start_date")), ("end_date", args.get("end_date"))]
            if v
        }
        query_str = urlencode(params)
        url = f"{self.base_url}/{realm_id}/reports/ProfitAndLossDetail?{query_str}"

        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

    def get_cashflow_report(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get cash flow statement report"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        params = {
            k: v
            for k, v in [("start_date", args.get("start_date")), ("end_date", args.get("end_date"))]
            if v
        }
        query_str = urlencode(params)
        url = f"{self.base_url}/{realm_id}/reports/CashFlow?{query_str}"

        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

    def get_budget(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get budget data from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Budget"
        if args.get("fiscal_year"):
            query += f" WHERE FiscalYear = '{args['fiscal_year']}'"

        url = f"{self.base_url}/{realm_id}/query?query={quote(query)}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        budgets = result.get("QueryResponse", {}).get("Budget", [])
        return {"budgets": budgets, "count": len(budgets)}

    def get_general_ledger(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get general ledger report"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        params = {
            k: v
            for k, v in [("start_date", args.get("start_date")), ("end_date", args.get("end_date"))]
            if v
        }
        query_str = urlencode(params)
        url = f"{self.base_url}/{realm_id}/reports/GeneralLedger?{query_str}"

        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

    def get_ar_aging(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get A/R aging summary report"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        url = f"{self.base_url}/{realm_id}/reports/AgedReceivables"
        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

    def get_ap_aging(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get A/P aging summary report"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        url = f"{self.base_url}/{realm_id}/reports/AgedPayables"
        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

    def get_ar_aging_detail(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get detailed A/R aging report"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        url = f"{self.base_url}/{realm_id}/reports/AgedReceivableDetail"
        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

    def get_ap_aging_detail(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get detailed A/P aging report"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        url = f"{self.base_url}/{realm_id}/reports/AgedPayableDetail"
        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

    def list_transactions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get transaction list report"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        params = {
            k: v
            for k, v in [("start_date", args.get("start_date")), ("end_date", args.get("end_date"))]
            if v
        }
        query_str = urlencode(params)
        url = f"{self.base_url}/{realm_id}/reports/TransactionList?{query_str}"

        return http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )
