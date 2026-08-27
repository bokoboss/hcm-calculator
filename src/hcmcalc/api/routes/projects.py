"""File-oriented Project v2 API operations (no database)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from hcmcalc.api.schemas import (
    ApiError,
    ApiErrorResponse,
    ProjectCompareRequest,
    ProjectCompareResponse,
    ProjectDocumentRequest,
    ProjectDuplicateScenarioRequest,
    ProjectFromAnalysisRequest,
    ProjectRecordResultRequest,
    ProjectRenameScenarioRequest,
    ProjectResponse,
    ProjectUpdateScenarioRequest,
)
from hcmcalc.application.project import (
    ProjectFileError,
    compare_scenarios,
    duplicate_scenario,
    load_project,
    record_result,
    rename_scenario,
    save_analysis_to_project,
    update_scenario_inputs,
)


router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _project_error(exc: ProjectFileError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=ApiError(
            code="project_invalid",
            message_key="api.project_invalid",
            details={"message": str(exc)},
        ).model_dump(mode="json"),
    )


@router.post(
    "/from-analysis",
    response_model=ProjectResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ApiErrorResponse}},
)
def project_from_analysis(request: ProjectFromAnalysisRequest) -> ProjectResponse:
    try:
        project = save_analysis_to_project(
            request.analysis_snapshot,
            project_name=request.project_name,
            analysis_name=request.analysis_name,
            scenario_name=request.scenario_name,
        )
        return ProjectResponse(project=project)
    except ProjectFileError as exc:
        raise _project_error(exc) from exc


@router.post(
    "/validate",
    response_model=ProjectResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ApiErrorResponse}},
)
def validate_project(request: ProjectDocumentRequest) -> ProjectResponse:
    try:
        project = load_project(request.project)
        return ProjectResponse(
            project=project,
            migrated=bool(project.get("migration")),
        )
    except ProjectFileError as exc:
        raise _project_error(exc) from exc


@router.post(
    "/duplicate-scenario",
    response_model=ProjectResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ApiErrorResponse}},
)
def project_duplicate_scenario(request: ProjectDuplicateScenarioRequest) -> ProjectResponse:
    try:
        return ProjectResponse(
            project=duplicate_scenario(
                request.project,
                analysis_id=request.analysis_id,
                scenario_id=request.scenario_id,
                scenario_name=request.scenario_name,
            )
        )
    except ProjectFileError as exc:
        raise _project_error(exc) from exc


@router.post(
    "/rename-scenario",
    response_model=ProjectResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ApiErrorResponse}},
)
def project_rename_scenario(request: ProjectRenameScenarioRequest) -> ProjectResponse:
    try:
        return ProjectResponse(
            project=rename_scenario(
                request.project,
                analysis_id=request.analysis_id,
                scenario_id=request.scenario_id,
                scenario_name=request.scenario_name,
            )
        )
    except ProjectFileError as exc:
        raise _project_error(exc) from exc


@router.post(
    "/record-result",
    response_model=ProjectResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ApiErrorResponse}},
)
def project_record_result(request: ProjectRecordResultRequest) -> ProjectResponse:
    try:
        return ProjectResponse(
            project=record_result(
                request.project,
                analysis_id=request.analysis_id,
                scenario_id=request.scenario_id,
                snapshot=request.analysis_snapshot,
            )
        )
    except ProjectFileError as exc:
        raise _project_error(exc) from exc


@router.post(
    "/update-scenario",
    response_model=ProjectResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ApiErrorResponse}},
)
def project_update_scenario(request: ProjectUpdateScenarioRequest) -> ProjectResponse:
    try:
        return ProjectResponse(
            project=update_scenario_inputs(
                request.project,
                analysis_id=request.analysis_id,
                scenario_id=request.scenario_id,
                snapshot=request.analysis_snapshot,
            )
        )
    except ProjectFileError as exc:
        raise _project_error(exc) from exc


@router.post(
    "/compare",
    response_model=ProjectCompareResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ApiErrorResponse}},
)
def project_compare(request: ProjectCompareRequest) -> ProjectCompareResponse:
    try:
        return ProjectCompareResponse(
            comparison=compare_scenarios(
                request.project,
                analysis_id=request.analysis_id,
                left_scenario_id=request.left_scenario_id,
                right_scenario_id=request.right_scenario_id,
            )
        )
    except ProjectFileError as exc:
        raise _project_error(exc) from exc
