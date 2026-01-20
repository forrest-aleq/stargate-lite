"""
Specialized workflow methods for Hyperbrowser v2.
"""

import re
from datetime import datetime
from typing import Any

from .actions import BrowserActionsMixin


class WorkflowsMixin(BrowserActionsMixin):
    """Mixin with specialized workflow methods."""

    def export_powerbi_report(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Complete Power BI export workflow with validation

        Args:
            dashboard_url: Power BI dashboard URL
            report_name: Name of report to export
            filters: Dict of filter_name: filter_value to apply
            export_format: "excel", "pdf", "powerpoint", "csv"
            download_timeout: Max seconds to wait for download
        """
        dashboard_url = args.get("dashboard_url")
        report_name = args.get("report_name")
        filters = args.get("filters", {})
        export_format = args.get("export_format", "excel")
        timeout = args.get("download_timeout", 60)

        # Build comprehensive goal
        goal = f"""
Complete Power BI report export:

1. Navigate to: {dashboard_url}
2. Wait for report '{report_name}' to fully load (charts, tables visible)
"""

        if filters:
            goal += "3. Apply these filters:\n"
            for fname, fvalue in filters.items():
                goal += f"   - {fname}: {fvalue}\n"
            goal += "4. Wait for report to refresh with filtered data\n"
            goal += "5. Click 'Export' or 'File' menu\n"
        else:
            goal += "3. Click 'Export' or 'File' menu\n"

        goal += f"""
{4 if filters else 3}. Select '{export_format.title()}' export option
{5 if filters else 4}. Wait for export dialog to appear
{6 if filters else 5}. Click 'Export' or 'Download' button
{7 if filters else 6}. Wait for download to complete (max {timeout}s)
{8 if filters else 7}. Confirm file appears in downloads folder

Return the full path to the downloaded file.
"""

        result = self._execute_action_loop(
            goal=goal,
            max_iterations=30,  # Complex workflow
        )

        # Extract file path
        file_path = None
        result_text = result.get("result", "")
        if "/" in result_text:
            path_match = re.search(r"([/~][\w\-/\.]+\.xlsx)", result_text)
            if path_match:
                file_path = path_match.group(1)

        return {
            "dashboard_url": dashboard_url,
            "report_name": report_name,
            "filters_applied": filters,
            "export_format": export_format,
            "status": result["status"],
            "file_path": file_path,
            "exported": file_path is not None,
            "iterations": result["iterations"],
            "action_log": result["action_log"],
        }

    def collect_bank_balances(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Collect balances from multiple bank portals

        Args:
            bank_portals: List of dicts with portal_url, credential_key, account_type
            output_format: "json" or "csv"
        """
        bank_portals = args.get("bank_portals", [])
        output_format = args.get("output_format", "json")

        all_balances = []

        for portal in bank_portals:
            portal_url = portal.get("portal_url")
            credential_key = portal.get("credential_key")
            account_type = portal.get("account_type", "checking")

            # Login
            login_result = self.login_with_credentials(
                org_id,
                user_id,
                {
                    "portal_url": portal_url,
                    "credential_key": credential_key,
                    "mfa_method": portal.get("mfa_method", "none"),
                },
            )

            if login_result["status"] != "success":
                all_balances.append(
                    {"portal": portal_url, "error": "Login failed", "balance": None}
                )
                continue

            # Extract balance
            extract_goal = (
                f"Find the current balance for {account_type} account and return "
                f"just the number (e.g., '1234.56')"
            )
            extract_result = self._execute_action_loop(goal=extract_goal, max_iterations=10)

            balance_text = extract_result.get("result", "")
            balance_match = re.search(r"[\d,]+\.?\d*", balance_text)
            balance = float(balance_match.group(0).replace(",", "")) if balance_match else None

            all_balances.append(
                {
                    "portal": portal_url,
                    "account_type": account_type,
                    "balance": balance,
                    "currency": "USD",  # TODO: Detect from page
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Logout
            self._execute_action_loop(goal="Logout from the portal", max_iterations=5)

        return {
            "portals_checked": len(bank_portals),
            "balances": all_balances,
            "format": output_format,
            "total_balance": sum(b["balance"] for b in all_balances if b["balance"]),
        }

    def get_action_log(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Return action log for debugging/audit"""
        return {"action_log": self.action_log, "metrics": self.metrics}

    def reset_session(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Reset session state"""
        self.conversation_history = []
        self.action_log = []

        return {"session_reset": True, "status": "success"}
