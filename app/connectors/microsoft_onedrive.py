"""
Microsoft OneDrive connector for Stargate Lite
Handles file upload, download, and management via Microsoft Graph API
Shares OAuth credentials with Excel and Outlook Calendar (service="microsoft")
"""

import base64
import os
from datetime import datetime, timedelta
from typing import Any, ClassVar, cast

import requests

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)


class MicrosoftOneDriveConnector:
    """Microsoft Graph API OneDrive connector"""

    # Combined scopes for all Microsoft services
    SCOPES: ClassVar[list[str]] = [
        "https://graph.microsoft.com/Files.ReadWrite.All",
        "https://graph.microsoft.com/Calendars.ReadWrite",
        "https://graph.microsoft.com/Mail.ReadWrite",
        "offline_access",
    ]

    def __init__(self) -> None:
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.graph_url = "https://graph.microsoft.com/v1.0"

    def _get_access_token(self, org_id: str, user_id: str) -> str:
        """Get valid access token, refreshing if necessary"""
        cred_data = CredentialManager.get_credential(org_id, user_id, "microsoft")

        if not cred_data:
            raise ValueError(
                f"No Microsoft credentials found for org_id={org_id}, user_id={user_id}"
            )

        # Check if token is expired
        expiry = cred_data.get("token_expiry")
        if expiry and datetime.fromisoformat(expiry) < datetime.now() + timedelta(minutes=5):
            logger.info(
                "Microsoft token expired or expiring soon, refreshing",
                service="microsoft_onedrive",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_start",
            )
            try:
                # Refresh token
                token_response = requests.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": cred_data["refresh_token"],
                        "grant_type": "refresh_token",
                        "scope": " ".join(self.SCOPES),
                    },
                    timeout=30,
                )

                if token_response.status_code != 200:
                    raise Exception(f"Token refresh failed: {token_response.text}")

                token_data = token_response.json()

                new_expiry = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))
                CredentialManager.store_credential(
                    org_id=org_id,
                    user_id=user_id,
                    service="microsoft",
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token", cred_data["refresh_token"]),
                    token_expiry=new_expiry,
                )

                logger.info(
                    "Microsoft token refreshed successfully",
                    service="microsoft_onedrive",
                    org_id=org_id,
                    user_id=user_id,
                    expires_in_seconds=token_data.get("expires_in", 3600),
                    log_event="token_refresh_success",
                )

                return str(token_data["access_token"])
            except Exception as e:
                logger.error(
                    "Microsoft token refresh failed",
                    service="microsoft_onedrive",
                    org_id=org_id,
                    user_id=user_id,
                    error_type=type(e).__name__,
                    log_event="token_refresh_error",
                    exc_info=True,
                )
                raise

        return str(cred_data["access_token"])

    def _make_request(
        self, method: str, endpoint: str, token: str, data: Any = None, is_binary: bool = False
    ) -> dict[str, Any]:
        """Make authenticated request to Microsoft Graph API"""
        url = f"{self.graph_url}/{endpoint}"

        headers = {"Authorization": f"Bearer {token}"}

        if not is_binary:
            headers["Content-Type"] = "application/json"

        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            json_data = data if not is_binary else None
            binary_data = data if is_binary else None
            response = requests.post(
                url, headers=headers, json=json_data, data=binary_data, timeout=30
            )
        elif method == "PUT":
            json_data = data if not is_binary else None
            binary_data = data if is_binary else None
            response = requests.put(
                url, headers=headers, json=json_data, data=binary_data, timeout=30
            )
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if response.status_code not in [200, 201, 204]:
            raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")

        if response.status_code == 204:
            return {"status": "success"}

        # For binary downloads
        if is_binary and method == "GET":
            return {"content": response.content}

        return cast(dict[str, Any], response.json())

    def upload_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Upload file to OneDrive"""
        token = self._get_access_token(org_id, user_id)

        file_name = args.get("file_name")
        file_content = args.get("file_content")  # Base64 encoded
        folder_path = args.get("folder_path", "")  # Optional: path like "/Documents"

        if not isinstance(file_content, str):
            raise ValueError("file_content is required and must be a base64 encoded string")

        # Decode base64 content
        file_bytes = base64.b64decode(file_content)

        # Build endpoint
        if folder_path:
            endpoint = f"me/drive/root:{folder_path}/{file_name}:/content"
        else:
            endpoint = f"me/drive/root:/{file_name}:/content"

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"}

        url = f"{self.graph_url}/{endpoint}"
        response = requests.put(url, headers=headers, data=file_bytes, timeout=30)

        if response.status_code not in [200, 201]:
            raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")

        result = response.json()

        return {
            "file_id": result.get("id"),
            "file_name": result.get("name"),
            "size_bytes": result.get("size"),
            "created_time": result.get("createdDateTime"),
            "web_url": result.get("webUrl"),
            "status": "uploaded",
        }

    def download_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Download file from OneDrive"""
        token = self._get_access_token(org_id, user_id)

        file_id = args.get("file_id")

        # Get file metadata first
        endpoint_meta = f"me/drive/items/{file_id}"
        metadata = self._make_request("GET", endpoint_meta, token)

        # Download content
        endpoint_content = f"me/drive/items/{file_id}/content"
        content_result = self._make_request("GET", endpoint_content, token, is_binary=True)

        # Encode as base64
        file_content_base64 = base64.b64encode(content_result["content"]).decode("utf-8")

        return {
            "file_id": file_id,
            "file_name": metadata.get("name"),
            "size_bytes": metadata.get("size"),
            "file_content": file_content_base64,
            "status": "downloaded",
        }

    def list_files(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List files in OneDrive (optionally in a specific folder)"""
        token = self._get_access_token(org_id, user_id)

        folder_id = args.get("folder_id")
        folder_path = args.get("folder_path")  # Alternative: path like "/Documents"

        if folder_id:
            endpoint = f"me/drive/items/{folder_id}/children"
        elif folder_path:
            endpoint = f"me/drive/root:{folder_path}:/children"
        else:
            endpoint = "me/drive/root/children"

        result = self._make_request("GET", endpoint, token)

        items = result.get("value", [])

        return {
            "files": [
                {
                    "file_id": item.get("id"),
                    "file_name": item.get("name"),
                    "size_bytes": item.get("size"),
                    "is_folder": "folder" in item,
                    "created_time": item.get("createdDateTime"),
                    "modified_time": item.get("lastModifiedDateTime"),
                    "web_url": item.get("webUrl"),
                }
                for item in items
            ],
            "count": len(items),
        }

    def create_folder(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a folder in OneDrive"""
        token = self._get_access_token(org_id, user_id)

        folder_name = args.get("folder_name")
        parent_folder_id = args.get("parent_folder_id")  # Optional
        parent_folder_path = args.get("parent_folder_path")  # Alternative

        if parent_folder_id:
            endpoint = f"me/drive/items/{parent_folder_id}/children"
        elif parent_folder_path:
            endpoint = f"me/drive/root:{parent_folder_path}:/children"
        else:
            endpoint = "me/drive/root/children"

        data: dict[str, Any] = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename",
        }

        result = self._make_request("POST", endpoint, token, data)

        return {
            "folder_id": result.get("id"),
            "folder_name": result.get("name"),
            "web_url": result.get("webUrl"),
            "status": "created",
        }

    def get_file_metadata(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get file metadata without downloading content"""
        token = self._get_access_token(org_id, user_id)

        file_id = args.get("file_id")

        endpoint = f"me/drive/items/{file_id}"

        result = self._make_request("GET", endpoint, token)

        return {
            "file_id": result.get("id"),
            "file_name": result.get("name"),
            "size_bytes": result.get("size"),
            "is_folder": "folder" in result,
            "created_time": result.get("createdDateTime"),
            "modified_time": result.get("lastModifiedDateTime"),
            "web_url": result.get("webUrl"),
            "mime_type": result.get("file", {}).get("mimeType"),
        }
