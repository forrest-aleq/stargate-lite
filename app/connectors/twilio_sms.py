"""
Twilio SMS connector for Stargate Lite
Handles text messaging (SMS/MMS)
Uses Twilio API (October 2025)
"""

import os
from base64 import b64encode
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class TwilioSMSConnector:
    """Twilio API connector for SMS messaging"""

    BASE_URL = "https://api.twilio.com/2010-04-01"

    def __init__(self) -> None:
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

    def _get_auth_header(self) -> dict[str, str]:
        """Generate HTTP Basic Auth header"""
        credentials = f"{self.account_sid}:{self.auth_token}"
        encoded = b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _make_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/Accounts/{self.account_sid}{endpoint}"
        headers = self._get_auth_header()

        if method not in ["GET", "POST"]:
            raise ValueError(f"Unsupported method: {method}")

        if method == "GET":
            return http_client.get(url=url, service="twilio", headers=headers, params=data)
        else:
            # POST - Twilio uses form-encoded data, not JSON
            return http_client.post(url=url, service="twilio", headers=headers, data=data)

    def send_sms(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send an SMS message"""
        message_data = {
            "From": args.get("from_number", self.from_number),
            "To": args.get("to_number"),
            "Body": args.get("message"),
        }

        # Optional: MMS with media
        if args.get("media_urls"):
            for idx, url in enumerate(args["media_urls"][:10]):  # Max 10
                message_data[f"MediaUrl{idx}"] = url

        # Optional: schedule message
        if args.get("send_at"):
            message_data["SendAt"] = args["send_at"]  # ISO 8601 format

        # Optional: status callback
        if args.get("status_callback"):
            message_data["StatusCallback"] = args["status_callback"]

        result = self._make_request("POST", "/Messages.json", message_data)

        return {
            "message_sid": result.get("sid"),
            "status": result.get("status"),
            "to": result.get("to"),
            "from": result.get("from"),
            "body": result.get("body"),
            "num_segments": result.get("num_segments"),  # For long messages
            "price": result.get("price"),
            "direction": result.get("direction"),
        }

    def get_message(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get details of a specific message"""
        message_sid = args.get("message_sid")

        result = self._make_request("GET", f"/Messages/{message_sid}.json")

        return {
            "message_sid": result.get("sid"),
            "status": result.get("status"),
            "to": result.get("to"),
            "from": result.get("from"),
            "body": result.get("body"),
            "date_sent": result.get("date_sent"),
            "price": result.get("price"),
            "error_code": result.get("error_code"),
            "error_message": result.get("error_message"),
        }

    def list_messages(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List recent messages"""
        params = {"PageSize": args.get("page_size", 50)}

        # Optional filters
        if args.get("to"):
            params["To"] = args["to"]
        if args.get("from"):
            params["From"] = args["from"]
        if args.get("date_sent"):
            params["DateSent"] = args["date_sent"]

        result = self._make_request("GET", "/Messages.json", params)

        return {
            "messages": [
                {
                    "message_sid": msg["sid"],
                    "to": msg["to"],
                    "from": msg["from"],
                    "body": msg["body"],
                    "status": msg["status"],
                    "date_sent": msg.get("date_sent"),
                }
                for msg in result.get("messages", [])
            ],
            "page": result.get("page"),
            "page_size": result.get("page_size"),
        }

    def delete_message(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a message"""
        message_sid = args.get("message_sid")

        # Twilio DELETE returns 204 No Content on success
        url = f"{self.BASE_URL}/Accounts/{self.account_sid}/Messages/{message_sid}.json"
        headers = self._get_auth_header()

        response = http_client.request(
            method="DELETE", url=url, service="twilio", headers=headers, parse_json=False
        )

        if response.status_code != 204:
            raise Exception(f"Twilio API error: {response.status_code} - {response.text}")

        return {"message_sid": message_sid, "status": "deleted"}

    def get_incoming_messages(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get incoming messages (received)"""
        params = {
            "PageSize": args.get("page_size", 50),
            "To": args.get("to_number", self.from_number),  # Messages sent to your Twilio number
        }

        result = self._make_request("GET", "/Messages.json", params)

        return {
            "messages": [
                {
                    "message_sid": msg["sid"],
                    "from": msg["from"],
                    "to": msg["to"],
                    "body": msg["body"],
                    "date_sent": msg.get("date_sent"),
                    "num_media": msg.get("num_media", "0"),
                }
                for msg in result.get("messages", [])
                if msg.get("direction") == "inbound"
            ]
        }

    def send_mms(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send an MMS message with media"""
        return self.send_sms(org_id, user_id, args)  # Same endpoint, just includes MediaUrl

    def schedule_message(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Schedule an SMS message for future delivery"""
        message_data = {
            "From": args.get("from_number", self.from_number),
            "To": args.get("to_number"),
            "Body": args.get("message"),
            "SendAt": args.get("send_at"),  # ISO 8601 datetime
            # Required for scheduled messages
            "MessagingServiceSid": args.get("messaging_service_sid"),
        }

        result = self._make_request("POST", "/Messages.json", message_data)

        return {
            "message_sid": result.get("sid"),
            "status": result.get("status"),
            "send_at": result.get("send_at"),
        }
