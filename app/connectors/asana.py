"""
Asana connector for Stargate Lite
Handles tasks, projects, portfolios, custom fields, sections
Uses Asana API 1.0 (October 2025)
"""

import os
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class AsanaConnector:
    """Asana API connector for project management"""

    BASE_URL = "https://app.asana.com/api/1.0"

    def __init__(self) -> None:
        self.api_key = os.getenv("ASANA_API_KEY")

    def _get_access_token(self, args: dict[str, Any]) -> str:
        """Extract and validate access_token from args."""
        access_token = args.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("access_token is required and must be a string")
        return access_token

    def _get_headers(self, access_token: str | None = None) -> dict[str, str]:
        token = access_token or self.api_key
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _make_request(
        self, method: str, endpoint: str, access_token: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers(access_token)

        if method not in ["GET", "POST", "PUT", "DELETE"]:
            raise ValueError(f"Unsupported method: {method}")

        # Handle GET with params vs POST/PUT with JSON body
        if method == "GET":
            result = http_client.get(url=url, service="asana", headers=headers, params=data)
        else:
            # POST, PUT, DELETE
            result = http_client.request(
                method=method,
                url=url,
                service="asana",
                headers=headers,
                json={"data": data} if data else {},
            )

        data = result.get("data", result)
        return data if isinstance(data, dict) else result

    def create_task(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a task in Asana"""
        access_token = self._get_access_token(args)

        task_data = {
            "name": args.get("task_name"),
            "notes": args.get("notes", ""),
            "workspace": args.get("workspace_gid"),
            "projects": args.get("projects", []),  # Array of project GIDs
        }

        # Optional fields
        if args.get("assignee"):
            task_data["assignee"] = args["assignee"]

        if args.get("due_on"):
            task_data["due_on"] = args["due_on"]

        if args.get("due_at"):
            task_data["due_at"] = args["due_at"]

        if args.get("custom_fields"):
            task_data["custom_fields"] = args["custom_fields"]

        if args.get("parent"):
            task_data["parent"] = args["parent"]  # For subtasks

        result = self._make_request("POST", "/tasks", access_token, task_data)

        return {
            "task_gid": result["gid"],
            "name": result.get("name"),
            "permalink_url": result.get("permalink_url"),
            "created_at": result.get("created_at"),
        }

    def update_task(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an existing task"""
        access_token = self._get_access_token(args)
        task_gid = args.get("task_gid")

        update_data = {}

        # Only include fields that are being updated
        if args.get("name"):
            update_data["name"] = args["name"]

        if args.get("notes") is not None:
            update_data["notes"] = args["notes"]

        if args.get("completed") is not None:
            update_data["completed"] = args["completed"]

        if args.get("assignee") is not None:
            update_data["assignee"] = args["assignee"]

        if args.get("due_on") is not None:
            update_data["due_on"] = args["due_on"]

        if args.get("custom_fields"):
            update_data["custom_fields"] = args["custom_fields"]

        result = self._make_request("PUT", f"/tasks/{task_gid}", access_token, update_data)

        return {
            "task_gid": result["gid"],
            "name": result.get("name"),
            "completed": result.get("completed"),
            "modified_at": result.get("modified_at"),
        }

    def get_task(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get task details"""
        access_token = self._get_access_token(args)
        task_gid = args.get("task_gid")

        default_opt_fields = (
            "name,notes,completed,assignee,due_on,custom_fields," "projects,tags,permalink_url"
        )
        params = {"opt_fields": args.get("opt_fields", default_opt_fields)}

        result = self._make_request("GET", f"/tasks/{task_gid}", access_token, params)

        return {
            "task_gid": result["gid"],
            "name": result.get("name"),
            "notes": result.get("notes"),
            "completed": result.get("completed"),
            "assignee": result.get("assignee"),
            "due_on": result.get("due_on"),
            "custom_fields": result.get("custom_fields", []),
            "projects": result.get("projects", []),
            "tags": result.get("tags", []),
            "permalink_url": result.get("permalink_url"),
        }

    def list_tasks(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List tasks in a project"""
        access_token = self._get_access_token(args)
        project_gid = args.get("project_gid")

        params = {
            "opt_fields": args.get("opt_fields", "name,completed,assignee,due_on"),
            "limit": args.get("limit", 100),
        }

        result = self._make_request("GET", f"/projects/{project_gid}/tasks", access_token, params)

        return {
            "tasks": [
                {
                    "task_gid": t["gid"],
                    "name": t.get("name"),
                    "completed": t.get("completed"),
                    "assignee": t.get("assignee"),
                    "due_on": t.get("due_on"),
                }
                for t in (result if isinstance(result, list) else result.get("data", []))
            ]
        }

    def create_project(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a project"""
        access_token = self._get_access_token(args)

        project_data = {
            "name": args.get("project_name"),
            "workspace": args.get("workspace_gid"),
            "notes": args.get("notes", ""),
            "layout": args.get("layout", "list"),  # list or board
        }

        # Optional fields
        if args.get("team"):
            project_data["team"] = args["team"]

        if args.get("color"):
            project_data["color"] = args["color"]

        if args.get("owner"):
            project_data["owner"] = args["owner"]

        if args.get("due_date"):
            project_data["due_date"] = args["due_date"]

        result = self._make_request("POST", "/projects", access_token, project_data)

        return {
            "project_gid": result["gid"],
            "name": result.get("name"),
            "permalink_url": result.get("permalink_url"),
            "created_at": result.get("created_at"),
        }

    def get_project(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get project details"""
        access_token = self._get_access_token(args)
        project_gid = args.get("project_gid")

        default_opt_fields = (
            "name,notes,color,completed,owner,team,members,custom_fields,permalink_url"
        )
        params = {"opt_fields": args.get("opt_fields", default_opt_fields)}

        result = self._make_request("GET", f"/projects/{project_gid}", access_token, params)

        return {
            "project_gid": result["gid"],
            "name": result.get("name"),
            "notes": result.get("notes"),
            "color": result.get("color"),
            "completed": result.get("completed"),
            "owner": result.get("owner"),
            "team": result.get("team"),
            "members": result.get("members", []),
            "custom_fields": result.get("custom_fields", []),
            "permalink_url": result.get("permalink_url"),
        }

    def list_projects(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List projects in a workspace"""
        access_token = self._get_access_token(args)
        workspace_gid = args.get("workspace_gid")

        params = {
            "workspace": workspace_gid,
            "opt_fields": args.get("opt_fields", "name,owner,completed"),
            "limit": args.get("limit", 100),
        }

        result = self._make_request("GET", "/projects", access_token, params)

        return {
            "projects": [
                {
                    "project_gid": p["gid"],
                    "name": p.get("name"),
                    "owner": p.get("owner"),
                    "completed": p.get("completed"),
                }
                for p in (result if isinstance(result, list) else result.get("data", []))
            ]
        }

    def add_custom_field_to_project(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Add a custom field to a project"""
        access_token = self._get_access_token(args)
        project_gid = args.get("project_gid")

        field_data = {
            "custom_field": args.get("custom_field_gid"),
            "insert_before": args.get("insert_before"),  # Optional: position control
            "insert_after": args.get("insert_after"),
        }

        result = self._make_request(
            "POST", f"/projects/{project_gid}/addCustomFieldSetting", access_token, field_data
        )

        return {
            "custom_field_setting_gid": result.get("gid"),
            "custom_field": result.get("custom_field"),
            "project": result.get("project"),
        }

    def update_task_custom_field(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Update custom field value on a task"""
        access_token = self._get_access_token(args)
        task_gid = args.get("task_gid")
        custom_field_gid = args.get("custom_field_gid")
        value = args.get("value")

        # Custom fields need to be updated via the task update endpoint
        update_data = {"custom_fields": {custom_field_gid: value}}

        result = self._make_request("PUT", f"/tasks/{task_gid}", access_token, update_data)

        return {"task_gid": result["gid"], "custom_fields": result.get("custom_fields", [])}

    def create_section(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a section in a project"""
        access_token = self._get_access_token(args)
        project_gid = args.get("project_gid")

        section_data = {
            "name": args.get("section_name"),
            "insert_before": args.get("insert_before"),  # Optional: position control
            "insert_after": args.get("insert_after"),
        }

        result = self._make_request(
            "POST", f"/projects/{project_gid}/sections", access_token, section_data
        )

        return {
            "section_gid": result["gid"],
            "name": result.get("name"),
            "project": result.get("project"),
            "created_at": result.get("created_at"),
        }

    def add_task_to_section(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Add a task to a section"""
        access_token = self._get_access_token(args)
        section_gid = args.get("section_gid")

        task_data = {
            "task": args.get("task_gid"),
            "insert_before": args.get("insert_before"),  # Optional: position control
            "insert_after": args.get("insert_after"),
        }

        self._make_request("POST", f"/sections/{section_gid}/addTask", access_token, task_data)

        return {"success": True, "section_gid": section_gid, "task_gid": args.get("task_gid")}

    def upload_attachment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Upload an attachment to a task"""
        access_token = self._get_access_token(args)
        task_gid = args.get("task_gid")
        file_content = args.get("file_content")  # bytes
        file_name = args.get("file_name")

        url = f"{self.BASE_URL}/tasks/{task_gid}/attachments"
        headers = {"Authorization": f"Bearer {access_token or self.api_key}"}

        files = {"file": (file_name, file_content)}

        result = http_client.post(url=url, service="asana", headers=headers, files=files)
        data = result.get("data", result)

        return {
            "attachment_gid": data["gid"],
            "name": data.get("name"),
            "download_url": data.get("download_url"),
            "permanent_url": data.get("permanent_url"),
        }
