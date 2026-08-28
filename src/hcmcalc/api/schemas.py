"""Typed JSON contracts for the local API boundary."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from hcmcalc.application.registry import AnalysisDefinition


class HealthResponse(BaseModel):
    """Minimal service health response."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    service: str = "hcmcalc-api"
    api_version: str = "v1"
    application_version: str


class ApiError(BaseModel):
    """Stable structured error detail for API clients."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message_key: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class ApiErrorResponse(BaseModel):
    """Stable error envelope returned by the API boundary."""

    model_config = ConfigDict(extra="forbid")

    detail: ApiError


class MethodDefinitionResponse(BaseModel):
    """Public engineering metadata; no frontend delivery status is implied.

    The persisted method/input identity is intentionally separate from the
    qualified engine method identity for legacy workflows whose result method
    name differs from their project/fingerprint identity.
    """

    model_config = ConfigDict(extra="forbid")

    method_id: str = Field(min_length=1)
    family: str = Field(min_length=1)
    name_key: str = Field(min_length=1)
    description_key: str = Field(min_length=1)
    method_identifier: str = Field(min_length=1)
    engine_method_identifier: str = Field(min_length=1)
    method_version: str = Field(min_length=1)
    input_contract: str = Field(min_length=1)
    project_type: str = Field(min_length=1)
    hcm_edition: str = Field(min_length=1)
    hcm_chapter: str = Field(min_length=1)
    chapter_reference: str = Field(min_length=1)
    supported_unit_systems: list[Literal["metric", "imperial"]]
    availability: str = Field(min_length=1)
    engineering_available: bool = True
    capabilities: list[str]
    scope_summary_keys: list[str]
    legacy_workflow: str | None = None

    @classmethod
    def from_definition(cls, definition: AnalysisDefinition) -> "MethodDefinitionResponse":
        return cls.model_validate(definition.to_mapping())


class MethodsResponse(BaseModel):
    """Stable envelope for method discovery."""

    model_config = ConfigDict(extra="forbid")

    registry_version: str = "r1"
    methods: list[MethodDefinitionResponse]


class ValidationIssue(BaseModel):
    """A field-level or workflow-level validation message."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    field: str | None = None
    message: str = Field(min_length=1)
    message_key: str = Field(min_length=1)


class WorkflowRequest(BaseModel):
    """Displayed worksheet values submitted for validation/calculation."""

    model_config = ConfigDict(extra="forbid")

    template_id: str = Field(min_length=1)
    unit_system: Literal["metric", "imperial"]
    displayed_inputs: dict[str, Any]


class WorkflowValidationResponse(BaseModel):
    """Readiness response; validation never executes an HCM calculation."""

    model_config = ConfigDict(extra="forbid")

    method_id: str
    template_id: str
    unit_system: Literal["metric", "imperial"]
    valid: bool
    ready: bool
    validation_status: str
    errors: list[ValidationIssue]
    displayed_inputs: dict[str, Any]
    normalized_inputs: dict[str, Any] | None = None
    calculation_fingerprint: str | None = None
    input_snapshot_fingerprint: str | None = None
    method_identifier: str | None = None
    engine_method_identifier: str | None = None
    method_version: str | None = None
    input_contract: str | None = None
    project_type: str | None = None
    calculation_state: dict[str, Any]


class WorkflowCalculationResponse(BaseModel):
    """Auditable result envelope returned after explicit calculation."""

    model_config = ConfigDict(extra="forbid")

    method_id: str
    template_id: str
    unit_system: Literal["metric", "imperial"]
    displayed_inputs: dict[str, Any]
    normalized_inputs: dict[str, Any]
    calculation_fingerprint: str
    input_snapshot_fingerprint: str
    method_identifier: str
    engine_method_identifier: str
    method_version: str
    input_contract: str
    project_type: str
    calculation_state: dict[str, Any]
    result: dict[str, Any]
    presentation: dict[str, Any]
    audit: dict[str, Any]
    method: dict[str, Any]
    generated_at: str


class WorkflowTemplatesResponse(BaseModel):
    """Template, group, branch, and field metadata for one delivered workflow."""

    model_config = ConfigDict(extra="forbid")

    method_id: str
    unit_systems: list[Literal["metric", "imperial"]]
    templates: list[dict[str, Any]]
    fields: list[dict[str, Any]]
    groups: list[dict[str, Any]] = Field(default_factory=list)
    branches: dict[str, Any] = Field(default_factory=dict)
    scope_notes: list[str] = Field(default_factory=list)


class WorkflowStartingValuesResponse(BaseModel):
    """Validated starting values for a selected template."""

    model_config = ConfigDict(extra="allow")

    method_id: str
    template_id: str
    template_label: str
    unit_system: Literal["metric", "imperial"]
    fields: list[dict[str, Any]]


class WorkflowExportRequest(WorkflowRequest):
    """Export request carrying an already-calculated result identity."""

    calculation_fingerprint: str = Field(min_length=1)
    input_snapshot_fingerprint: str = Field(min_length=1)
    result: dict[str, Any]
    export_format: Literal["csv", "xlsx", "markdown", "json"]


class WorkflowExportResponse(BaseModel):
    """A rendered export; ``content_base64`` is used for XLSX."""

    model_config = ConfigDict(extra="forbid")

    export_format: Literal["csv", "xlsx", "markdown", "json"]
    filename: str
    content: str | None = None
    content_base64: str | None = None
    media_type: str
    calculation_fingerprint: str
    recalculated: Literal[False] = False


class ProjectDocumentRequest(BaseModel):
    """Generic Project v2 document carried by a file-oriented client."""

    model_config = ConfigDict(extra="forbid")

    project: dict[str, Any]


class ProjectFromAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_name: str = Field(default="Untitled HCM study", min_length=1)
    analysis_name: str | None = None
    scenario_name: str = Field(default="Base", min_length=1)
    analysis_snapshot: dict[str, Any]


class ProjectScenarioRequest(ProjectDocumentRequest):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)


class ProjectDuplicateScenarioRequest(ProjectScenarioRequest):
    scenario_name: str = Field(min_length=1)


class ProjectRenameScenarioRequest(ProjectScenarioRequest):
    scenario_name: str = Field(min_length=1)


class ProjectRecordResultRequest(ProjectDocumentRequest):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    analysis_snapshot: dict[str, Any]


class ProjectUpdateScenarioRequest(ProjectDocumentRequest):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    analysis_snapshot: dict[str, Any]


class ProjectCompareRequest(ProjectDocumentRequest):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(min_length=1)
    left_scenario_id: str = Field(min_length=1)
    right_scenario_id: str = Field(min_length=1)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: dict[str, Any]
    migrated: bool = False


class ProjectCompareResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comparison: dict[str, Any]
