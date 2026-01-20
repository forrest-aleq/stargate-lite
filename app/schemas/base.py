"""
Schema models for Enhanced Capability Registry.

Provides rich metadata for AI agents (MARS/Claude) to understand and use
capabilities more effectively.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.errors import ErrorCode


class ParameterSchema(BaseModel):
    """Schema for a single parameter of a capability."""

    type: Literal["string", "integer", "number", "boolean", "array", "object"]
    required: bool = False
    description: str
    default: Any = None
    enum: list[str] | None = None
    example: Any = None
    items_type: str | None = Field(default=None, description="Type of items if type is 'array'")
    properties: dict[str, "ParameterSchema"] | None = Field(
        default=None, description="Nested properties if type is 'object'"
    )


class ReturnFieldSchema(BaseModel):
    """Schema for a single field in the return value."""

    type: str
    description: str
    example: Any = None
    items_type: str | None = Field(default=None, description="Type of items if type is 'array'")


class ErrorHint(BaseModel):
    """Hint about a specific error that may occur."""

    error_code: ErrorCode
    description: str
    recovery_hint: str


class WorkflowHints(BaseModel):
    """Hints for workflow orchestration - what capabilities pair well."""

    typically_preceded_by: list[str] = Field(
        default_factory=list,
        description="Capabilities that usually come before this one",
    )
    typically_followed_by: list[str] = Field(
        default_factory=list,
        description="Capabilities that usually come after this one",
    )
    related_capabilities: list[str] = Field(
        default_factory=list,
        description="Other capabilities that work well with this one",
    )


class UsageExample(BaseModel):
    """Example of how to use this capability."""

    description: str
    args: dict[str, Any]
    expected_output: dict[str, Any] | None = None


class CapabilitySchema(BaseModel):
    """
    Complete schema for a capability, enabling AI agents to understand:
    - What the capability does (description, description_detailed)
    - What parameters it accepts (parameters)
    - What it returns (returns)
    - What errors may occur (errors)
    - How it fits into workflows (workflow)
    - Example usage (examples)
    - Side effect information (idempotent, has_side_effects)
    """

    capability_key: str = Field(description="The unique capability key (e.g., 'vendor.create')")
    service: str = Field(description="The service this capability belongs to (e.g., 'quickbooks')")
    category: str | None = Field(
        default=None, description="Category within the service (e.g., 'vendors', 'bills')"
    )
    description: str = Field(description="Short description (1 line)")
    description_detailed: str | None = Field(
        default=None,
        description="Detailed description including when/why to use this capability",
    )
    parameters: dict[str, ParameterSchema] = Field(
        default_factory=dict, description="Input parameters"
    )
    returns: dict[str, ReturnFieldSchema] = Field(
        default_factory=dict, description="Return value fields"
    )
    errors: list[ErrorHint] = Field(default_factory=list, description="Possible errors")
    workflow: WorkflowHints | None = Field(default=None, description="Workflow orchestration hints")
    examples: list[UsageExample] = Field(default_factory=list, description="Usage examples")
    idempotent: bool = Field(
        default=False, description="True if calling multiple times has no additional effect"
    )
    has_side_effects: bool = Field(
        default=True, description="True if this capability modifies state"
    )
