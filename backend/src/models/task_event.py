"""
TaskEvent entity for audit and event publishing.

Phase 5: Event-driven architecture support.

This module defines:
- TaskEventType: Enum for event types
- TaskEvent: Database table model for audit log
- TaskEventPublic: API output schema

Implements requirements:
- FR-028: Task events for audit and event publishing
- Event retry support for failed publishes
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON

from src.models.base import utc_now


# =============================================================================
# Enums
# =============================================================================

class TaskEventType(str, Enum):
    """Types of task lifecycle events."""
    CREATED = "task.created"
    UPDATED = "task.updated"
    COMPLETED = "task.completed"
    DELETED = "task.deleted"
    TAG_ADDED = "task.tag_added"
    TAG_REMOVED = "task.tag_removed"
    REMINDER_SET = "task.reminder_set"
    RECURRENCE_CREATED = "task.recurrence_created"


# =============================================================================
# Database Table Model
# =============================================================================

class TaskEvent(SQLModel, table=True):
    """
    TaskEvent database entity.

    Stores task lifecycle events for audit and async publishing.
    Events are published to Kafka via Dapr and marked as published.
    Failed publishes are retried via scheduled job.
    """

    __tablename__ = "task_events"

    id: UUID | None = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique event identifier (UUID v4)",
    )

    task_id: UUID = Field(
        foreign_key="tasks.id",
        nullable=False,
        index=True,
        description="Task this event relates to (FK -> tasks.id)",
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
        description="User who triggered the event (FK -> users.id)",
    )

    event_type: str = Field(
        max_length=50,
        index=True,
        description="Type of event (e.g., task.created)",
    )

    event_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Event payload as JSON",
    )

    published: bool = Field(
        default=False,
        index=True,
        description="Whether event has been published to message broker",
    )

    published_at: datetime | None = Field(
        default=None,
        description="When the event was published (UTC)",
    )

    created_at: datetime | None = Field(
        default_factory=utc_now,
        index=True,
        description="Event creation timestamp (UTC)",
    )


# =============================================================================
# API Output Schema
# =============================================================================

class TaskEventPublic(SQLModel):
    """
    Schema for task event data in API responses.
    """

    id: UUID = Field(description="Unique event identifier")
    task_id: UUID = Field(description="Associated task identifier")
    user_id: UUID = Field(description="User who triggered the event")
    event_type: str = Field(description="Type of event")
    event_data: dict[str, Any] | None = Field(description="Event payload")
    published: bool = Field(description="Whether event was published")
    created_at: datetime = Field(description="Event creation timestamp (UTC)")

    model_config = {"from_attributes": True}


__all__ = [
    "TaskEventType",
    "TaskEvent",
    "TaskEventPublic",
]
