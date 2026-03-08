from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone

from app.core.config import settings
from app.core.response import APIResponse


router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    app_name: str
    version: str
    timestamp: datetime


class HealthDetail(BaseModel):
    """Detailed health check with component statuses."""

    status: str
    app_name: str
    version: str
    timestamp: datetime
    components: dict[str, str]


@router.get(
    "",
    response_model=APIResponse[HealthStatus],
    summary="Basic health check",
    description="Public endpoint to verify the service is running.",
)
async def health_check() -> APIResponse[HealthStatus]:
    """Basic health check endpoint."""
    return APIResponse.ok(
        data=HealthStatus(
            status="healthy",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            timestamp=datetime.now(timezone.utc),
        )
    )


@router.get(
    "/ready",
    response_model=APIResponse[HealthDetail],
    summary="Readiness check",
    description="Check if the service and its dependencies are ready to accept traffic.",
)
async def readiness_check() -> APIResponse[HealthDetail]:
    """Readiness check with component status.

    This endpoint checks:
    - Database connectivity (when implemented)
    - Redis connectivity (when implemented)
    - External service availability (when implemented)
    """
    components = {
        "database": "not_configured",
        "redis": "not_configured",
    }

    # TODO: Add actual health checks when infrastructure is connected
    # For now, return healthy status

    overall_status = "healthy"

    return APIResponse.ok(
        data=HealthDetail(
            status=overall_status,
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            timestamp=datetime.now(timezone.utc),
            components=components,
        )
    )
