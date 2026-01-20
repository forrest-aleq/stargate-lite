"""
Read, download, watch, and helper operations for Gmail connector.
"""

import base64
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.logging_config import get_logger

from .labels import LabelsMixin

logger = get_logger(__name__)


class ReadMixin(LabelsMixin):
    """Mixin with read, download, watch, and helper operations."""

    def read_emails(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Read emails from Gmail"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            # Build query
            query = args.get("query", "")
            max_results = args.get("max_results", 10)

            # Get messages
            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])

            # Get full message details
            email_list = []
            for msg in messages:
                message = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )

                headers = {h["name"]: h["value"] for h in message["payload"].get("headers", [])}

                email_list.append(
                    {
                        "message_id": message["id"],
                        "thread_id": message["threadId"],
                        "subject": headers.get("Subject", ""),
                        "from": headers.get("From", ""),
                        "to": headers.get("To", ""),
                        "date": headers.get("Date", ""),
                        "snippet": message.get("snippet", ""),
                    }
                )

            return {
                "emails": email_list,
                "count": len(email_list),
                "next_page_token": results.get("nextPageToken"),
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def get_history(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Fetch Gmail history changes since start_history_id"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            start_history_id = args.get("start_history_id")
            max_results = args.get("max_results", 100)
            email_address = args.get("email_address", "me")

            response = (
                service.users()
                .history()
                .list(
                    userId=email_address,
                    startHistoryId=start_history_id,
                    historyTypes=["messageAdded"],
                    maxResults=max_results,
                )
                .execute()
            )

            return {
                "history": response.get("history", []),
                "history_id": response.get("historyId"),
                "next_page_token": response.get("nextPageToken"),
            }

        except HttpError as error:
            if error.resp.status == 404:
                history_id = args.get("start_history_id")
                logger.warning(
                    f"History expired for {org_id}/{user_id} (historyId: {history_id}). "
                    f"This is rare but expected. Returning empty history."
                )
                return {"history": [], "history_id": history_id}
            raise Exception(f"Gmail API error: {error}") from error

    def get_message_full(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Fetch full message with headers, body, and attachment metadata"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            message_id = args.get("message_id")
            email_address = args.get("email_address", "me")

            message = (
                service.users()
                .messages()
                .get(userId=email_address, id=message_id, format="full")
                .execute()
            )

            # Extract key fields
            headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
            body = self._extract_body(message)
            attachments = self._extract_attachment_metadata(message)

            return {
                "message_id": message["id"],
                "thread_id": message["threadId"],
                "label_ids": message.get("labelIds", []),
                "snippet": message.get("snippet", ""),
                "internal_date": message.get("internalDate"),
                "headers": headers,
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "body": body,
                "attachments": attachments,
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def download_attachment(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Download attachment and save to specified path"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            message_id = args.get("message_id")
            attachment_id = args.get("attachment_id")
            output_path_str = args.get("output_path")
            if not isinstance(output_path_str, str):
                raise ValueError("output_path is required")
            output_path = Path(output_path_str)
            email_address = args.get("email_address", "me")

            attachment = (
                service.users()
                .messages()
                .attachments()
                .get(userId=email_address, messageId=message_id, id=attachment_id)
                .execute()
            )

            # Decode and write to file
            file_data = base64.urlsafe_b64decode(attachment["data"])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(file_data)

            logger.info(f"Downloaded attachment {attachment_id} to {output_path}")

            return {
                "output_path": str(output_path),
                "size_bytes": len(file_data),
                "status": "downloaded",
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def setup_watch(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Set up Gmail push notifications watch"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            topic_name = args.get("topic_name")
            label_ids = args.get("label_ids", ["INBOX"])
            email_address = args.get("email_address", "me")

            watch_request = {"topicName": topic_name, "labelIds": label_ids}

            response = service.users().watch(userId=email_address, body=watch_request).execute()

            logger.info(f"Set up watch for {email_address}: expires at {response['expiration']}")

            return {
                "history_id": response["historyId"],
                "expiration": response["expiration"],
                "status": "active",
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def mark_as_read(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Mark message as read (remove UNREAD label)"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            message_id = args.get("message_id")
            email_address = args.get("email_address", "me")

            service.users().messages().modify(
                userId=email_address, id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()

            logger.info(f"Marked message {message_id} as read")

            return {"message_id": message_id, "status": "read"}

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    # Helper methods

    def _extract_attachment_metadata(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract attachment metadata from message (without downloading)"""
        attachments: list[dict[str, Any]] = []

        def extract_from_parts(parts: list[dict[str, Any]]) -> None:
            for part in parts:
                filename = part.get("filename")
                if filename and part.get("body", {}).get("attachmentId"):
                    attachments.append(
                        {
                            "attachment_id": part["body"]["attachmentId"],
                            "filename": filename,
                            "mime_type": part.get("mimeType", "application/octet-stream"),
                            "size_bytes": part["body"].get("size", 0),
                        }
                    )

                # Recursively check nested parts
                if "parts" in part:
                    extract_from_parts(part["parts"])

        payload = message.get("payload", {})
        if "parts" in payload:
            extract_from_parts(payload["parts"])

        return attachments
