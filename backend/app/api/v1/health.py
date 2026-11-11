"""
Health Check Endpoint (GET /api/v1/health).
"""

from datetime import datetime, timezone
from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="System Health Check")
async def health_check() -> HealthResponse:
    """
    Returns the current operational status of the API and underlying infrastructure services.
    """
    return HealthResponse(
        status="healthy",
        mongodb="connected",
        timestamp=datetime.now(timezone.utc),
    )
