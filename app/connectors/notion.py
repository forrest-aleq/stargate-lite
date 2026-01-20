"""
Notion connector for Stargate Lite
Handles databases, pages, blocks
Uses Notion API 2025-09-03 (Multi-source databases)
"""

import os
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class NotionConnector:
    """Notion API connector for workspace management"""

    BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2025-09-03"

    def __init__(self) -> None:
        self.api_key = os.getenv("NOTION_API_KEY")

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
            "Notion-Version": self.API_VERSION,
        }

    def _make_request(
        self, method: str, endpoint: str, access_token: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers(access_token)

        if method not in ["GET", "POST", "PATCH", "DELETE"]:
            raise ValueError(f"Unsupported method: {method}")

        if method == "GET":
            return http_client.get(url=url, service="notion", headers=headers, params=data)
        else:
            result: dict[str, Any] = http_client.request(
                method=method, url=url, service="notion", headers=headers, json=data
            )
            return result

    def query_database(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Query a database (2025-09-03 with data_source_id support)"""
        access_token = self._get_access_token(args)
        database_id = args.get("database_id")

        query_data = {
            "filter": args.get("filter", {}),
            "sorts": args.get("sorts", []),
            "start_cursor": args.get("start_cursor"),
            "page_size": args.get("page_size", 100),
        }

        result = self._make_request(
            "POST", f"/databases/{database_id}/query", access_token, query_data
        )

        return {
            "results": result.get("results", []),
            "next_cursor": result.get("next_cursor"),
            "has_more": result.get("has_more", False),
        }

    def create_page(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a page in a database (2025-09-03: uses data_source_id)"""
        access_token = self._get_access_token(args)

        page_data = {
            "parent": {
                "type": "data_source_id",  # NEW in 2025-09-03
                "data_source_id": args.get("data_source_id"),
            },
            "properties": args.get("properties", {}),
        }

        if args.get("children"):
            page_data["children"] = args["children"]

        result = self._make_request("POST", "/pages", access_token, page_data)

        return {
            "page_id": result["id"],
            "url": result.get("url"),
            "created_time": result.get("created_time"),
        }

    def update_page(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a page's properties"""
        access_token = self._get_access_token(args)
        page_id = args.get("page_id")

        update_data = {"properties": args.get("properties", {})}

        if args.get("archived") is not None:
            update_data["archived"] = args["archived"]

        result = self._make_request("PATCH", f"/pages/{page_id}", access_token, update_data)

        return {"page_id": result["id"], "last_edited_time": result.get("last_edited_time")}

    def get_page(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get page details"""
        access_token = self._get_access_token(args)
        page_id = args.get("page_id")

        result = self._make_request("GET", f"/pages/{page_id}", access_token)

        return {
            "page_id": result["id"],
            "properties": result.get("properties", {}),
            "url": result.get("url"),
            "created_time": result.get("created_time"),
            "last_edited_time": result.get("last_edited_time"),
        }

    def append_block_children(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Append blocks to a page (max 100 blocks per request)"""
        access_token = self._get_access_token(args)
        block_id = args.get("block_id")  # Page ID or block ID

        blocks_data = {
            "children": args.get("children", [])  # Max 100 blocks
        }

        result = self._make_request(
            "PATCH", f"/blocks/{block_id}/children", access_token, blocks_data
        )

        return {"results": result.get("results", []), "block_count": len(result.get("results", []))}

    def get_block_children(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get children of a block"""
        access_token = self._get_access_token(args)
        block_id = args.get("block_id")

        params = {"start_cursor": args.get("start_cursor"), "page_size": args.get("page_size", 100)}

        result = self._make_request("GET", f"/blocks/{block_id}/children", access_token, params)

        return {
            "results": result.get("results", []),
            "next_cursor": result.get("next_cursor"),
            "has_more": result.get("has_more", False),
        }

    def get_database(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get database details"""
        access_token = self._get_access_token(args)
        database_id = args.get("database_id")

        result = self._make_request("GET", f"/databases/{database_id}", access_token)

        return {
            "database_id": result["id"],
            "title": result.get("title", []),
            "properties": result.get("properties", {}),
            "url": result.get("url"),
        }

    def get_data_sources(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get data sources for a database (NEW in 2025-09-03)"""
        access_token = self._get_access_token(args)
        database_id = args.get("database_id")

        result = self._make_request("GET", f"/databases/{database_id}/data_sources", access_token)

        return {
            "data_sources": [
                {"data_source_id": ds["id"], "name": ds.get("name"), "type": ds.get("type")}
                for ds in result.get("results", [])
            ]
        }

    def create_database(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new database"""
        access_token = self._get_access_token(args)

        database_data = {
            "parent": {"type": "page_id", "page_id": args.get("parent_page_id")},
            "title": args.get("title", []),
            "properties": args.get("properties", {}),
        }

        result = self._make_request("POST", "/databases", access_token, database_data)

        return {"database_id": result["id"], "url": result.get("url")}

    def search(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search Notion workspace"""
        access_token = self._get_access_token(args)

        search_data = {
            "query": args.get("query", ""),
            "filter": args.get("filter", {}),
            "sort": args.get("sort", {}),
            "page_size": args.get("page_size", 100),
        }

        result = self._make_request("POST", "/search", access_token, search_data)

        return {
            "results": result.get("results", []),
            "next_cursor": result.get("next_cursor"),
            "has_more": result.get("has_more", False),
        }
