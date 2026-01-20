"""
Browser execution environment interface for Hyperbrowser v2.
"""

from typing import Any


class BrowserExecutionEnvironment:
    """
    Interface for browser execution environments.

    Implementations could be:
    - Docker container running browser + VNC
    - Cloud service like BrowserBase, Browserless
    - Local desktop automation
    - Anthropic's reference implementation
    """

    def execute_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a computer use action (click, type, screenshot, etc.)

        Args:
            action: Computer use action dict from Claude
                   e.g., {"action": "key", "text": "Return"}
                        {"action": "left_click", "coordinate": [100, 200]}

        Returns:
            Dict with execution result and new screenshot
        """
        raise NotImplementedError("Execution environment must be configured")

    def take_screenshot(self) -> str:
        """
        Take screenshot of current browser state

        Returns:
            Base64-encoded PNG screenshot
        """
        raise NotImplementedError("Execution environment must be configured")

    def get_download_path(self) -> str:
        """Get path to downloads folder in execution environment"""
        raise NotImplementedError("Execution environment must be configured")
