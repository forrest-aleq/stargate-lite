"""
Core browser action methods for Hyperbrowser v2.
"""

from typing import Any

from app.database import CredentialManager

from .base import HyperbrowserBase


class BrowserActionsMixin(HyperbrowserBase):
    """Mixin with core browser action methods."""

    def navigate_to(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Navigate to URL with wait and validation

        Args:
            url: Target URL
            wait_for_element: Natural description of element to wait for
            timeout: Max wait seconds (default: 30)
            validate_url: Expected URL pattern after navigation
        """
        url = args.get("url")
        wait_for = args.get("wait_for_element")
        timeout = args.get("timeout", 30)

        goal = f"Navigate to {url}"
        if wait_for:
            goal += f" and wait for '{wait_for}' to appear (max {timeout}s)"

        result = self._run_task(goal=goal, max_steps=10)

        return {
            "url": url,
            "status": result["status"],
            "iterations": result["iterations"],
            "action_count": len([a for a in result["action_log"] if a.get("success")]),
            "final_screenshot": result["final_screenshot"],
        }

    def click_element(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Click element by description or selector

        Args:
            description: Natural language description (e.g., "Export button in top right")
            selector: CSS selector (optional, falls back to description)
        """
        description = args.get("description")
        selector = args.get("selector")
        target = selector if selector else description

        goal = f"Click the element: {target}"
        result = self._run_task(goal=goal, max_steps=5)

        return {
            "target": target,
            "status": result["status"],
            "iterations": result["iterations"],
            "final_screenshot": result["final_screenshot"],
        }

    def fill_form(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Fill form fields with values

        Args:
            fields: Dict of field descriptions/selectors to values
                    e.g., {"username": "user@example.com", "password": "secret"}
            submit: Whether to submit form after filling (default: False)
        """
        fields = args.get("fields", {})
        submit = args.get("submit", False)

        field_list = "\n".join([f"- {field}: {value}" for field, value in fields.items()])
        goal = f"Fill in the following form fields:\n{field_list}"
        if submit:
            goal += "\nThen submit the form."

        result = self._run_task(goal=goal, max_steps=10)

        return {
            "fields_filled": len(fields),
            "submitted": submit,
            "status": result["status"],
            "iterations": result["iterations"],
            "final_screenshot": result["final_screenshot"],
        }

    def extract_data(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Extract data from page using natural language description

        Args:
            description: What data to extract (e.g., "all expense amounts from the table")
            format: "json", "csv", "text" (default: "json")
        """
        description = args.get("description")
        output_format = args.get("format", "json")

        goal = f"Extract the following data from the current page: {description}"
        if output_format != "text":
            goal += f"\nFormat the output as {output_format}."

        result = self._run_task(goal=goal, max_steps=5)

        # Get extracted text from the agent's final response
        extracted_text = result.get("result", "")

        return {
            "description": description,
            "format": output_format,
            "data": extracted_text,
            "status": result["status"],
            "final_screenshot": result["final_screenshot"],
        }

    def download_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Trigger file download by clicking download button/link

        Args:
            trigger_description: Description of download button/link
            wait_for_download: Whether to wait for download completion (default: True)
            timeout: Max wait time in seconds (default: 60)
        """
        trigger = args.get("trigger_description")
        wait = args.get("wait_for_download", True)
        timeout = args.get("timeout", 60)

        goal = f"Click '{trigger}' to download the file"
        if wait:
            goal += f" and wait for download to complete (max {timeout}s)"

        result = self._run_task(goal=goal, max_steps=8)

        return {
            "trigger": trigger,
            "status": result["status"],
            "iterations": result["iterations"],
            "final_screenshot": result["final_screenshot"],
        }

    def take_screenshot(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Take screenshot of current browser state

        Returns:
            Screenshot as base64-encoded PNG
        """
        screenshot_data = self._take_screenshot()

        return {
            "screenshot": screenshot_data,
            "has_screenshot": bool(screenshot_data),
            "status": "success",
        }

    def login_to_portal(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Login to web portal (backward compatibility wrapper)

        Args:
            portal_url: Login page URL
            username: Username or email
            password: Password
            mfa_method: "totp", "sms", "email", "none" (default: "none")
        """
        portal_url = args.get("portal_url")
        username = args.get("username")
        mfa_method = args.get("mfa_method", "none")

        # Build single comprehensive login goal for the managed agent
        goal = (
            f"Navigate to {portal_url}, find the login form, "
            f"enter username '{username}' and password, then submit the form."
        )

        if mfa_method != "none":
            goal += f"\nAfter login, complete MFA using {mfa_method} method."

        goal += "\nConfirm successful login by checking for dashboard or account page."

        result = self._run_task(goal=goal, max_steps=15)

        return {
            "portal_url": portal_url,
            "logged_in": result["status"] == "success",
            "mfa_completed": mfa_method != "none",
            "status": result["status"],
        }

    def extract_table_data(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Extract table data from current page

        Args:
            table_description: Natural language description of table
            columns: Optional list of column names to extract
            format: "json" or "csv" (default: "json")
            max_rows: Max rows to extract (default: all)
        """
        table_desc = args.get("table_description")
        columns = args.get("columns", [])
        output_format = args.get("format", "json")
        max_rows = args.get("max_rows")

        goal = f"Extract all data from the table: {table_desc}"
        if columns:
            goal += f"\nOnly extract these columns: {', '.join(columns)}"
        if max_rows:
            goal += f"\nLimit to {max_rows} rows"
        goal += f"\nReturn data in {output_format} format"

        result = self._run_task(
            goal=goal,
            max_steps=15,  # May need scrolling
        )

        # Parse extracted data from result
        data_text = result.get("result", "")

        return {
            "table_description": table_desc,
            "format": output_format,
            "data": data_text,
            "status": result["status"],
            "rows_extracted": data_text.count("\n") if output_format == "csv" else None,
        }

    def wait_for_download(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Wait for file download to complete and return file path

        Args:
            expected_filename: Partial filename to match (e.g., "report", ".xlsx")
            timeout: Max wait seconds (default: 60)
        """
        import re

        expected = args.get("expected_filename", "")
        timeout = args.get("timeout", 60)

        goal = (
            f"Wait for file download to complete (looking for '{expected}' in "
            f"downloads folder, max {timeout}s). Return the full file path."
        )

        result = self._run_task(goal=goal, max_steps=10)

        # Extract file path from result
        file_path = None
        result_text = result.get("result", "")
        if "download" in result_text.lower() and "/" in result_text:
            # Try to extract path
            path_match = re.search(r"([/~][\w\-/\.]+)", result_text)
            if path_match:
                file_path = path_match.group(1)

        return {
            "status": result["status"],
            "file_path": file_path,
            "download_complete": file_path is not None,
            "message": result_text,
        }

    def login_with_credentials(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Login to portal using credentials from CredentialManager

        Args:
            portal_url: Login page URL
            credential_key: Key to retrieve from CredentialManager
            mfa_method: "totp", "sms", "email", "none"
        """
        portal_url = args.get("portal_url")
        credential_key = args.get("credential_key")
        mfa_method = args.get("mfa_method", "none")

        if not isinstance(credential_key, str):
            return {"status": "error", "error": "credential_key is required"}

        # Retrieve credentials
        cred = CredentialManager.get_credential(org_id, user_id, credential_key)
        if not cred:
            return {"status": "error", "error": f"No credentials found for {credential_key}"}

        username = cred.get("username") or cred.get("email")

        # Build login goal
        goal = (
            f"Navigate to {portal_url}, fill in username '{username}' and password, "
            f"then submit the login form."
        )

        if mfa_method != "none":
            goal += f"\nAfter login, complete MFA using {mfa_method} method."
            if mfa_method == "totp":
                totp_secret = cred.get("totp_secret")
                if totp_secret:
                    # Generate TOTP code
                    import pyotp

                    totp = pyotp.TOTP(totp_secret)
                    code = totp.now()
                    goal += f"\nUse this MFA code: {code}"

        goal += "\nConfirm successful login by checking for dashboard or account page."

        result = self._run_task(goal=goal, max_steps=20)

        return {
            "portal_url": portal_url,
            "status": result["status"],
            "logged_in": "success" in result["status"],
            "mfa_completed": mfa_method != "none",
            "iterations": result["iterations"],
        }
