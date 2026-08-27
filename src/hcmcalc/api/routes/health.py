"""Health endpoint."""

from fastapi import APIRouter

from hcmcalc import __version__
from hcmcalc.api.schemas import HealthResponse


router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report that the local application boundary is available."""

    return HealthResponse(application_version=__version__)
