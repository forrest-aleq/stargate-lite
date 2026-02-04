"""
Slack channels mixin for channel and user operations.
"""

from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .messaging import MessagingMixin


class ChannelsMixin(MessagingMixin):
    """Mixin with channel and user operations."""

    def upload_file(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Upload a file to Slack"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channels = args.get("channels")
            file_content = args.get("content")
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

    def create_channel(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            name = args.get("name")
            is_private = args.get("is_private", False)

            response = client.conversations_create(
                name=name, is_private=is_private
            )

            return {
                "channel_id": response["channel"]["id"],
                "channel_name": response["channel"]["name"],
                "is_private": response["channel"]["is_private"],
                "status": "created",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def invite_to_channel(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Invite users to a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            user_ids = args.get("user_ids")

            response = client.conversations_invite(
                channel=channel_id, users=user_ids
            )

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

            response = client.conversations_history(
                channel=channel_id, limit=limit
            )

            messages = [
                {
                    "text": msg.get("text"),
                    "user": msg.get("user"),
                    "timestamp": msg.get("ts"),
                    "type": msg.get("type"),
                }
                for msg in response["messages"]
            ]

            return {
                "channel_id": channel_id,
                "messages": messages,
                "count": len(messages),
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def list_channels(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
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

    def get_channel_info(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get detailed information about a channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")

            response = client.conversations_info(channel=channel_id)
            ch = response["channel"]

            return {
                "channel_id": ch["id"],
                "name": ch.get("name"),
                "is_private": ch.get("is_private", False),
                "is_archived": ch.get("is_archived", False),
                "topic": ch.get("topic", {}).get("value"),
                "purpose": ch.get("purpose", {}).get("value"),
                "num_members": ch.get("num_members", 0),
                "created": ch.get("created"),
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def archive_channel(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Archive a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")

            client.conversations_archive(channel=channel_id)

            return {"channel_id": channel_id, "status": "archived"}

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def set_channel_topic(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Set the topic for a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            topic = args.get("topic", "")

            response = client.conversations_setTopic(
                channel=channel_id, topic=topic
            )

            return {
                "channel_id": response["channel"]["id"],
                "topic": response["channel"]["topic"]["value"],
                "status": "updated",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def set_channel_purpose(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Set the purpose for a Slack channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            purpose = args.get("purpose", "")

            response = client.conversations_setPurpose(
                channel=channel_id, purpose=purpose
            )

            return {
                "channel_id": response["channel"]["id"],
                "purpose": response["channel"]["purpose"]["value"],
                "status": "updated",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def list_users(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
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
                    "display_name": user.get("profile", {}).get(
                        "display_name"
                    ),
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

    def get_user_info(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
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
