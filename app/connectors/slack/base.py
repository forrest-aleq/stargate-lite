"""
Slack connector base with authentication.
"""

import os
from typing import Any

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)


class SlackBase:
    """Base class for Slack API with authentication."""

    TOKEN_URL = "https://slack.com/api/oauth.v2.access"

    def __init__(self) -> None:
        self.client_id = os.getenv("SLACK_CLIENT_ID")
        self.client_secret = os.getenv("SLACK_CLIENT_SECRET")

    def _get_access_token(self, org_id: str, user_id: str) -> str:
        """Get Slack access token"""
        cred = CredentialManager.get_credential(org_id, user_id, "slack")

        if not cred:
            raise ValueError(
                f"No Slack credentials found for org_id={org_id}, user_id={user_id}"
            )

        # Slack tokens don't expire in the same way as other OAuth tokens
        # They remain valid until revoked
        return str(cred["access_token"])
