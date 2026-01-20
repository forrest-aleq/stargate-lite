"""
Task operations for ClickUp connector.
"""

from typing import Any

from .base import ClickUpBase


class TasksMixin(ClickUpBase):
    """Mixin with task operations."""

    def create_task(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new task in ClickUp

        Args:
            list_id (required): ID of the list to create task in
            name (required): Task name
            description: Task description
            assignees: List of user IDs to assign
            priority: 1 (urgent), 2 (high), 3 (normal), 4 (low)
            due_date: Due date timestamp (milliseconds)
            start_date: Start date timestamp (milliseconds)
            status: Status name
            tags: List of tag names

        Returns:
            Created task object with id, name, url, status, assignees
        """
        if not args.get("list_id"):
            raise ValueError("list_id is required to create a task")
        if not args.get("name"):
            raise ValueError("name is required to create a task")

        list_id = args["list_id"]

        # Build task data
        task_data: dict[str, Any] = {"name": args["name"]}

        if args.get("description"):
            task_data["description"] = args["description"]
        if args.get("assignees"):
            task_data["assignees"] = args["assignees"]
        if args.get("priority"):
            task_data["priority"] = args["priority"]
        if args.get("due_date"):
            task_data["due_date"] = args["due_date"]
        if args.get("start_date"):
            task_data["start_date"] = args["start_date"]
        if args.get("status"):
            task_data["status"] = args["status"]
        if args.get("tags"):
            task_data["tags"] = args["tags"]

        result = self._make_request(org_id, user_id, "POST", f"list/{list_id}/task", data=task_data)

        return {
            "task_id": result.get("id"),
            "name": result.get("name"),
            "url": result.get("url"),
            "status": result.get("status", {}).get("status"),
            "assignees": [a.get("username") for a in result.get("assignees", [])],
            "due_date": result.get("due_date"),
            "priority": result.get("priority"),
        }

    def get_task(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get details of a specific task

        Args:
            task_id (required): Task ID
            include_subtasks: Include subtasks (default: false)

        Returns:
            Full task object with all details
        """
        if not args.get("task_id"):
            raise ValueError("task_id is required")

        task_id = args["task_id"]
        params = {}

        if args.get("include_subtasks"):
            params["include_subtasks"] = "true"

        result = self._make_request(org_id, user_id, "GET", f"task/{task_id}", params=params)

        return {
            "task_id": result.get("id"),
            "name": result.get("name"),
            "description": result.get("description"),
            "status": result.get("status", {}).get("status"),
            "assignees": [
                {"id": a.get("id"), "username": a.get("username"), "email": a.get("email")}
                for a in result.get("assignees", [])
            ],
            "due_date": result.get("due_date"),
            "start_date": result.get("start_date"),
            "priority": (
                result.get("priority", {}).get("priority")
                if isinstance(result.get("priority"), dict)
                else result.get("priority")
            ),
            "tags": [t.get("name") for t in result.get("tags", [])],
            "url": result.get("url"),
            "date_created": result.get("date_created"),
            "date_updated": result.get("date_updated"),
        }

    def update_task(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing task

        Args:
            task_id (required): Task ID
            name: New task name
            description: New description
            status: New status name
            priority: New priority (1-4)
            assignees: New assignee list (replaces existing)
            due_date: New due date timestamp
            start_date: New start date timestamp

        Returns:
            Updated task object
        """
        if not args.get("task_id"):
            raise ValueError("task_id is required")

        task_id = args["task_id"]

        # Build update data (only include fields that are provided)
        update_data: dict[str, Any] = {}

        if "name" in args:
            update_data["name"] = args["name"]
        if "description" in args:
            update_data["description"] = args["description"]
        if "status" in args:
            update_data["status"] = args["status"]
        if "priority" in args:
            update_data["priority"] = args["priority"]
        if "assignees" in args:
            update_data["assignees"] = {"add": args["assignees"]}
        if "due_date" in args:
            update_data["due_date"] = args["due_date"]
        if "start_date" in args:
            update_data["start_date"] = args["start_date"]

        result = self._make_request(org_id, user_id, "PUT", f"task/{task_id}", data=update_data)

        return {
            "task_id": result.get("id"),
            "name": result.get("name"),
            "status": result.get("status", {}).get("status"),
            "url": result.get("url"),
        }

    def list_tasks(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        List tasks in a list

        Args:
            list_id (required): List ID
            archived: Include archived tasks (default: false)
            page: Page number (0-indexed)
            order_by: Field to order by (created, updated, due_date)
            reverse: Reverse order (default: false)
            subtasks: Include subtasks (default: false)
            statuses: Filter by status names (array)
            assignees: Filter by assignee IDs (array)
            tags: Filter by tag names (array)
            due_date_gt: Due date greater than (timestamp)
            due_date_lt: Due date less than (timestamp)

        Returns:
            List of tasks (max 100 per page)
        """
        if not args.get("list_id"):
            raise ValueError("list_id is required")

        list_id = args["list_id"]
        params: dict[str, Any] = {}

        if args.get("archived"):
            params["archived"] = "true"
        if args.get("page") is not None:
            params["page"] = args["page"]
        if args.get("order_by"):
            params["order_by"] = args["order_by"]
        if args.get("reverse"):
            params["reverse"] = "true"
        if args.get("subtasks"):
            params["subtasks"] = "true"
        if args.get("statuses"):
            params["statuses[]"] = args["statuses"]
        if args.get("assignees"):
            params["assignees[]"] = args["assignees"]
        if args.get("tags"):
            params["tags[]"] = args["tags"]
        if args.get("due_date_gt"):
            params["due_date_gt"] = args["due_date_gt"]
        if args.get("due_date_lt"):
            params["due_date_lt"] = args["due_date_lt"]

        result = self._make_request(org_id, user_id, "GET", f"list/{list_id}/task", params=params)

        tasks = result.get("tasks", [])

        return {
            "count": len(tasks),
            "tasks": [
                {
                    "task_id": t.get("id"),
                    "name": t.get("name"),
                    "status": t.get("status", {}).get("status"),
                    "assignees": [a.get("username") for a in t.get("assignees", [])],
                    "due_date": t.get("due_date"),
                    "priority": (
                        t.get("priority", {}).get("priority")
                        if isinstance(t.get("priority"), dict)
                        else t.get("priority")
                    ),
                    "url": t.get("url"),
                }
                for t in tasks
            ],
        }
