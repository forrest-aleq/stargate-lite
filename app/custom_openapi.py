"""Custom OpenAPI schema generation for Stargate Lite.

Ensures the runtime /openapi.json endpoint and the committed openapi.json
file serve identical schemas. Post-processes the FastAPI-generated spec to:
  - Include schemas that can be dropped by inference/caching edge cases
  - Replace anyOf with oneOf + discriminator on the /api/v1/execute response
  - Pin /api/v1/capabilities response to typed CapabilitiesResponse
"""

from __future__ import annotations

from typing import Any


def custom_openapi(app: Any) -> dict[str, Any]:
    """Return the OpenAPI schema with contract-stable post-processing.

    FastAPI caches the result on ``app.openapi_schema``, so this function
    is called at most once per process.
    """
    if app.openapi_schema:
        return app.openapi_schema  # type: ignore[no-any-return]

    from fastapi.openapi.utils import get_openapi

    from app.models import CapabilitiesResponse, CapabilityInfo, ToolExecutionResponse

    spec: dict[str, Any] = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Ensure key models are present even if FastAPI omits them due to inference quirks.
    schemas = spec.setdefault("components", {}).setdefault("schemas", {})
    if "ToolExecutionResponse" not in schemas:
        schemas["ToolExecutionResponse"] = ToolExecutionResponse.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
    if "CapabilityInfo" not in schemas:
        schemas["CapabilityInfo"] = CapabilityInfo.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
    if "CapabilitiesResponse" not in schemas:
        schemas["CapabilitiesResponse"] = CapabilitiesResponse.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )

    # Stabilize execute response as oneOf + discriminator (not anyOf)
    execute_path = spec.get("paths", {}).get("/api/v1/execute", {})
    post_200 = execute_path.get("post", {}).get("responses", {}).get("200", {})
    schema = post_200.get("content", {}).get("application/json", {}).get("schema", {})
    if "anyOf" in schema:
        schema["oneOf"] = schema.pop("anyOf")
        schema["discriminator"] = {
            "propertyName": "status",
            "mapping": {
                "success": "#/components/schemas/ToolExecutionResponse",
                "error": "#/components/schemas/ErrorResponse",
            },
        }

    # Stabilize capabilities response as typed model reference.
    capabilities_path = spec.get("paths", {}).get("/api/v1/capabilities", {})
    cap_200 = capabilities_path.get("get", {}).get("responses", {}).get("200", {})
    cap_content = cap_200.get("content", {}).get("application/json", {})
    cap_content["schema"] = {"$ref": "#/components/schemas/CapabilitiesResponse"}

    app.openapi_schema = spec
    return spec
