"""
Hyperbrowser connector for Stargate Lite
Browser automation using Anthropic's computer use API (October 2025)
Enables interaction with Power BI, bank portals, and legacy ERPs
"""

import os
from typing import Any

from anthropic import Anthropic

from app.logging_config import get_logger

logger = get_logger(__name__)


class HyperbrowserConnector:
    """
    Browser automation using Anthropic's computer use API
    Model: Claude Sonnet 4.5 with computer_20250124 tool
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client: Anthropic | None = None  # Lazy initialization
        self.model = "claude-sonnet-4-5"
        self.beta_version = "computer-use-2025-01-24"

        # Display settings (recommended ≤ 1280x800)
        self.display_width = 1280
        self.display_height = 800

        # Session state
        self.conversation_history: list[dict[str, Any]] = []
        self.last_screenshot: str | None = None

    def _ensure_client(self) -> None:
        """Ensure Anthropic client is initialized (lazy loading)"""
        if self.client is None:
            if not self.api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Set it in .env file to use browser automation features."
                )
            self.client = Anthropic(api_key=self.api_key)

    def _execute_computer_action(
        self, action: str, instruction: str, max_tokens: int = 4096
    ) -> dict[str, Any]:
        """
        Execute a computer use action via Claude API

        Args:
            action: High-level instruction for Claude (e.g., "Click the Export button")
            instruction: Context or goal (e.g., "Export Power BI report to Excel")
            max_tokens: Max tokens for Claude's response

        Returns:
            Dict with action results and screenshot
        """
        # Ensure client is initialized
        self._ensure_client()
        assert self.client is not None

        # Build messages for conversation
        if not self.conversation_history:
            # First message includes the goal
            messages = [{"role": "user", "content": f"{instruction}\n\nAction: {action}"}]
        else:
            # Continue conversation
            messages = [*self.conversation_history, {"role": "user", "content": action}]

        # Make API call with computer use tool
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            tools=[
                {
                    "type": "computer_20250124",
                    "name": "computer",
                    "display_width_px": self.display_width,
                    "display_height_px": self.display_height,
                }
            ],
            messages=messages,
            betas=[self.beta_version],
        )

        # Update conversation history
        self.conversation_history = [*messages, {"role": "assistant", "content": response.content}]

        # Extract results
        results = {
            "stop_reason": response.stop_reason,
            "content": [],
            "tool_uses": [],
            "text_responses": [],
        }

        for block in response.content:
            if block.type == "tool_use":
                results["tool_uses"].append({"action": block.name, "input": block.input})
            elif block.type == "text":
                results["text_responses"].append(block.text)

            results["content"].append(block)

        return results

    def navigate_to(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Navigate browser to URL and wait for page load

        Args:
            url: Target URL
            wait_for: CSS selector to wait for (optional)
            timeout: Max wait time in seconds (default: 30)
        """
        url = args.get("url")
        wait_for = args.get("wait_for")
        timeout = args.get("timeout", 30)

        if wait_for:
            instruction = (
                f"Navigate to {url} and wait for element "
                f"'{wait_for}' to appear (max {timeout}s)"
            )
        else:
            instruction = f"Navigate to {url} and wait for page to fully load"

        result = self._execute_computer_action(
            action=f"Open a web browser and go to {url}", instruction=instruction
        )

        return {
            "url": url,
            "loaded": result["stop_reason"] != "error",
            "actions_taken": len(result["tool_uses"]),
            "status": "success" if result["stop_reason"] == "end_turn" else "partial",
        }

    def click_element(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Click element by description or selector

        Args:
            description: Natural language description (e.g., "Export button in top right")
            selector: CSS selector (optional, falls back to description)
            click_type: "left", "right", "double", "triple" (default: "left")
        """
        description = args.get("description")
        selector = args.get("selector")
        click_type = args.get("click_type", "left")

        target = selector if selector else description
        instruction = f"Click the element: {target}"

        if click_type != "left":
            instruction += f" (using {click_type} click)"

        result = self._execute_computer_action(
            action=instruction, instruction=f"Find and click: {target}"
        )

        return {
            "target": target,
            "clicked": len(result["tool_uses"]) > 0,
            "actions_taken": len(result["tool_uses"]),
            "status": "success" if result["stop_reason"] == "end_turn" else "partial",
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

        # Build instruction
        field_list = "\n".join([f"- {field}: {value}" for field, value in fields.items()])
        instruction = f"Fill in the following form fields:\n{field_list}"

        if submit:
            instruction += "\nThen submit the form."

        result = self._execute_computer_action(action=instruction, instruction="Fill form fields")

        return {
            "fields_filled": len(fields),
            "submitted": submit,
            "actions_taken": len(result["tool_uses"]),
            "status": "success" if result["stop_reason"] == "end_turn" else "partial",
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

        instruction = f"Extract the following data from the current page: {description}"
        if output_format != "text":
            instruction += f"\nFormat the output as {output_format}."

        result = self._execute_computer_action(
            action=instruction,
            instruction="Extract data from page",
            max_tokens=8000,  # Allow larger responses for data extraction
        )

        # Get extracted text from Claude's response
        extracted_text = "\n".join(result["text_responses"])

        return {
            "description": description,
            "format": output_format,
            "data": extracted_text,
            "status": "success" if result["stop_reason"] == "end_turn" else "partial",
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

        instruction = f"Click '{trigger}' to download the file"
        if wait:
            instruction += f" and wait for download to complete (max {timeout}s)"

        result = self._execute_computer_action(action=instruction, instruction="Download file")

        return {
            "trigger": trigger,
            "download_initiated": len(result["tool_uses"]) > 0,
            "actions_taken": len(result["tool_uses"]),
            "status": "success" if result["stop_reason"] == "end_turn" else "partial",
        }

    def take_screenshot(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Take screenshot of current browser state

        Returns:
            Screenshot as base64-encoded PNG
        """
        result = self._execute_computer_action(
            action="Take a screenshot of the current page", instruction="Capture current state"
        )

        # Find screenshot tool use
        screenshot_data = None
        for tool_use in result["tool_uses"]:
            if tool_use["action"] == "computer" and "screenshot" in str(tool_use["input"]):
                screenshot_data = tool_use["input"].get("screenshot")

        return {
            "screenshot": screenshot_data,
            "has_screenshot": screenshot_data is not None,
            "status": "success",
        }

    # ==================== SPECIALIZED METHODS ====================

    def export_powerbi_report(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Export Power BI report to Excel (October 2025)

        Args:
            dashboard_url: Power BI dashboard URL
            report_name: Name of report to export
            filters: Dict of filters to apply before export (optional)
            download_path: Where to save file (optional)

        Returns:
            File path and export status
        """
        dashboard_url = args.get("dashboard_url")
        report_name = args.get("report_name")
        filters = args.get("filters", {})

        # Step 1: Navigate to Power BI dashboard
        nav_result = self.navigate_to(
            org_id, user_id, {"url": dashboard_url, "wait_for": "Export button", "timeout": 30}
        )

        if not nav_result["loaded"]:
            return {
                "status": "error",
                "error": "Failed to load Power BI dashboard",
                "step": "navigation",
            }

        # Step 2: Apply filters if specified
        if filters:
            filter_instruction = "Apply the following filters:\n"
            for filter_name, filter_value in filters.items():
                filter_instruction += f"- {filter_name}: {filter_value}\n"

            self._execute_computer_action(
                action=filter_instruction, instruction="Apply filters to Power BI report"
            )

        # Step 3: Export to Excel
        export_result = self._execute_computer_action(
            action=(
                f"Click the Export button, select 'Excel', "
                f"and download the '{report_name}' report"
            ),
            instruction="Export Power BI report to Excel",
        )

        # Step 4: Wait for download
        download_result = self._execute_computer_action(
            action="Wait for the Excel file to finish downloading (check downloads folder)",
            instruction="Confirm download completion",
            max_tokens=2000,
        )

        return {
            "dashboard_url": dashboard_url,
            "report_name": report_name,
            "filters_applied": len(filters),
            "exported": "download" in str(export_result["text_responses"]).lower(),
            "status": "success" if export_result["stop_reason"] == "end_turn" else "partial",
            "actions_taken": (
                nav_result["actions_taken"]
                + export_result["actions_taken"]
                + download_result["actions_taken"]
            ),
        }

    def login_to_portal(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Login to web portal (bank, ERP, etc.)

        Args:
            portal_url: Login page URL
            username: Username or email
            password: Password
            mfa_method: "totp", "sms", "email", "none" (default: "none")

        Returns:
            Login status
        """
        portal_url = args.get("portal_url")
        username = args.get("username")
        password = args.get("password")
        mfa_method = args.get("mfa_method", "none")

        # Step 1: Navigate to login page
        self.navigate_to(org_id, user_id, {"url": portal_url})

        # Step 2: Fill in credentials
        self.fill_form(
            org_id,
            user_id,
            {"fields": {"username": username, "password": password}, "submit": True},
        )

        # Step 3: Handle MFA if needed
        if mfa_method != "none":
            mfa_result = self._execute_computer_action(
                action=f"Complete MFA using {mfa_method} method",
                instruction="Handle multi-factor authentication",
            )

            return {
                "portal_url": portal_url,
                "logged_in": "dashboard" in str(mfa_result["text_responses"]).lower(),
                "mfa_completed": len(mfa_result["tool_uses"]) > 0,
                "status": "success",
            }

        return {
            "portal_url": portal_url,
            "logged_in": True,
            "mfa_completed": False,
            "status": "success",
        }

    def reset_session(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Reset browser session (clear history and state)
        Useful for starting fresh workflow
        """
        self.conversation_history = []
        self.last_screenshot = None

        return {"session_reset": True, "status": "success"}
