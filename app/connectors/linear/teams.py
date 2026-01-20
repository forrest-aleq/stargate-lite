"""
Team, project, label, and agent operations for Linear connector.
"""

from typing import Any

from .issues import IssuesMixin


class TeamsMixin(IssuesMixin):
    """Mixin with team, project, label, and agent operations."""

    def list_teams(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        List teams in workspace

        Returns:
            Dict with teams list
        """
        query = """
        query Teams {
          teams {
            nodes {
              id
              name
              key
              description
            }
          }
        }
        """

        result = self._graphql_request(org_id, user_id, query)

        teams = result["teams"]["nodes"]

        return {
            "teams": [
                {
                    "team_id": team["id"],
                    "name": team["name"],
                    "key": team["key"],
                    "description": team.get("description"),
                }
                for team in teams
            ],
            "count": len(teams),
        }

    def get_team(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get team details

        Args:
            team_id (str, required): Team ID

        Returns:
            Dict with team details
        """
        query = """
        query Team($id: String!) {
          team(id: $id) {
            id
            name
            key
            description
            states {
              nodes {
                id
                name
                color
                type
              }
            }
          }
        }
        """

        team_id = args.get("team_id")
        if not team_id:
            raise ValueError("team_id is required")

        result = self._graphql_request(org_id, user_id, query, {"id": team_id})

        team = result.get("team")
        if not team:
            raise RuntimeError(f"Team {team_id} not found")

        return {
            "team_id": team["id"],
            "name": team["name"],
            "key": team["key"],
            "description": team.get("description"),
            "states": list(team.get("states", {}).get("nodes", [])),
        }

    def list_projects(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        List projects in workspace

        Args:
            team_id (str, optional): Filter by team

        Returns:
            Dict with projects list
        """
        query = """
        query Projects($filter: ProjectFilter) {
          projects(filter: $filter) {
            nodes {
              id
              name
              description
              state
              url
            }
          }
        }
        """

        variables = {}

        if args.get("team_id"):
            variables["filter"] = {"team": {"id": {"eq": args["team_id"]}}}

        result = self._graphql_request(org_id, user_id, query, variables)

        projects = result["projects"]["nodes"]

        return {
            "projects": [
                {
                    "project_id": project["id"],
                    "name": project["name"],
                    "description": project.get("description"),
                    "state": project["state"],
                    "url": project["url"],
                }
                for project in projects
            ],
            "count": len(projects),
        }

    def create_label(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Create a label

        Args:
            team_id (str, required): Team ID
            name (str, required): Label name
            color (str, optional): Hex color (e.g., "#ff0000")
            description (str, optional): Label description

        Returns:
            Dict with label details
        """
        query = """
        mutation IssueLabelCreate($input: IssueLabelCreateInput!) {
          issueLabelCreate(input: $input) {
            success
            issueLabel {
              id
              name
              color
              description
            }
          }
        }
        """

        team_id = args.get("team_id")
        name = args.get("name")
        if not team_id:
            raise ValueError("team_id is required")
        if not name:
            raise ValueError("name is required")

        input_data: dict[str, Any] = {"teamId": team_id, "name": name}

        if args.get("color"):
            input_data["color"] = args["color"]

        if args.get("description"):
            input_data["description"] = args["description"]

        result = self._graphql_request(org_id, user_id, query, {"input": input_data})

        create_result = result.get("issueLabelCreate", {})
        if not create_result.get("success"):
            raise RuntimeError("Failed to create label in Linear")
        label_data = create_result.get("issueLabel")
        if not label_data:
            raise RuntimeError("No label data returned from Linear")

        return {
            "label_id": label_data["id"],
            "name": label_data["name"],
            "color": label_data.get("color"),
            "description": label_data.get("description"),
        }

    def get_viewer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get current agent user info

        Returns:
            Dict with agent user details (useful for debugging)
        """
        query = """
        query Viewer {
          viewer {
            id
            name
            email
            active
          }
        }
        """

        result = self._graphql_request(org_id, user_id, query)

        viewer = result["viewer"]

        return {
            "user_id": viewer["id"],
            "name": viewer["name"],
            "email": viewer.get("email"),
            "active": viewer["active"],
        }
