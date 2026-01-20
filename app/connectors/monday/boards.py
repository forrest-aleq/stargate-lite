"""
Board operations for Monday.com connector.
"""

from typing import Any, cast

from .base import MondayBase


class BoardsMixin(MondayBase):
    """Mixin with board operations."""

    def get_boards(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get all boards accessible to the user

        Args:
            limit: Maximum number of boards to return (default: 25)
            board_kind: Filter by board kind (public, private, share)
            state: Filter by state (active, archived, deleted, all)

        Returns:
            List of boards with id, name, description
        """
        limit = args.get("limit", 25)

        # Build query with optional filters
        filters = []
        if args.get("board_kind"):
            filters.append(f'board_kind: {args["board_kind"]}')
        if args.get("state"):
            filters.append(f'state: {args["state"]}')

        filter_str = f"({', '.join(filters)})" if filters else ""

        query = f"""
        query {{
            boards(limit: {limit} {filter_str}) {{
                id
                name
                description
                state
                board_kind
                item_count: items_count
                owner {{
                    id
                    name
                }}
            }}
        }}
        """

        data = self._execute_graphql(org_id, user_id, query)
        boards = data.get("boards", [])

        return {"count": len(boards), "boards": boards}

    def get_board(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get details of a specific board

        Args:
            board_id (required): Board ID

        Returns:
            Board with columns, groups, and metadata
        """
        if not args.get("board_id"):
            raise ValueError("board_id is required")

        board_id = args["board_id"]

        query = f"""
        query {{
            boards(ids: {board_id}) {{
                id
                name
                description
                state
                board_kind
                item_count: items_count
                columns {{
                    id
                    title
                    type
                    settings_str
                }}
                groups {{
                    id
                    title
                    color
                }}
                owner {{
                    id
                    name
                    email
                }}
            }}
        }}
        """

        data = self._execute_graphql(org_id, user_id, query)
        boards = data.get("boards", [])

        if not boards:
            raise Exception(f"Board {board_id} not found")

        return cast(dict[str, Any], boards[0])
