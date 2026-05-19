"""
Item and column value operations for Monday.com connector.
"""

import json
from typing import Any, cast

from .boards import BoardsMixin


class ItemsMixin(BoardsMixin):
    """Mixin with item and column value operations."""

    def create_item(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new item on a board

        Args:
            board_id (required): Board ID
            item_name (required): Item name
            group_id: Group ID to add item to
            column_values: JSON string of column values
                Example: {"status": {"label": "Done"}, "date": {"date": "2025-01-15"}}

        Returns:
            Created item with id, name, url

        Example:
            {
                "board_id": "1234567890",
                "item_name": "Review Q4 expenses",
                "group_id": "topics",
                "column_values": {"status": {"label": "In Progress"}}
            }
        """
        if not args.get("board_id"):
            raise ValueError("board_id is required")
        if not args.get("item_name"):
            raise ValueError("item_name is required")

        board_id = args["board_id"]
        item_name = args["item_name"]

        # Build mutation with optional parameters
        mutation_args = [f"board_id: {board_id}", "item_name: $itemName"]

        if args.get("group_id"):
            mutation_args.append(f'group_id: "{args["group_id"]}"')

        if args.get("column_values"):
            mutation_args.append("column_values: $columnValues")

        mutation = f"""
        mutation ($itemName: String!, $columnValues: JSON) {{
            create_item({", ".join(mutation_args)}) {{
                id
                name
                url: relative_link
                state
                created_at
            }}
        }}
        """

        variables: dict[str, Any] = {"itemName": item_name}

        if args.get("column_values"):
            variables["columnValues"] = json.dumps(args["column_values"])

        data = self._execute_graphql(org_id, user_id, mutation, variables)

        return cast(dict[str, Any], data.get("create_item", {}))

    def get_item(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get details of a specific item

        Args:
            item_id (required): Item ID

        Returns:
            Item with all column values and metadata
        """
        if not args.get("item_id"):
            raise ValueError("item_id is required")

        item_id = args["item_id"]

        query = f"""
        query {{
            items(ids: {item_id}) {{
                id
                name
                state
                url: relative_link
                created_at
                updated_at
                creator {{
                    id
                    name
                }}
                column_values {{
                    id
                    title
                    type
                    text
                    value
                }}
                board {{
                    id
                    name
                }}
                group {{
                    id
                    title
                }}
            }}
        }}
        """

        data = self._execute_graphql(org_id, user_id, query)
        items = data.get("items", [])

        if not items:
            raise Exception(f"Item {item_id} not found")

        return cast(dict[str, Any], items[0])

    def list_items(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        List items on a board

        Args:
            board_id (required): Board ID
            limit: Max items per page (default: 50, max: 100)
            cursor: Pagination cursor for next page

        Returns:
            Items with pagination cursor
        """
        if not args.get("board_id"):
            raise ValueError("board_id is required")

        board_id = args["board_id"]
        limit = min(args.get("limit", 50), 100)

        # Build items_page query with cursor if provided
        cursor_arg = f', cursor: "{args["cursor"]}"' if args.get("cursor") else ""

        query = f"""
        query {{
            boards(ids: {board_id}) {{
                items_page(limit: {limit}{cursor_arg}) {{
                    cursor
                    items {{
                        id
                        name
                        state
                        url: relative_link
                        created_at
                        column_values {{
                            id
                            title
                            text
                        }}
                    }}
                }}
            }}
        }}
        """

        data = self._execute_graphql(org_id, user_id, query)
        boards = data.get("boards", [])

        if not boards:
            raise Exception(f"Board {board_id} not found")

        items_page = boards[0].get("items_page", {})

        return {
            "count": len(items_page.get("items", [])),
            "items": items_page.get("items", []),
            "cursor": items_page.get("cursor"),
        }

    def update_item(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Update an item's name

        Args:
            item_id (required): Item ID
            item_name (required): New item name

        Returns:
            Updated item

        Note: To update column values, use change_column_value or change_multiple_column_values
        """
        if not args.get("item_id"):
            raise ValueError("item_id is required")
        if not args.get("item_name"):
            raise ValueError("item_name is required")

        item_id = args["item_id"]

        mutation = f"""
        mutation ($itemName: String!) {{
            change_simple_column_value(
                item_id: {item_id}
                column_id: "name"
                value: $itemName
            ) {{
                id
                name
            }}
        }}
        """

        variables = {"itemName": args["item_name"]}

        data = self._execute_graphql(org_id, user_id, mutation, variables)

        return cast(dict[str, Any], data.get("change_simple_column_value", {}))

    def change_column_value(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Change a single column value for an item

        Args:
            board_id (required): Board ID
            item_id (required): Item ID
            column_id (required): Column ID
            value (required): JSON value for the column
                Example: {"label": "Done"} for status
                Example: {"date": "2025-01-15"} for date
                Example: {"text": "John Doe"} for text

        Returns:
            Updated item

        Example:
            {
                "board_id": "1234567890",
                "item_id": "9876543210",
                "column_id": "status",
                "value": {"label": "Done"}
            }
        """
        if not args.get("board_id"):
            raise ValueError("board_id is required")
        if not args.get("item_id"):
            raise ValueError("item_id is required")
        if not args.get("column_id"):
            raise ValueError("column_id is required")
        if "value" not in args:
            raise ValueError("value is required")

        board_id = args["board_id"]
        item_id = args["item_id"]
        column_id = args["column_id"]

        mutation = f"""
        mutation ($value: JSON!) {{
            change_column_value(
                board_id: {board_id}
                item_id: {item_id}
                column_id: "{column_id}"
                value: $value
            ) {{
                id
                name
            }}
        }}
        """

        variables = {"value": json.dumps(args["value"])}

        data = self._execute_graphql(org_id, user_id, mutation, variables)

        return cast(dict[str, Any], data.get("change_column_value", {}))

    def change_multiple_column_values(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Change multiple column values for an item at once

        Args:
            board_id (required): Board ID
            item_id (required): Item ID
            column_values (required): Dictionary of column_id -> value
                Example: {
                    "status": {"label": "Done"},
                    "date": {"date": "2025-01-15"},
                    "text": "Review complete"
                }

        Returns:
            Updated item
        """
        if not args.get("board_id"):
            raise ValueError("board_id is required")
        if not args.get("item_id"):
            raise ValueError("item_id is required")
        if not args.get("column_values"):
            raise ValueError("column_values is required")

        board_id = args["board_id"]
        item_id = args["item_id"]

        mutation = f"""
        mutation ($columnValues: JSON!) {{
            change_multiple_column_values(
                board_id: {board_id}
                item_id: {item_id}
                column_values: $columnValues
            ) {{
                id
                name
            }}
        }}
        """

        variables = {"columnValues": json.dumps(args["column_values"])}

        data = self._execute_graphql(org_id, user_id, mutation, variables)

        return cast(dict[str, Any], data.get("change_multiple_column_values", {}))
