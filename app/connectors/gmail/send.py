"""
Send and draft operations for Gmail connector.
"""

import base64
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import GmailBase


class SendMixin(GmailBase):
    """Mixin with send and draft operations."""

    def send_email(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send an email via Gmail"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            # Create message
            to_addr = args.get("to")
            subject = args.get("subject")
            if not isinstance(to_addr, str) or not isinstance(subject, str):
                raise ValueError("to and subject are required")
            message = MIMEMultipart()
            message["To"] = to_addr
            message["Subject"] = subject

            if args.get("cc"):
                message["Cc"] = args["cc"]
            if args.get("bcc"):
                message["Bcc"] = args["bcc"]

            # Add body
            body = args.get("body", "")
            is_html = args.get("is_html", False)
            message.attach(MIMEText(body, "html" if is_html else "plain"))

            # Add attachments if any
            if args.get("attachments"):
                for attachment in args["attachments"]:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(base64.b64decode(attachment["content"]))
                    encoders.encode_base64(part)
                    # Use keyword arg form to prevent header injection
                    part.add_header(
                        "Content-Disposition", "attachment", filename=attachment["filename"]
                    )
                    message.attach(part)

            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {"raw": raw_message}

            result = service.users().messages().send(userId="me", body=send_message).execute()

            return {
                "message_id": result["id"],
                "thread_id": result.get("threadId"),
                "status": "sent",
                "to": args.get("to"),
                "subject": args.get("subject"),
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def create_draft(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a draft email"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            # Create message
            to_addr = args.get("to")
            subject = args.get("subject")
            if not isinstance(to_addr, str) or not isinstance(subject, str):
                raise ValueError("to and subject are required")
            message = MIMEText(args.get("body", ""))
            message["To"] = to_addr
            message["Subject"] = subject

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            draft = (
                service.users()
                .drafts()
                .create(userId="me", body={"message": {"raw": raw_message}})
                .execute()
            )

            return {
                "draft_id": draft["id"],
                "message_id": draft["message"]["id"],
                "status": "draft",
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def reply_to_email(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Reply to an email in the same thread"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            thread_id = args.get("thread_id")
            to_addr = args.get("to")
            body_text = args.get("body", "")
            subject = args.get("subject", "")
            is_html = args.get("is_html", False)

            if not isinstance(to_addr, str):
                raise ValueError("to is required")

            # Create reply message
            message = MIMEText(body_text, "html" if is_html else "plain")
            message["To"] = to_addr
            message["Subject"] = subject if subject else "Re: "

            # Encode and send as reply to thread
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_body = {"raw": raw_message, "threadId": thread_id}

            result = service.users().messages().send(userId="me", body=send_body).execute()

            return {
                "message_id": result["id"],
                "thread_id": result.get("threadId"),
                "status": "sent",
                "to": to_addr,
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def forward_email(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Forward an email to another recipient"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("gmail", "v1", credentials=creds)

            message_id = args.get("message_id")
            to_addr = args.get("to")
            additional_message = args.get("message", "")

            if not isinstance(to_addr, str) or not isinstance(message_id, str):
                raise ValueError("to and message_id are required")

            # Get original message
            original = (
                service.users().messages().get(userId="me", id=message_id, format="full").execute()
            )

            headers = {h["name"]: h["value"] for h in original["payload"].get("headers", [])}
            original_subject = headers.get("Subject", "")
            original_from = headers.get("From", "")
            original_date = headers.get("Date", "")

            # Extract original body
            original_body = self._extract_forward_body(original)

            # Build forward message
            forward_body = (
                f"{additional_message}\n\n"
                f"---------- Forwarded message ----------\n"
                f"From: {original_from}\n"
                f"Date: {original_date}\n"
                f"Subject: {original_subject}\n\n"
                f"{original_body}"
            )

            message = MIMEText(forward_body)
            message["To"] = to_addr
            message["Subject"] = f"Fwd: {original_subject}"

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_body = {"raw": raw_message}

            result = service.users().messages().send(userId="me", body=send_body).execute()

            return {
                "message_id": result["id"],
                "thread_id": result.get("threadId"),
                "status": "forwarded",
                "to": to_addr,
                "original_message_id": message_id,
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}") from error

    def _extract_forward_body(self, message: dict[str, Any]) -> str:
        """Extract body for forwarding (plain text preferred)"""
        payload = message.get("payload", {})

        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", "ignore")

        def get_text_from_parts(parts: list[dict[str, Any]]) -> str:
            for part in parts:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", "ignore")
                if "parts" in part:
                    nested = get_text_from_parts(part["parts"])
                    if nested:
                        return nested
            return ""

        return get_text_from_parts(payload.get("parts", []))
