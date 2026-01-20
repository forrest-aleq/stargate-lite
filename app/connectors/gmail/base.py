"""
Base class for Gmail connector with authentication.
"""

import base64
import os
from typing import Any, ClassVar

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)


class GmailBase:
    """Gmail API connector base class"""

    SCOPES: ClassVar[list[str]] = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    def __init__(self) -> None:
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    def _get_credentials(self, org_id: str, user_id: str) -> Credentials:
        """Get valid Google credentials, refreshing if necessary"""
        cred_data = CredentialManager.get_credential(org_id, user_id, "google")

        if not cred_data:
            raise ValueError(f"No Google credentials found for org_id={org_id}, user_id={user_id}")

        creds = Credentials(
            token=cred_data["access_token"],
            refresh_token=cred_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.SCOPES,
        )

        # Refresh if needed
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                logger.info(
                    "Google token expired, refreshing",
                    service="gmail",
                    org_id=org_id,
                    user_id=user_id,
                    log_event="token_refresh_start",
                )
                try:
                    creds.refresh(Request())

                    # Store the refreshed token
                    CredentialManager.store_credential(
                        org_id=org_id,
                        user_id=user_id,
                        service="google",
                        access_token=creds.token,
                        refresh_token=creds.refresh_token,
                        token_expiry=creds.expiry,
                    )
                    logger.info(
                        "Google token refreshed successfully",
                        service="gmail",
                        org_id=org_id,
                        user_id=user_id,
                        log_event="token_refresh_success",
                    )
                except Exception as e:
                    logger.error(
                        "Google token refresh failed",
                        service="gmail",
                        org_id=org_id,
                        user_id=user_id,
                        error_type=type(e).__name__,
                        log_event="token_refresh_error",
                        exc_info=True,
                    )
                    raise

        return creds

    def _extract_body(self, message: dict[str, Any]) -> str:
        """Extract email body (plain text or HTML) from message parts"""
        payload = message.get("payload", {})

        # Simple case: body in top-level payload
        if "body" in payload and payload["body"].get("data"):
            decoded = base64.urlsafe_b64decode(payload["body"]["data"])
            return decoded.decode("utf-8", errors="ignore")

        # Multipart: search parts recursively
        def get_body_from_parts(parts: list[dict[str, Any]]) -> str:
            for part in parts:
                mime_type = part.get("mimeType", "")

                # Prefer text/plain over text/html
                if mime_type == "text/plain" and part.get("body", {}).get("data"):
                    decoded = base64.urlsafe_b64decode(part["body"]["data"])
                    return decoded.decode("utf-8", errors="ignore")

                # Recursively search nested parts
                if "parts" in part:
                    nested_body = get_body_from_parts(part["parts"])
                    if nested_body:
                        return nested_body

            # Fallback to HTML if no plain text
            for part in parts:
                if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                    decoded = base64.urlsafe_b64decode(part["body"]["data"])
                    return decoded.decode("utf-8", errors="ignore")

            return ""

        parts = payload.get("parts", [])
        return get_body_from_parts(parts)
