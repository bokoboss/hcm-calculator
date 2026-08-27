"""Typed API routes for the Phase 2 representative workflows."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from hcmcalc.api.schemas import (
    ApiError,
    ApiErrorResponse,
    WorkflowCalculationResponse,
    WorkflowExportRequest,
    WorkflowExportResponse,
    WorkflowRequest,
    WorkflowStartingValuesResponse,
    WorkflowTemplatesResponse,
    WorkflowValidationResponse,
)
from hcmcalc.application.workflows import (
    ApplicationWorkflowError,
    calculate_workflow_request,
    export_current_workflow,
    validate_workflow_request,
    workflow_starting_values,
    workflow_templates,
)


router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])


def _application_error(exc: ApplicationWorkflowError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        if exc.code not in {"method_not_found"}
        else status.HTTP_404_NOT_FOUND,
        detail=ApiError(
            code=exc.code,
            message_key=exc.message_key,
            details=exc.details,
        ).model_dump(mode="json"),
    )


@router.get(
    "/{method_id}/templates",
    response_model=WorkflowTemplatesResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse}},
)
def get_workflow_templates(method_id: str) -> WorkflowTemplatesResponse:
    try:
        return WorkflowTemplatesResponse.model_validate(workflow_templates(method_id))
    except ApplicationWorkflowError as exc:
        raise _application_error(exc) from exc


@router.get(
    "/{method_id}/starting-values",
    response_model=WorkflowStartingValuesResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse}},
)
def get_workflow_starting_values(
    method_id: str,
    template_id: str,
    unit_system: str = "metric",
) -> WorkflowStartingValuesResponse:
    try:
        return WorkflowStartingValuesResponse.model_validate(
            workflow_starting_values(method_id, template_id, unit_system)
        )
    except ApplicationWorkflowError as exc:
        raise _application_error(exc) from exc


@router.post(
    "/{method_id}/validate",
    response_model=WorkflowValidationResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse}},
)
def validate_workflow(
    method_id: str, request: WorkflowRequest
) -> WorkflowValidationResponse:
    try:
        result = validate_workflow_request(
            method_id,
            template_id=request.template_id,
            unit_system=request.unit_system,
            displayed_inputs=request.displayed_inputs,
        )
        return WorkflowValidationResponse.model_validate(result)
    except ApplicationWorkflowError as exc:
        raise _application_error(exc) from exc


@router.post(
    "/{method_id}/calculate",
    response_model=WorkflowCalculationResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse}},
)
def calculate_workflow(
    method_id: str, request: WorkflowRequest
) -> WorkflowCalculationResponse:
    try:
        result = calculate_workflow_request(
            method_id,
            template_id=request.template_id,
            unit_system=request.unit_system,
            displayed_inputs=request.displayed_inputs,
        )
        return WorkflowCalculationResponse.model_validate(result)
    except ApplicationWorkflowError as exc:
        raise _application_error(exc) from exc


@router.post(
    "/{method_id}/export",
    response_model=WorkflowExportResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse}},
)
def export_workflow(
    method_id: str, request: WorkflowExportRequest
) -> WorkflowExportResponse:
    try:
        result = export_current_workflow(
            method_id,
            template_id=request.template_id,
            unit_system=request.unit_system,
            displayed_inputs=request.displayed_inputs,
            calculation_fingerprint=request.calculation_fingerprint,
            input_snapshot_fingerprint=request.input_snapshot_fingerprint,
            result=request.result,
            export_format=request.export_format,
        )
        return WorkflowExportResponse.model_validate(result)
    except ApplicationWorkflowError as exc:
        raise _application_error(exc) from exc
