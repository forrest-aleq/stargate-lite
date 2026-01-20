"""
Label and thread operations for Gmail connector.
"""

from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.logging_config import get_logger

from .send import SendMixin

logger = get_logger(__name__)


class LabelsMixin(SendMixin):
    """Mixin with label and thread operations."""

    def trash_message(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Move message to trash"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            message_id = args.get("message_id")
            email_address = args.get("email_address", "me")

            service.users().messages().trash(userId=email_address, id=message_id).execute()

            logger.info(f"Moved message {message_id} to trash")

            return {"message_id": message_id, "status": "trashed"}

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def untrash_message(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Restore message from trash"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            message_id = args.get("message_id")
            email_address = args.get("email_address", "me")

            service.users().messages().untrash(userId=email_address, id=message_id).execute()

            logger.info(f"Restored message {message_id} from trash")

            return {"message_id": message_id, "status": "restored"}

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def star_message(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Star or unstar a message"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            message_id = args.get("message_id")
            starred = args.get("starred", True)
            email_address = args.get("email_address", "me")

            body: dict[str, list[str]] = {}
            if starred:
                body["addLabelIds"] = ["STARRED"]
            else:
                body["removeLabelIds"] = ["STARRED"]

            service.users().messages().modify(
                userId=email_address, id=message_id, body=body
            ).execute()

            action = "starred" if starred else "unstarred"
            logger.info(f"{action.capitalize()} message {message_id}")

            return {"message_id": message_id, "starred": starred, "status": action}

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def list_labels(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all labels in the mailbox"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            email_address = args.get("email_address", "me")

            results = service.users().labels().list(userId=email_address).execute()
            labels = results.get("labels", [])

            return {
                "labels": [
                    {
                        "label_id": label["id"],
                        "name": label["name"],
                        "type": label.get("type", "user"),
                    }
                    for label in labels
                ],
                "count": len(labels),
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def create_label(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new label"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            name = args.get("name")
            email_address = args.get("email_address", "me")

            label_body = {
                "name": name,
                "labelListVisibility": args.get("visibility", "labelShow"),
                "messageListVisibility": args.get("message_visibility", "show"),
            }

            result = (
                service.users().labels().create(userId=email_address, body=label_body).execute()
            )

            logger.info(f"Created label '{name}' with id {result['id']}")

            return {
                "label_id": result["id"],
                "name": result["name"],
                "type": result.get("type", "user"),
                "status": "created",
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def apply_labels(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Apply labels to a message"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            message_id = args.get("message_id")
            add_labels = args.get("add_label_ids", [])
            remove_labels = args.get("remove_label_ids", [])
            email_address = args.get("email_address", "me")

            body: dict[str, list[str]] = {}
            if add_labels:
                body["addLabelIds"] = add_labels
            if remove_labels:
                body["removeLabelIds"] = remove_labels

            service.users().messages().modify(
                userId=email_address, id=message_id, body=body
            ).execute()

            logger.info(f"Modified labels on message {message_id}")

            return {
                "message_id": message_id,
                "added_labels": add_labels,
                "removed_labels": remove_labels,
                "status": "modified",
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def get_thread(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a full email thread with all messages"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            thread_id = args.get("thread_id")
            email_address = args.get("email_address", "me")

            thread = (
                service.users()
                .threads()
                .get(userId=email_address, id=thread_id, format="full")
                .execute()
            )

            messages = []
            for msg in thread.get("messages", []):
                headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
                messages.append(
                    {
                        "message_id": msg["id"],
                        "subject": headers.get("Subject", ""),
                        "from": headers.get("From", ""),
                        "to": headers.get("To", ""),
                        "date": headers.get("Date", ""),
                        "snippet": msg.get("snippet", ""),
                        "body": self._extract_body(msg),
                    }
                )

            return {
                "thread_id": thread["id"],
                "messages": messages,
                "message_count": len(messages),
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def list_threads(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List email threads"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            query = args.get("query", "")
            max_results = args.get("max_results", 20)
            email_address = args.get("email_address", "me")

            results = (
                service.users()
                .threads()
                .list(userId=email_address, q=query, maxResults=max_results)
                .execute()
            )

            threads = results.get("threads", [])

            return {
                "threads": [
                    {"thread_id": t["id"], "snippet": t.get("snippet", "")} for t in threads
                ],
                "count": len(threads),
                "next_page_token": results.get("nextPageToken"),
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error
