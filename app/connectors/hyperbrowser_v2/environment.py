"""
Hyperbrowser Cloud browser environment.

Provides direct session operations (screenshots, session lifecycle)
via the Hyperbrowser SDK. The managed Claude Computer Use agent
handles all browser automation; this class is for supplementary
operations like on-demand screenshots.
"""

from typing import Any

from hyperbrowser import Hyperbrowser


class HyperbrowserCloud:
    """Thin wrapper for direct Hyperbrowser session operations."""

    def __init__(self, client: Hyperbrowser, session_id: str) -> None:
        self.client = client
        self.session_id = session_id

    def take_screenshot(self) -> str:
        """Take screenshot via Hyperbrowser computer action API.

        Returns:
            Base64-encoded PNG screenshot, or empty string on failure.
        """
        result = self.client.computer_action.screenshot(self.session_id)
        return result.screenshot or ""

    def get_downloads_url(self) -> dict[str, Any]:
        """Get the URL for downloading files from the session."""
        result = self.client.sessions.get_downloads_url(self.session_id)
        return {"url": getattr(result, "url", str(result))}
