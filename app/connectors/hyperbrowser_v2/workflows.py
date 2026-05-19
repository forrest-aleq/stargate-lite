"""
Specialized workflow methods for Hyperbrowser v2.
"""

import re
from datetime import UTC, datetime
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

        result = self._run_task(
            goal=goal,
            max_steps=30,  # Complex workflow
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
            extract_result = self._run_task(goal=extract_goal, max_steps=10, keep_browser_open=True)

            balance_text = extract_result.get("result", "")
            balance_match = re.search(r"[\d,]+\.?\d*", balance_text)
            balance = float(balance_match.group(0).replace(",", "")) if balance_match else None

            all_balances.append(
                {
                    "portal": portal_url,
                    "account_type": account_type,
                    "balance": balance,
                    "currency": "USD",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            # Logout
            self._run_task(goal="Logout from the portal", max_steps=5)

        return {
            "portals_checked": len(bank_portals),
            "balances": all_balances,
            "format": output_format,
            "total_balance": sum(b["balance"] for b in all_balances if b["balance"]),
        }

    def accept_invite(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Accept a service invite via browser automation.

        Args:
            invite_url: The invite link URL
            display_name: Name to use if prompted (default: "Aleq")
            email: Email to use if prompted (default: "aleq@aleq.net")
        """
        invite_url = args.get("invite_url")
        display_name = args.get("display_name", "Aleq")
        email = args.get("email", "aleq@aleq.net")

        if not invite_url:
            return {"status": "error", "error": "invite_url is required"}

        goal = f"""
Accept this invitation:

1. Navigate to: {invite_url}
2. If prompted for a name, use: {display_name}
3. If prompted for an email, use: {email}
4. If there is an "Accept" or "Join" button, click it
5. If asked to create an account, fill in the signup form with the name and email above
6. Complete any onboarding steps (skip optional ones)
7. Confirm you've successfully joined/accepted by checking for a dashboard or welcome page

Return the final page URL and any account details shown.
"""

        result = self._run_task(goal=goal, max_steps=25)

        return {
            "invite_url": invite_url,
            "status": result["status"],
            "accepted": result["status"] == "success",
            "result": result.get("result", ""),
            "iterations": result["iterations"],
            "final_screenshot": result["final_screenshot"],
        }

    def signup_for_service(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Sign up for a new service via browser automation.

        Args:
            signup_url: The signup page URL
            display_name: Name to use (default: "Aleq")
            email: Email to use (default: "aleq@aleq.net")
            password: Password to use (generate one if not provided)
            extra_fields: Dict of additional form fields to fill
        """
        signup_url = args.get("signup_url")
        display_name = args.get("display_name", "Aleq")
        email = args.get("email", "aleq@aleq.net")
        password = args.get("password", "")
        extra_fields = args.get("extra_fields", {})

        if not signup_url:
            return {"status": "error", "error": "signup_url is required"}

        goal = f"""
Sign up for a new account:

1. Navigate to: {signup_url}
2. Find the signup/registration form
3. Fill in:
   - Name/Display Name: {display_name}
   - Email: {email}
"""
        if password:
            goal += f"   - Password: {password}\n"
        else:
            goal += "   - Password: Generate a strong password if required\n"

        for field_name, field_value in extra_fields.items():
            goal += f"   - {field_name}: {field_value}\n"

        goal += """
4. Accept any terms of service / privacy policy checkboxes
5. Submit the registration form
6. If email verification is required, note that in your response
7. Complete any onboarding steps (skip optional ones)
8. Return the final page URL and confirmation of account creation

Return any account details, confirmation messages, or next steps shown.
"""

        result = self._run_task(goal=goal, max_steps=30)

        return {
            "signup_url": signup_url,
            "email": email,
            "status": result["status"],
            "signed_up": result["status"] == "success",
            "result": result.get("result", ""),
            "needs_email_verification": "verif" in result.get("result", "").lower(),
            "iterations": result["iterations"],
            "final_screenshot": result["final_screenshot"],
        }

    def get_action_log(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Return action log for debugging/audit"""
        return {"action_log": self.action_log, "metrics": self.metrics}

    def reset_session(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Reset session state"""
        self._stop_session()
        self.action_log = []

        return {"session_reset": True, "status": "success"}
