"""
Slack connector for Stargate Lite
Handles OAuth 2.0 and messaging operations
"""

import os
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)


class SlackConnector:
    """Slack API connector"""

    TOKEN_URL = "https://slack.com/api/oauth.v2.access"

    def __init__(self) -> None:
        self.client_id = os.getenv("SLACK_CLIENT_ID")
        self.client_secret = os.getenv("SLACK_CLIENT_SECRET")

    def _get_access_token(self, org_id: str, user_id: str) -> str:
        """Get Slack access token"""
        cred = CredentialManager.get_credential(org_id, user_id, "slack")

        if not cred:
            raise ValueError(f"No Slack credentials found for org_id={org_id}, user_id={user_id}")

        # Slack tokens don't expire in the same way as other OAuth tokens
        # They remain valid until revoked
        return str(cred["access_token"])

    def send_message(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send a message to a Slack channel or user"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel = args.get("channel")  # Can be channel ID or @username
            text = args.get("text")
            blocks = args.get("blocks")  # For rich formatting
            thread_ts = args.get("thread_ts")  # For replying to threads

            response = client.chat_postMessage(
                channel=channel, text=text, blocks=blocks, thread_ts=thread_ts
            )

            return {
                "message_id": response["ts"],
                "channel": response["channel"],
                "text": text,
                "status": "sent",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def send_direct_message(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a direct message to a Slack user"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            # Get or open DM channel with user
            slack_user_id = args.get("user_id")
            text = args.get("text")

            # Open a DM channel
            dm_response = client.conversations_open(users=slack_user_id)
            channel_id = dm_response["channel"]["id"]

            # Send message
            response = client.chat_postMessage(channel=channel_id, text=text)

            return {
                "message_id": response["ts"],
                "channel": channel_id,
                "text": text,
                "status": "sent",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def upload_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Upload a file to Slack"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channels = args.get("channels")  # Comma-separated channel IDs
            file_content = args.get("content")  # Base64 or raw content
            filename = args.get("filename")
            title = args.get("title", filename)
            initial_comment = args.get("initial_comment")

            response = client.files_upload_v2(
                channels=channels,
                content=file_content,
                filename=filename,
                title=title,
                initial_comment=initial_comment,
            )

            return {
                "file_id": response["file"]["id"],
                "filename": response["file"]["name"],
                "url": response["file"]["url_private"],
                "status": "uploaded",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def create_channel(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            name = args.get("name")
            is_private = args.get("is_private", False)

            response = client.conversations_create(name=name, is_private=is_private)

            return {
                "channel_id": response["channel"]["id"],
                "channel_name": response["channel"]["name"],
                "is_private": response["channel"]["is_private"],
                "status": "created",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def invite_to_channel(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Invite users to a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            user_ids = args.get("user_ids")  # Comma-separated user IDs

            response = client.conversations_invite(channel=channel_id, users=user_ids)

            return {
                "channel_id": response["channel"]["id"],
                "invited_users": user_ids,
                "status": "invited",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def get_channel_history(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get message history from a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            limit = args.get("limit", 100)

            response = client.conversations_history(channel=channel_id, limit=limit)

            messages = [
                {
                    "text": msg.get("text"),
                    "user": msg.get("user"),
                    "timestamp": msg.get("ts"),
                    "type": msg.get("type"),
                }
                for msg in response["messages"]
            ]

            return {"channel_id": channel_id, "messages": messages, "count": len(messages)}

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def list_channels(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all channels in the workspace"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            types = args.get("types", "public_channel,private_channel")
            limit = args.get("limit", 100)

            response = client.conversations_list(types=types, limit=limit)

            channels = [
                {
                    "channel_id": ch["id"],
                    "name": ch["name"],
                    "is_private": ch.get("is_private", False),
                    "is_archived": ch.get("is_archived", False),
                    "num_members": ch.get("num_members", 0),
                }
                for ch in response["channels"]
            ]

            return {"channels": channels, "count": len(channels)}

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def archive_channel(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Archive a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")

            client.conversations_archive(channel=channel_id)

            return {"channel_id": channel_id, "status": "archived"}

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def set_channel_topic(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Set the topic for a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            topic = args.get("topic", "")

            response = client.conversations_setTopic(channel=channel_id, topic=topic)

            return {
                "channel_id": response["channel"]["id"],
                "topic": response["channel"]["topic"]["value"],
                "status": "updated",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def add_reaction(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Add a reaction to a message"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            timestamp = args.get("timestamp")
            name = args.get("name")  # Emoji name without colons

            client.reactions_add(channel=channel_id, timestamp=timestamp, name=name)

            return {
                "channel_id": channel_id,
                "timestamp": timestamp,
                "reaction": name,
                "status": "added",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def remove_reaction(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Remove a reaction from a message"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            timestamp = args.get("timestamp")
            name = args.get("name")

            client.reactions_remove(channel=channel_id, timestamp=timestamp, name=name)

            return {
                "channel_id": channel_id,
                "timestamp": timestamp,
                "reaction": name,
                "status": "removed",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def list_users(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all users in the workspace"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            limit = args.get("limit", 100)

            response = client.users_list(limit=limit)

            users = [
                {
                    "user_id": user["id"],
                    "name": user.get("name"),
                    "real_name": user.get("real_name"),
                    "display_name": user.get("profile", {}).get("display_name"),
                    "email": user.get("profile", {}).get("email"),
                    "is_bot": user.get("is_bot", False),
                    "is_admin": user.get("is_admin", False),
                }
                for user in response["members"]
                if not user.get("deleted", False)
            ]

            return {"users": users, "count": len(users)}

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def get_user_info(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get detailed information about a user"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            slack_user_id = args.get("user_id")

            response = client.users_info(user=slack_user_id)
            user = response["user"]

            return {
                "user_id": user["id"],
                "name": user.get("name"),
                "real_name": user.get("real_name"),
                "display_name": user.get("profile", {}).get("display_name"),
                "email": user.get("profile", {}).get("email"),
                "title": user.get("profile", {}).get("title"),
                "phone": user.get("profile", {}).get("phone"),
                "is_bot": user.get("is_bot", False),
                "is_admin": user.get("is_admin", False),
                "timezone": user.get("tz"),
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def search_messages(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search for messages in the workspace"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            query = args.get("query")
            count = args.get("count", 20)
            sort = args.get("sort", "timestamp")
            sort_dir = args.get("sort_dir", "desc")

            response = client.search_messages(
                query=query, count=count, sort=sort, sort_dir=sort_dir
            )

            matches = response.get("messages", {}).get("matches", [])
            messages = [
                {
                    "text": msg.get("text"),
                    "user": msg.get("user"),
                    "username": msg.get("username"),
                    "timestamp": msg.get("ts"),
                    "channel_id": msg.get("channel", {}).get("id"),
                    "channel_name": msg.get("channel", {}).get("name"),
                    "permalink": msg.get("permalink"),
                }
                for msg in matches
            ]

            return {
                "query": query,
                "messages": messages,
                "count": len(messages),
                "total": response.get("messages", {}).get("total", 0),
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e
