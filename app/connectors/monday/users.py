"""
Update, user, and group operations for Monday.com connector.
"""

from typing import Any, cast

from .items import ItemsMixin


class UsersMixin(ItemsMixin):
    """Mixin with update, user, and group operations."""

    def create_update(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Create an update (comment) on an item

        Args:
            item_id (required): Item ID
            body (required): Update text/body

        Returns:
            Created update
        """
        if not args.get("item_id"):
            raise ValueError("item_id is required")
        if not args.get("body"):
            raise ValueError("body is required")

        item_id = int(args["item_id"])

        mutation = """
        mutation ($itemId: ID!, $body: String!) {
            create_update(
                item_id: $itemId
                body: $body
            ) {
                id
                body
                creator {
                    id
                    name
                }
                created_at
            }
        }
        """

        variables = {"itemId": item_id, "body": args["body"]}

        data = self._execute_graphql(org_id, user_id, mutation, variables)

        return cast(dict[str, Any], data.get("create_update", {}))

    def get_item_updates(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get all updates (comments) for an item

        Args:
            item_id (required): Item ID
            limit: Max updates to return (default: 25)

        Returns:
            List of updates
        """
        if not args.get("item_id"):
            raise ValueError("item_id is required")

        item_id = int(args["item_id"])
        limit = int(args.get("limit", 25))

        query = """
        query ($itemIds: [ID!], $limit: Int) {
            items(ids: $itemIds) {
                updates(limit: $limit) {
                    id
                    body
                    creator {
                        id
                        name
                    }
                    created_at
                }
            }
        }
        """

        variables = {"itemIds": [item_id], "limit": limit}
        data = self._execute_graphql(org_id, user_id, query, variables)
        items = data.get("items", [])

        if not items:
            raise Exception(f"Item {item_id} not found")

        updates = items[0].get("updates", [])

        return {"count": len(updates), "updates": updates}

    def get_users(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get users in the account

        Args:
            kind: Filter by user kind (all, non_guests, guests, non_pending)
            limit: Max users to return (default: 50)

        Returns:
            List of users
        """
        kind = args.get("kind", "all")
        limit = args.get("limit", 50)

        query = f"""
        query {{
            users(kind: {kind}, limit: {limit}) {{
                id
                name
                email
                enabled
                is_guest
                is_pending
                title
                photo_thumb
            }}
        }}
        """

        data = self._execute_graphql(org_id, user_id, query)
        users = data.get("users", [])

        return {"count": len(users), "users": users}

    def get_current_user(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get the currently authenticated user

        Returns:
            Current user details
        """
        query = """
        query {
            me {
                id
                name
                email
                title
                account {
                    id
                    name
                    slug
                }
            }
        }
        """

        data = self._execute_graphql(org_id, user_id, query)

        return cast(dict[str, Any], data.get("me", {}))

    def create_group(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new group on a board

        Args:
            board_id (required): Board ID
            group_name (required): Group name

        Returns:
            Created group
        """
        if not args.get("board_id"):
            raise ValueError("board_id is required")
        if not args.get("group_name"):
            raise ValueError("group_name is required")

        board_id = int(args["board_id"])

        mutation = """
        mutation ($boardId: ID!, $groupName: String!) {
            create_group(
                board_id: $boardId
                group_name: $groupName
            ) {
                id
                title
                color
            }
        }
        """

        variables = {"boardId": board_id, "groupName": args["group_name"]}

        data = self._execute_graphql(org_id, user_id, mutation, variables)

        return cast(dict[str, Any], data.get("create_group", {}))
