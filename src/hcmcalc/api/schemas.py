"""Typed JSON contracts for the R1 discovery/health API."""

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
