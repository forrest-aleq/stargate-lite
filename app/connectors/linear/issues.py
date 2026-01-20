"""
Issue operations for Linear connector.
"""

from typing import Any

from .base import LinearBase

# GraphQL mutation for issue creation
_ISSUE_CREATE_MUTATION = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      identifier
      title
      description
      url
      state { id name color }
      assignee { id name email }
      priority
      createdAt
      updatedAt
    }
  }
}
"""


class IssuesMixin(LinearBase):
    """Mixin with issue and comment operations."""

    def _build_issue_input(self, args: dict[str, Any], team_id: str, title: str) -> dict[str, Any]:
        """Build input data for issue creation with optional fields."""
        input_data: dict[str, Any] = {
            "teamId": team_id,
            "title": title,
            "createAsUser": self.agent_name,
        }
        if self.agent_avatar_url:
            input_data["displayIconUrl"] = self.agent_avatar_url

        optional_mappings = [
            ("description", "description"),
            ("assignee_id", "assigneeId"),
            ("state_id", "stateId"),
            ("project_id", "projectId"),
            ("label_ids", "labelIds"),
            ("parent_id", "parentId"),
        ]
        for arg_key, api_key in optional_mappings:
            if args.get(arg_key):
                input_data[api_key] = args[arg_key]

        if args.get("priority") is not None:
            input_data["priority"] = args["priority"]

        return input_data

    def _format_issue_response(self, issue_data: dict[str, Any]) -> dict[str, Any]:
        """Format issue data for API response."""
        return {
            "issue_id": issue_data["id"],
            "identifier": issue_data["identifier"],
            "title": issue_data["title"],
            "description": issue_data.get("description"),
            "url": issue_data["url"],
            "state": issue_data.get("state"),
            "assignee": issue_data.get("assignee"),
            "priority": issue_data.get("priority"),
            "created_at": issue_data["createdAt"],
        }

    def create_issue(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Create an issue in Linear as Aleq AI agent

        Args:
            team_id (str, required): Team ID where issue is created
            title (str, required): Issue title
            description (str, optional): Issue description (supports markdown)
            assignee_id (str, optional): User ID to assign
            priority (int, optional): Priority 0-4 (0=None, 1=Urgent, 2=High, 3=Medium, 4=Low)
            state_id (str, optional): State ID (e.g., "In Progress")
            project_id (str, optional): Project ID
            label_ids (list, optional): List of label IDs
            parent_id (str, optional): Parent issue ID for subtasks

        Returns:
            Dict with issue details including id, identifier (e.g., "ENG-123"), url
        """
        team_id = args.get("team_id")
        title = args.get("title")
        if not team_id:
            raise ValueError("team_id is required")
        if not title:
            raise ValueError("title is required")

        input_data = self._build_issue_input(args, team_id, title)
        result = self._graphql_request(
            org_id, user_id, _ISSUE_CREATE_MUTATION, {"input": input_data}
        )

        create_result = result.get("issueCreate", {})
        if not create_result.get("success"):
            raise RuntimeError("Failed to create issue in Linear")
        issue_data = create_result.get("issue")
        if not issue_data:
            raise RuntimeError("No issue data returned from Linear")

        return self._format_issue_response(issue_data)

    def update_issue(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing issue

        Args:
            issue_id (str, required): Issue ID to update
            title (str, optional): New title
            description (str, optional): New description
            state_id (str, optional): New state ID
            assignee_id (str, optional): New assignee ID
            priority (int, optional): New priority
            project_id (str, optional): Move to project

        Returns:
            Dict with updated issue details
        """
        query = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue {
              id
              identifier
              title
              description
              url
              state { id name }
              assignee { id name }
              priority
              updatedAt
            }
          }
        }
        """

        issue_id = args.get("issue_id")
        if not issue_id:
            raise ValueError("issue_id is required")
        input_data = {}

        # Only include fields being updated
        if args.get("title"):
            input_data["title"] = args["title"]

        if args.get("description") is not None:
            input_data["description"] = args["description"]

        if args.get("state_id"):
            input_data["stateId"] = args["state_id"]

        if args.get("assignee_id") is not None:
            input_data["assigneeId"] = args["assignee_id"]

        if args.get("priority") is not None:
            input_data["priority"] = args["priority"]

        if args.get("project_id") is not None:
            input_data["projectId"] = args["project_id"]

        result = self._graphql_request(
            org_id, user_id, query, {"id": issue_id, "input": input_data}
        )

        issue_data = result["issueUpdate"]["issue"]

        return {
            "issue_id": issue_data["id"],
            "identifier": issue_data["identifier"],
            "title": issue_data["title"],
            "description": issue_data.get("description"),
            "url": issue_data["url"],
            "state": issue_data.get("state"),
            "assignee": issue_data.get("assignee"),
            "priority": issue_data.get("priority"),
            "updated_at": issue_data["updatedAt"],
        }

    def get_issue(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get issue details by ID

        Args:
            issue_id (str, required): Issue ID

        Returns:
            Dict with full issue details including comments
        """
        query = """
        query Issue($id: String!) {
          issue(id: $id) {
            id
            identifier
            title
            description
            url
            state {
              id
              name
              color
            }
            assignee {
              id
              name
              email
            }
            priority
            team {
              id
              name
              key
            }
            project {
              id
              name
            }
            labels {
              nodes {
                id
                name
                color
              }
            }
            comments {
              nodes {
                id
                body
                user {
                  id
                  name
                }
                createdAt
              }
            }
            createdAt
            updatedAt
          }
        }
        """

        issue_id = args.get("issue_id")
        if not issue_id:
            raise ValueError("issue_id is required")

        result = self._graphql_request(org_id, user_id, query, {"id": issue_id})

        issue = result["issue"]

        return {
            "issue_id": issue["id"],
            "identifier": issue["identifier"],
            "title": issue["title"],
            "description": issue.get("description"),
            "url": issue["url"],
            "state": issue.get("state"),
            "assignee": issue.get("assignee"),
            "priority": issue.get("priority"),
            "team": issue.get("team"),
            "project": issue.get("project"),
            "labels": list(issue.get("labels", {}).get("nodes", [])),
            "comments": list(issue.get("comments", {}).get("nodes", [])),
            "created_at": issue["createdAt"],
            "updated_at": issue["updatedAt"],
        }

    def list_issues(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        List issues with filtering

        Args:
            team_id (str, optional): Filter by team
            assignee_id (str, optional): Filter by assignee
            state_name (str, optional): Filter by state (e.g., "In Progress")
            limit (int, optional): Max results (default 50)

        Returns:
            Dict with issues list
        """
        query = """
        query Issues($filter: IssueFilter, $first: Int) {
          issues(filter: $filter, first: $first) {
            nodes {
              id
              identifier
              title
              url
              state {
                name
                color
              }
              assignee {
                id
                name
              }
              priority
              createdAt
              updatedAt
            }
          }
        }
        """

        # Build filter
        filter_data = {}

        if args.get("team_id"):
            filter_data["team"] = {"id": {"eq": args["team_id"]}}

        if args.get("assignee_id"):
            filter_data["assignee"] = {"id": {"eq": args["assignee_id"]}}

        if args.get("state_name"):
            filter_data["state"] = {"name": {"eq": args["state_name"]}}

        variables = {"first": args.get("limit", 50)}

        if filter_data:
            variables["filter"] = filter_data

        result = self._graphql_request(org_id, user_id, query, variables)

        issues = result["issues"]["nodes"]

        return {
            "issues": [
                {
                    "issue_id": issue["id"],
                    "identifier": issue["identifier"],
                    "title": issue["title"],
                    "url": issue["url"],
                    "state": issue.get("state"),
                    "assignee": issue.get("assignee"),
                    "priority": issue.get("priority"),
                    "created_at": issue["createdAt"],
                    "updated_at": issue["updatedAt"],
                }
                for issue in issues
            ],
            "count": len(issues),
        }

    def create_comment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Create a comment on an issue (as Aleq AI agent)

        Args:
            issue_id (str, required): Issue ID to comment on
            body (str, required): Comment body (supports markdown)

        Returns:
            Dict with comment details
        """
        query = """
        mutation CommentCreate($input: CommentCreateInput!) {
          commentCreate(input: $input) {
            success
            comment {
              id
              body
              user {
                id
                name
              }
              issue {
                id
                identifier
              }
              createdAt
            }
          }
        }
        """

        issue_id = args.get("issue_id")
        body = args.get("body")
        if not issue_id:
            raise ValueError("issue_id is required")
        if not body:
            raise ValueError("body is required")

        input_data = {
            "issueId": issue_id,
            "body": body,
            "createAsUser": self.agent_name,  # Agent identity
        }

        # Add optional agent avatar
        if self.agent_avatar_url:
            input_data["displayIconUrl"] = self.agent_avatar_url

        result = self._graphql_request(org_id, user_id, query, {"input": input_data})

        comment_data = result["commentCreate"]["comment"]

        return {
            "comment_id": comment_data["id"],
            "body": comment_data["body"],
            "user": comment_data.get("user"),
            "issue_id": comment_data["issue"]["id"],
            "issue_identifier": comment_data["issue"]["identifier"],
            "created_at": comment_data["createdAt"],
        }
