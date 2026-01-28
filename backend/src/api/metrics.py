"""
Phase 5: Prometheus Metrics Endpoint

Exposes application metrics in Prometheus format for monitoring.

Metrics exposed:
- http_requests_total: Total HTTP requests by method, path, status
- http_request_duration_seconds: Request latency histogram
- tasks_total: Total tasks by status (pending, completed)
- active_users: Number of active users

Usage:
    Include the router in your FastAPI app:
    app.include_router(router)

Access metrics at: GET /metrics
"""

from fastapi import APIRouter, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    multiprocess,
)
import os

router = APIRouter()

# =============================================================================
# Metrics Registry
# =============================================================================

# Use multiprocess mode if running with multiple workers
if "prometheus_multiproc_dir" in os.environ:
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
else:
    registry = CollectorRegistry(auto_describe=True)

# =============================================================================
# HTTP Metrics
# =============================================================================

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status"],
    registry=registry,
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry,
)

# =============================================================================
# Application Metrics
# =============================================================================

TASKS_TOTAL = Gauge(
    "tasks_total",
    "Total number of tasks by status",
    ["status"],
    registry=registry,
)

ACTIVE_USERS = Gauge(
    "active_users",
    "Number of active users",
    registry=registry,
)

EVENTS_PUBLISHED = Counter(
    "events_published_total",
    "Total number of events published to message broker",
    ["event_type", "status"],
    registry=registry,
)

REMINDERS_SENT = Counter(
    "reminders_sent_total",
    "Total number of reminders sent",
    ["status"],
    registry=registry,
)

# =============================================================================
# Metrics Endpoint
# =============================================================================


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )


# =============================================================================
# Metric Helper Functions
# =============================================================================


def record_request(method: str, path: str, status: int, duration: float) -> None:
    """
    Record an HTTP request metric.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status: HTTP status code
        duration: Request duration in seconds
    """
    HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=status).inc()
    HTTP_REQUEST_DURATION.labels(method=method, path=path).observe(duration)


def update_task_counts(pending: int, completed: int) -> None:
    """
    Update task count gauges.

    Args:
        pending: Number of pending tasks
        completed: Number of completed tasks
    """
    TASKS_TOTAL.labels(status="pending").set(pending)
    TASKS_TOTAL.labels(status="completed").set(completed)


def record_event_published(event_type: str, success: bool) -> None:
    """
    Record an event publish attempt.

    Args:
        event_type: Type of event (e.g., task.created)
        success: Whether the publish succeeded
    """
    status = "success" if success else "failure"
    EVENTS_PUBLISHED.labels(event_type=event_type, status=status).inc()


def record_reminder_sent(success: bool) -> None:
    """
    Record a reminder send attempt.

    Args:
        success: Whether the reminder was sent successfully
    """
    status = "success" if success else "failure"
    REMINDERS_SENT.labels(status=status).inc()


__all__ = [
    "router",
    "record_request",
    "update_task_counts",
    "record_event_published",
    "record_reminder_sent",
    "HTTP_REQUESTS_TOTAL",
    "HTTP_REQUEST_DURATION",
    "TASKS_TOTAL",
    "ACTIVE_USERS",
    "EVENTS_PUBLISHED",
    "REMINDERS_SENT",
]
