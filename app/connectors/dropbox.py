"""
Dropbox connector for Stargate Lite
Handles file upload, download, and management via Dropbox API v2
"""

import base64
import os
from datetime import datetime, timedelta
from typing import Any

import requests

from app.database import CredentialManager
from app.errors import (
    CredentialInvalidError,
    CredentialMissingError,
    ExternalAPIError,
    NotFoundError,
    RateLimitError,
)
from app.logging_config import get_logger

logger = get_logger(__name__)


class DropboxConnector:
    """Dropbox API v2 connector"""

    def __init__(self) -> None:
        self.client_id = os.getenv("DROPBOX_CLIENT_ID")
        self.client_secret = os.getenv("DROPBOX_CLIENT_SECRET")
        self.api_url = "https://api.dropboxapi.com/2"
        self.content_url = "https://content.dropboxapi.com/2"

    def _get_access_token(self, org_id: str, user_id: str) -> str:
        """Get valid access token, refreshing if necessary"""
        cred_data = CredentialManager.get_credential(org_id, user_id, "dropbox")

        if not cred_data:
            raise CredentialMissingError("dropbox", org_id, user_id)

        # Check if token is expired
        expiry = cred_data.get("token_expiry")
        if expiry and datetime.fromisoformat(expiry) < datetime.now() + timedelta(minutes=5):
            logger.info(
                "Dropbox token expired or expiring soon, refreshing",
                service="dropbox",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_start",
            )
            try:
                # Refresh token
                token_response = requests.post(
                    "https://api.dropboxapi.com/oauth2/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": cred_data["refresh_token"],
                        "grant_type": "refresh_token",
                    },
                    timeout=30,
                )

                if token_response.status_code != 200:
                    raise CredentialInvalidError(
                        "dropbox", f"Token refresh failed: {token_response.text}"
                    )

                token_data = token_response.json()

                new_expiry = datetime.now() + timedelta(seconds=token_data.get("expires_in", 14400))
                CredentialManager.store_credential(
                    org_id=org_id,
                    user_id=user_id,
                    service="dropbox",
                    access_token=token_data["access_token"],
                    refresh_token=cred_data["refresh_token"],
                    token_expiry=new_expiry,
                )

                logger.info(
                    "Dropbox token refreshed successfully",
                    service="dropbox",
                    org_id=org_id,
                    user_id=user_id,
                    log_event="token_refresh_success",
                )

                return str(token_data["access_token"])
            except Exception as e:
                logger.error(
                    "Dropbox token refresh failed",
                    service="dropbox",
                    org_id=org_id,
                    user_id=user_id,
                    error_type=type(e).__name__,
                    log_event="token_refresh_error",
                    exc_info=True,
                )
                raise

        return str(cred_data["access_token"])

    def _handle_error(self, response: requests.Response) -> None:
        """Handle Dropbox API errors"""
        if response.status_code == 401:
            raise CredentialInvalidError("dropbox", "Invalid or expired credentials")
        elif response.status_code == 404 or "path/not_found" in response.text:
            raise NotFoundError("file", "Dropbox resource not found")
        elif response.status_code == 429:
            raise RateLimitError("dropbox")
        elif response.status_code not in [200, 409]:  # 409 can be success for some endpoints
            raise ExternalAPIError("dropbox", response.status_code, response.text)

    def upload_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Upload file to Dropbox"""
        token = self._get_access_token(org_id, user_id)

        file_name = args.get("file_name")
        file_content = args.get("file_content")  # Base64 encoded
        folder_path = args.get("folder_path", "")  # Path like "/Documents"

        if not isinstance(file_content, str):
            raise ValueError("file_content is required and must be a base64 encoded string")

        # Decode base64 content
        file_bytes = base64.b64decode(file_content)

        # Build path
        if folder_path:
            path = f"{folder_path}/{file_name}"
        else:
            path = f"/{file_name}"

        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": f'{{"path": "{path}", "mode": "add", "autorename": true}}',
        }

        response = requests.post(
            f"{self.content_url}/files/upload",
            headers=headers,
            data=file_bytes,
            timeout=60,
        )

        self._handle_error(response)
        result = response.json()

        return {
            "file_id": result.get("id"),
            "file_name": result.get("name"),
            "path": result.get("path_display"),
            "size_bytes": result.get("size"),
            "modified_time": result.get("server_modified"),
            "status": "uploaded",
        }

    def download_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Download file from Dropbox"""
        token = self._get_access_token(org_id, user_id)

        path = args.get("path")  # File path like "/Documents/file.pdf"
        file_id = args.get("file_id")  # Or use file ID

        if file_id:
            path_param = f'{{"path": "id:{file_id}"}}'
        elif path:
            path_param = f'{{"path": "{path}"}}'
        else:
            raise ValueError("Either path or file_id is required")

        headers = {
            "Authorization": f"Bearer {token}",
            "Dropbox-API-Arg": path_param,
        }

        response = requests.post(
            f"{self.content_url}/files/download",
            headers=headers,
            timeout=60,
        )

        self._handle_error(response)

        # Metadata is in response header
        metadata_str = response.headers.get("Dropbox-API-Result", "{}")
        import json

        metadata = json.loads(metadata_str)

        # Encode as base64
        file_content_base64 = base64.b64encode(response.content).decode("utf-8")

        return {
            "file_id": metadata.get("id"),
            "file_name": metadata.get("name"),
            "path": metadata.get("path_display"),
            "size_bytes": metadata.get("size"),
            "file_content": file_content_base64,
            "status": "downloaded",
        }

    def list_files(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List files in Dropbox folder"""
        token = self._get_access_token(org_id, user_id)

        folder_path = args.get("folder_path", "")  # Empty string for root
        limit = args.get("limit", 100)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        data = {
            "path": folder_path,
            "limit": min(limit, 2000),  # Dropbox max is 2000
        }

        response = requests.post(
            f"{self.api_url}/files/list_folder",
            headers=headers,
            json=data,
            timeout=30,
        )

        self._handle_error(response)
        result = response.json()

        entries = result.get("entries", [])

        return {
            "files": [
                {
                    "file_id": entry.get("id"),
                    "file_name": entry.get("name"),
                    "path": entry.get("path_display"),
                    "is_folder": entry.get(".tag") == "folder",
                    "size_bytes": entry.get("size"),
                    "modified_time": entry.get("server_modified"),
                }
                for entry in entries
            ],
            "count": len(entries),
            "has_more": result.get("has_more", False),
            "cursor": result.get("cursor"),
        }

    def create_folder(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a folder in Dropbox"""
        token = self._get_access_token(org_id, user_id)

        folder_name = args.get("folder_name")
        parent_path = args.get("parent_path", "")  # Empty for root

        # Build path
        if parent_path:
            path = f"{parent_path}/{folder_name}"
        else:
            path = f"/{folder_name}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        data = {"path": path, "autorename": True}

        response = requests.post(
            f"{self.api_url}/files/create_folder_v2",
            headers=headers,
            json=data,
            timeout=30,
        )

        self._handle_error(response)
        result = response.json()
        metadata = result.get("metadata", {})

        return {
            "folder_id": metadata.get("id"),
            "folder_name": metadata.get("name"),
            "path": metadata.get("path_display"),
            "status": "created",
        }

    def get_file_metadata(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get file metadata without downloading content"""
        token = self._get_access_token(org_id, user_id)

        path = args.get("path")  # File path
        file_id = args.get("file_id")  # Or use file ID

        if file_id:
            path_param = f"id:{file_id}"
        elif path:
            path_param = path
        else:
            raise ValueError("Either path or file_id is required")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        data = {"path": path_param}

        response = requests.post(
            f"{self.api_url}/files/get_metadata",
            headers=headers,
            json=data,
            timeout=30,
        )

        self._handle_error(response)
        result = response.json()

        return {
            "file_id": result.get("id"),
            "file_name": result.get("name"),
            "path": result.get("path_display"),
            "is_folder": result.get(".tag") == "folder",
            "size_bytes": result.get("size"),
            "modified_time": result.get("server_modified"),
        }
