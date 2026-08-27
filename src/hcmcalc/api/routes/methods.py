"""Backend-authoritative analysis method discovery routes."""

from fastapi import APIRouter, HTTPException, status

from hcmcalc.api.schemas import (
    ApiError,
    ApiErrorResponse,
    MethodDefinitionResponse,
    MethodsResponse,
)
from hcmcalc.application.registry import get_analysis_definition, list_analysis_definitions


router = APIRouter(prefix="/api/v1/methods", tags=["methods"])


@router.get("", response_model=MethodsResponse)
def list_methods() -> MethodsResponse:
    """List all current engineering methods for reference and frontend handshake."""

    return MethodsResponse(
        methods=[
            MethodDefinitionResponse.from_definition(definition)
            for definition in list_analysis_definitions()
        ]
    )


@router.get(
    "/{method_id}",
    response_model=MethodDefinitionResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse}},
)
def get_method(method_id: str) -> MethodDefinitionResponse:
    """Return one language-neutral engineering method definition."""

    definition = get_analysis_definition(method_id)
    if definition is None:
        detail = ApiError(
            code="method_not_found",
            message_key="api.method_not_found",
            details={"method_id": method_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail.model_dump(mode="json"),
        )
    return MethodDefinitionResponse.from_definition(definition)
