"""
Google Drive connector for Stargate Lite
Handles file upload, download, and management via Drive API v3
Shares OAuth credentials with Gmail connector (service="google")
"""

import base64
import io
import os
from typing import Any, ClassVar, Never

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

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


class GoogleDriveConnector:
    """Google Drive API connector"""

    # Combined scopes for all Google services (Gmail, Drive, Calendar, Sheets)
    SCOPES: ClassVar[list[str]] = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    def __init__(self) -> None:
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    def _handle_http_error(self, error: HttpError) -> Never:
        """Convert Google API HttpError to StargateError"""
        status_code = error.resp.status
        error_message = str(error)

        if status_code == 401:
            raise CredentialInvalidError("google", "Invalid or expired credentials")
        elif status_code == 404:
            raise NotFoundError("file", "Google Drive resource not found")
        elif status_code == 429:
            raise RateLimitError("google")
        else:
            raise ExternalAPIError("google", status_code, error_message)

    def _get_credentials(self, org_id: str, user_id: str) -> Credentials:
        """Get valid Google credentials (shared with Gmail/Calendar/Sheets)."""
        cred_data = CredentialManager.get_credential(org_id, user_id, "google")

        if not cred_data:
            raise CredentialMissingError("google", org_id, user_id)

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
                    service="google_drive",
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
                        service="google_drive",
                        org_id=org_id,
                        user_id=user_id,
                        log_event="token_refresh_success",
                    )
                except Exception as e:
                    logger.error(
                        "Google token refresh failed",
                        service="google_drive",
                        org_id=org_id,
                        user_id=user_id,
                        error_type=type(e).__name__,
                        log_event="token_refresh_error",
                        exc_info=True,
                    )
                    raise

        return creds

    def upload_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Upload file to Google Drive"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("drive", "v3", credentials=creds)

            file_name = args.get("file_name")
            file_content = args.get("file_content")  # Base64 encoded
            folder_id = args.get("folder_id")  # Optional: parent folder ID
            mime_type = args.get("mime_type", "application/octet-stream")

            if not isinstance(file_content, str):
                raise ValueError("file_content is required and must be a base64 string")

            # Decode base64 content
            file_bytes = base64.b64decode(file_content)
            file_stream = io.BytesIO(file_bytes)

            # File metadata
            file_metadata = {"name": file_name}

            if folder_id:
                file_metadata["parents"] = [folder_id]

            # Upload file
            media = MediaIoBaseUpload(file_stream, mimetype=mime_type, resumable=True)
            file = (
                service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, mimeType, size, createdTime, webViewLink",
                )
                .execute()
            )

            return {
                "file_id": file.get("id"),
                "file_name": file.get("name"),
                "mime_type": file.get("mimeType"),
                "size_bytes": int(file.get("size", 0)),
                "created_time": file.get("createdTime"),
                "web_view_link": file.get("webViewLink"),
                "status": "uploaded",
            }

        except HttpError as error:
            self._handle_http_error(error)

    def download_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Download file from Google Drive"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("drive", "v3", credentials=creds)

            file_id = args.get("file_id")

            # Get file metadata first
            file_metadata = (
                service.files().get(fileId=file_id, fields="name, mimeType, size").execute()
            )

            # Download file content
            request = service.files().get_media(fileId=file_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)

            done = False
            while not done:
                _status, done = downloader.next_chunk()

            # Encode content as base64
            file_stream.seek(0)
            file_content_base64 = base64.b64encode(file_stream.read()).decode("utf-8")

            return {
                "file_id": file_id,
                "file_name": file_metadata.get("name"),
                "mime_type": file_metadata.get("mimeType"),
                "size_bytes": int(file_metadata.get("size", 0)),
                "file_content": file_content_base64,
                "status": "downloaded",
            }

        except HttpError as error:
            self._handle_http_error(error)

    def list_files(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List files in Google Drive (optionally in a specific folder)"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("drive", "v3", credentials=creds)

            folder_id = args.get("folder_id")
            query = args.get("query", "")  # Optional Drive query string
            max_results = args.get("max_results", 100)

            # Build query
            if folder_id:
                query = f"'{folder_id}' in parents"

            # Add "not trashed" to query
            if query:
                query = f"{query} and trashed=false"
            else:
                query = "trashed=false"

            # List files
            results = (
                service.files()
                .list(
                    q=query,
                    pageSize=max_results,
                    fields=(
                        "nextPageToken, files(id, name, mimeType, size, "
                        "createdTime, modifiedTime, webViewLink)"
                    ),
                )
                .execute()
            )

            files = results.get("files", [])

            return {
                "files": [
                    {
                        "file_id": f.get("id"),
                        "file_name": f.get("name"),
                        "mime_type": f.get("mimeType"),
                        "size_bytes": int(f.get("size", 0)) if f.get("size") else 0,
                        "created_time": f.get("createdTime"),
                        "modified_time": f.get("modifiedTime"),
                        "web_view_link": f.get("webViewLink"),
                    }
                    for f in files
                ],
                "count": len(files),
                "next_page_token": results.get("nextPageToken"),
            }

        except HttpError as error:
            self._handle_http_error(error)

    def create_folder(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a folder in Google Drive"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("drive", "v3", credentials=creds)

            folder_name = args.get("folder_name")
            parent_folder_id = args.get("parent_folder_id")  # Optional

            file_metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}

            if parent_folder_id:
                file_metadata["parents"] = [parent_folder_id]

            folder = (
                service.files().create(body=file_metadata, fields="id, name, webViewLink").execute()
            )

            return {
                "folder_id": folder.get("id"),
                "folder_name": folder.get("name"),
                "web_view_link": folder.get("webViewLink"),
                "status": "created",
            }

        except HttpError as error:
            self._handle_http_error(error)

    def get_file_metadata(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get file metadata (name, size, type, last modified) without downloading content"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("drive", "v3", credentials=creds)

            file_id = args.get("file_id")

            file_metadata = (
                service.files()
                .get(
                    fileId=file_id,
                    fields=(
                        "id, name, mimeType, size, createdTime, modifiedTime, "
                        "webViewLink, owners, permissions"
                    ),
                )
                .execute()
            )

            return {
                "file_id": file_metadata.get("id"),
                "file_name": file_metadata.get("name"),
                "mime_type": file_metadata.get("mimeType"),
                "size_bytes": int(file_metadata.get("size", 0)) if file_metadata.get("size") else 0,
                "created_time": file_metadata.get("createdTime"),
                "modified_time": file_metadata.get("modifiedTime"),
                "web_view_link": file_metadata.get("webViewLink"),
                "owners": [owner.get("emailAddress") for owner in file_metadata.get("owners", [])],
            }

        except HttpError as error:
            self._handle_http_error(error)
