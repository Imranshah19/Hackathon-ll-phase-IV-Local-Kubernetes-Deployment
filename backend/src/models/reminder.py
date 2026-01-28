"""
Reminder entity and API schemas.

Phase 5: Task reminder notifications.

This module defines:
- ReminderBase: Shared validation
- Reminder: Database table model
- ReminderCreate: API input schema
- ReminderPublic: API output schema

Implements requirements:
- FR-019: Reminders with scheduled datetime
- Auto-cancel on task completion
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from src.models.base import utc_now

if TYPE_CHECKING:
    from src.models.task import Task


# =============================================================================
# Base Schema (Shared Validation)
# =============================================================================

class ReminderBase(SQLModel):
    """
    Base reminder schema with shared validation.

    Used as foundation for all reminder-related schemas.
    """

    remind_at: datetime = Field(
        description="When to send the reminder (UTC)",
    )

    message: str | None = Field(
        default=None,
        max_length=255,
        description="Optional custom reminder message",
    )


# =============================================================================
# Database Table Model
# =============================================================================

class Reminder(ReminderBase, table=True):
    """
    Reminder database entity.

    Represents a scheduled notification for a task.
    Automatically canceled when the associated task is completed.
    """

    __tablename__ = "reminders"

    id: UUID | None = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique reminder identifier (UUID v4)",
    )

    task_id: UUID = Field(
        foreign_key="tasks.id",
        nullable=False,
        index=True,
        description="Associated task identifier (FK -> tasks.id)",
    )

    sent: bool = Field(
        default=False,
        description="Whether the reminder has been sent",
    )

    sent_at: datetime | None = Field(
        default=None,
        description="When the reminder was sent (UTC)",
    )

    created_at: datetime | None = Field(
        default_factory=utc_now,
        description="Reminder creation timestamp (UTC)",
    )

    # Relationship back to Task
    task: "Task" = Relationship(back_populates="reminders")


# =============================================================================
# API Input Schemas
# =============================================================================

class ReminderCreate(ReminderBase):
    """
    Schema for reminder creation.

    task_id must be provided.
    """

    task_id: UUID = Field(description="Task to attach reminder to")


# =============================================================================
# API Output Schema
# =============================================================================

class ReminderPublic(ReminderBase):
    """
    Schema for reminder data in API responses.
    """

    id: UUID = Field(description="Unique reminder identifier")
    task_id: UUID = Field(description="Associated task identifier")
    sent: bool = Field(description="Whether reminder has been sent")
    sent_at: datetime | None = Field(description="When reminder was sent")
    created_at: datetime = Field(description="Reminder creation timestamp (UTC)")

    model_config = {"from_attributes": True}


__all__ = [
    "ReminderBase",
    "Reminder",
    "ReminderCreate",
    "ReminderPublic",
]
