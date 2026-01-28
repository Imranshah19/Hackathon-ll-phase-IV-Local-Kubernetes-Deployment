"""
Phase 5: Structured JSON Logging Configuration

Configures structlog for JSON-formatted log output suitable for
log aggregation systems (ELK, Loki, CloudWatch, etc.).

Usage:
    from src.config.logging import configure_logging, get_logger

    configure_logging()
    logger = get_logger(__name__)
    logger.info("Task created", task_id=str(task.id), user_id=str(user_id))

Output format (JSON):
    {
        "timestamp": "2026-01-28T12:00:00.000000Z",
        "level": "info",
        "logger": "src.api.tasks",
        "message": "Task created",
        "task_id": "uuid",
        "user_id": "uuid",
        "request_id": "uuid"
    }
"""

import logging
import os
import sys
from typing import Any

import structlog


def configure_logging(
    log_level: str | None = None,
    json_format: bool | None = None,
) -> None:
    """
    Configure application logging with structlog.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Whether to output JSON (default: True in production)
    """
    # Determine settings from environment
    level = log_level or os.getenv("LOG_LEVEL", "INFO")
    is_production = os.getenv("ENV", "development") == "production"
    use_json = json_format if json_format is not None else is_production

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Shared processors
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if use_json:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Pretty console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        BoundLogger: Structured logger instance
    """
    return structlog.get_logger(name)


def bind_request_context(request_id: str, user_id: str | None = None) -> None:
    """
    Bind request context to all subsequent log calls.

    Args:
        request_id: Unique request identifier
        user_id: Authenticated user ID (if available)
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        user_id=user_id,
    )


def unbind_request_context() -> None:
    """Clear request context after request completion."""
    structlog.contextvars.clear_contextvars()


__all__ = [
    "configure_logging",
    "get_logger",
    "bind_request_context",
    "unbind_request_context",
]
