"""
List, space, comment, and team operations for ClickUp connector.
"""

from typing import Any

from .tasks import TasksMixin


class ListsSpacesMixin(TasksMixin):
    """Mixin with list, space, comment, and team operations."""

    def get_list(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get details of a specific list

        Args:
            list_id (required): List ID

        Returns:
            List object with name, folder, space, statuses
        """
        if not args.get("list_id"):
            raise ValueError("list_id is required")

        list_id = args["list_id"]

        result = self._make_request(org_id, user_id, "GET", f"list/{list_id}")

        return {
            "list_id": result.get("id"),
            "name": result.get("name"),
            "folder": {
                "id": result.get("folder", {}).get("id"),
                "name": result.get("folder", {}).get("name"),
            },
            "space": {
                "id": result.get("space", {}).get("id"),
                "name": result.get("space", {}).get("name"),
            },
            "statuses": [
                {"status": s.get("status"), "type": s.get("type"), "color": s.get("color")}
                for s in result.get("statuses", [])
            ],
            "task_count": result.get("task_count"),
        }

    def get_lists_in_folder(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Get all lists in a folder

        Args:
            folder_id (required): Folder ID
            archived: Include archived lists (default: false)

        Returns:
            Array of lists
        """
        if not args.get("folder_id"):
            raise ValueError("folder_id is required")

        folder_id = args["folder_id"]
        params = {}

        if args.get("archived"):
            params["archived"] = "true"

        result = self._make_request(
            org_id, user_id, "GET", f"folder/{folder_id}/list", params=params
        )

        lists = result.get("lists", [])

        return {
            "count": len(lists),
            "lists": [
                {
                    "list_id": item.get("id"),
                    "name": item.get("name"),
                    "task_count": item.get("task_count"),
                }
                for item in lists
            ],
        }

    def get_lists_in_space(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get folderless lists in a space

        Args:
            space_id (required): Space ID
            archived: Include archived lists (default: false)

        Returns:
            Array of lists
        """
        if not args.get("space_id"):
            raise ValueError("space_id is required")

        space_id = args["space_id"]
        params = {}

        if args.get("archived"):
            params["archived"] = "true"

        result = self._make_request(org_id, user_id, "GET", f"space/{space_id}/list", params=params)

        lists = result.get("lists", [])

        return {
            "count": len(lists),
            "lists": [
                {
                    "list_id": item.get("id"),
                    "name": item.get("name"),
                    "task_count": item.get("task_count"),
                }
                for item in lists
            ],
        }

    def get_spaces(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get all spaces in a workspace (team)

        Args:
            team_id (required): Team/Workspace ID
            archived: Include archived spaces (default: false)

        Returns:
            Array of spaces
        """
        if not args.get("team_id"):
            raise ValueError("team_id is required (workspace ID)")

        team_id = args["team_id"]
        params = {}

        if args.get("archived"):
            params["archived"] = "true"

        result = self._make_request(org_id, user_id, "GET", f"team/{team_id}/space", params=params)

        spaces = result.get("spaces", [])

        return {
            "count": len(spaces),
            "spaces": [
                {
                    "space_id": s.get("id"),
                    "name": s.get("name"),
                    "private": s.get("private"),
                    "statuses": [st.get("status") for st in s.get("statuses", [])],
                }
                for s in spaces
            ],
        }

    def get_space(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get details of a specific space

        Args:
            space_id (required): Space ID

        Returns:
            Space object with folders, lists, statuses
        """
        if not args.get("space_id"):
            raise ValueError("space_id is required")

        space_id = args["space_id"]

        result = self._make_request(org_id, user_id, "GET", f"space/{space_id}")

        return {
            "space_id": result.get("id"),
            "name": result.get("name"),
            "private": result.get("private"),
            "statuses": [
                {"status": s.get("status"), "type": s.get("type"), "color": s.get("color")}
                for s in result.get("statuses", [])
            ],
            "features": result.get("features"),
        }

    def create_comment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Create a comment on a task

        Args:
            task_id (required): Task ID
            comment_text (required): Comment text
            assignee: User ID to assign with comment
            notify_all: Notify all assignees (default: false)

        Returns:
            Created comment object
        """
        if not args.get("task_id"):
            raise ValueError("task_id is required")
        if not args.get("comment_text"):
            raise ValueError("comment_text is required")

        task_id = args["task_id"]

        comment_data: dict[str, Any] = {"comment_text": args["comment_text"]}

        if args.get("assignee"):
            comment_data["assignee"] = args["assignee"]
        if args.get("notify_all"):
            comment_data["notify_all"] = args["notify_all"]

        result = self._make_request(
            org_id, user_id, "POST", f"task/{task_id}/comment", data=comment_data
        )

        # ClickUp create comment API returns only id, hist_id, and date at top level
        return {
            "comment_id": result.get("id"),
            "hist_id": result.get("hist_id"),
            "date": result.get("date"),
        }

    def get_task_comments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get all comments on a task

        Args:
            task_id (required): Task ID

        Returns:
            Array of comments
        """
        if not args.get("task_id"):
            raise ValueError("task_id is required")

        task_id = args["task_id"]

        result = self._make_request(org_id, user_id, "GET", f"task/{task_id}/comment")

        comments = result.get("comments", [])

        return {
            "count": len(comments),
            "comments": [
                {
                    "comment_id": c.get("id"),
                    "comment_text": c.get("comment_text"),
                    "user": c.get("user", {}).get("username"),
                    "date": c.get("date"),
                }
                for c in comments
            ],
        }

    def get_authorized_teams(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Get all workspaces (teams) the authenticated user has access to

        Returns:
            Array of teams/workspaces
        """
        result = self._make_request(org_id, user_id, "GET", "team")

        teams = result.get("teams", [])

        return {
            "count": len(teams),
            "teams": [
                {
                    "team_id": t.get("id"),
                    "name": t.get("name"),
                    "color": t.get("color"),
                    "avatar": t.get("avatar"),
                }
                for t in teams
            ],
        }
