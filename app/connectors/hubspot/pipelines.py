"""
HubSpot pipelines mixin for pipeline and stage operations.
"""

from typing import Any

from app.http_client import http_client

from .associations import AssociationsMixin


class PipelinesMixin(AssociationsMixin):
    """Mixin with pipeline operations."""

    def list_pipelines(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List pipelines for an object type"""
        cred = self._get_access_token(org_id, user_id)
        object_type = args.get("object_type", "deals")

        url = f"{self.BASE_URL}/crm/v3/pipelines/{object_type}"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )

        pipelines = [
            {
                "pipeline_id": p["id"],
                "label": p.get("label"),
                "display_order": p.get("displayOrder"),
                "stages_count": len(p.get("stages", [])),
            }
            for p in result.get("results", [])
        ]

        return {"object_type": object_type, "pipelines": pipelines}

    def get_pipeline(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get pipeline details with stages"""
        cred = self._get_access_token(org_id, user_id)
        object_type = args.get("object_type", "deals")
        pipeline_id = args.get("pipeline_id")

        url = f"{self.BASE_URL}/crm/v3/pipelines/{object_type}/{pipeline_id}"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )

        stages = [
            {
                "stage_id": s["id"],
                "label": s.get("label"),
                "display_order": s.get("displayOrder"),
                "metadata": s.get("metadata", {}),
            }
            for s in result.get("stages", [])
        ]

        return {
            "pipeline_id": result["id"],
            "label": result.get("label"),
            "stages": stages,
        }

    def list_pipeline_stages(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List stages for a specific pipeline"""
        cred = self._get_access_token(org_id, user_id)
        object_type = args.get("object_type", "deals")
        pipeline_id = args.get("pipeline_id")

        url = f"{self.BASE_URL}/crm/v3/pipelines/{object_type}/{pipeline_id}/stages"
        result = http_client.get(
            url=url,
            service="hubspot",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )

        stages = [
            {
                "stage_id": s["id"],
                "label": s.get("label"),
                "display_order": s.get("displayOrder"),
            }
            for s in result.get("results", [])
        ]

        return {
            "pipeline_id": pipeline_id,
            "stages": stages,
            "count": len(stages),
        }
