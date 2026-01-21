"""
Health check endpoint for Kubernetes probes and monitoring.

Provides:
- Liveness probe: Is the application running?
- Readiness probe: Is the application ready to accept traffic?
- Database connectivity status
"""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import text

from src.db import engine

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: Literal["healthy", "unhealthy"]
    timestamp: str
    database: Literal["connected", "disconnected"]
    version: str = "0.1.0"


class LivenessResponse(BaseModel):
    """Liveness probe response schema."""

    status: Literal["alive"]


class ReadinessResponse(BaseModel):
    """Readiness probe response schema."""

    status: Literal["ready", "not_ready"]
    database: Literal["connected", "disconnected"]


def check_database_connection() -> bool:
    """
    Check if database is reachable.

    Returns:
        bool: True if database is connected, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"},
    },
    summary="Full health check",
    description="Returns comprehensive health status including database connectivity.",
)
async def health_check() -> JSONResponse:
    """
    Full health check endpoint.

    Returns service status and database connectivity.
    Used by monitoring systems and load balancers.
    """
    db_connected = check_database_connection()
    timestamp = datetime.now(timezone.utc).isoformat()

    response_data = {
        "status": "healthy" if db_connected else "unhealthy",
        "timestamp": timestamp,
        "database": "connected" if db_connected else "disconnected",
        "version": "0.1.0",
    }

    status_code = status.HTTP_200_OK if db_connected else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=response_data, status_code=status_code)


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Kubernetes liveness probe. Returns 200 if application is running.",
)
async def liveness_probe() -> LivenessResponse:
    """
    Kubernetes liveness probe.

    Always returns 200 if the application is running.
    Used by Kubernetes to detect if pod needs restart.
    """
    return LivenessResponse(status="alive")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    },
    summary="Readiness probe",
    description="Kubernetes readiness probe. Returns 200 if ready to accept traffic.",
)
async def readiness_probe() -> JSONResponse:
    """
    Kubernetes readiness probe.

    Checks if the service is ready to accept traffic.
    Returns 503 if database is not connected.
    """
    db_connected = check_database_connection()

    response_data = {
        "status": "ready" if db_connected else "not_ready",
        "database": "connected" if db_connected else "disconnected",
    }

    status_code = status.HTTP_200_OK if db_connected else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=response_data, status_code=status_code)
