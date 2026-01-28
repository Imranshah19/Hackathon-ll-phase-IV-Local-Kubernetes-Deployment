"""
Task entity and API schemas.

This module defines:
- TaskBase: Shared validation for title, description, is_completed
- Task: Database table model with user_id FK
- TaskCreate: API input schema (user_id injected from auth)
- TaskUpdate: API input schema for partial updates
- TaskPublic: API output schema

Implements requirements:
- FR-002: Task schema with id, user_id, title, description, is_completed, timestamps
- FR-004: Foreign key on Task.user_id -> User.id
- FR-005: UUID auto-generation for id
- FR-006: Auto-populate created_at
- FR-007: Auto-update updated_at
- FR-009: Title validation (1-255 chars)
- FR-010: Description validation (max 4000 chars)
- FR-012: CASCADE DELETE on User->Task relationship
- FR-014: description nullable with default None

Phase 5 additions:
- FR-001: Priority field (1=Critical to 5=None, default=3)
- FR-013: Recurrence support via recurrence_rule_id FK
- FR-015: Due date field for scheduling
- Parent task tracking for recurring instances
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from src.models.base import utc_now

if TYPE_CHECKING:
    from src.models.reminder import Reminder
    from src.models.user import User


# =============================================================================
# Base Schema (Shared Validation)
# =============================================================================

class TaskBase(SQLModel):
    """
    Base task schema with shared validation.

    Used as foundation for all task-related schemas.
    """

    title: str = Field(
        min_length=1,
        max_length=255,
        description="Task title (1-255 characters, required)",
    )

    description: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional task description (max 4000 characters)",
    )

    is_completed: bool = Field(
        default=False,
        description="Task completion status",
    )

    # Phase 5: Priority Management
    priority: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Priority level: 1=Critical, 2=High, 3=Medium, 4=Low, 5=None",
    )

    due: datetime | None = Field(
        default=None,
        description="Task due date/time (UTC)",
    )


# =============================================================================
# Database Table Model
# =============================================================================

class Task(TaskBase, table=True):
    """
    Task database entity.

    Represents a todo item owned by a user.
    Contains title, description, completion status, and audit fields.

    Phase 5 additions:
    - priority: 1-5 scale for task importance
    - due: optional due date/time
    - recurrence_rule_id: FK to recurrence pattern
    - parent_task_id: self-FK for recurring instances
    """

    __tablename__ = "tasks"

    id: UUID | None = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique task identifier (UUID v4)",
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
        description="Owner user identifier (FK -> users.id)",
    )

    created_at: datetime | None = Field(
        default_factory=utc_now,
        description="Task creation timestamp (UTC)",
    )

    updated_at: datetime | None = Field(
        default_factory=utc_now,
        description="Last update timestamp (UTC)",
    )

    # Phase 5: Recurring task support
    recurrence_rule_id: UUID | None = Field(
        default=None,
        foreign_key="recurrence_rules.id",
        nullable=True,
        description="FK to recurrence pattern (null for non-recurring tasks)",
    )

    parent_task_id: UUID | None = Field(
        default=None,
        foreign_key="tasks.id",
        nullable=True,
        description="Parent task ID for recurring instances",
    )

    # Relationship back to User
    user: "User" = Relationship(back_populates="tasks")

    # Phase 5: Reminders relationship
    reminders: list["Reminder"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# =============================================================================
# API Input Schemas
# =============================================================================

class TaskCreate(TaskBase):
    """
    Schema for task creation.

    user_id is NOT included here - it will be injected from auth context.
    Inherits title, description, is_completed from TaskBase.
    """

    pass


class TaskUpdate(SQLModel):
    """
    Schema for partial task updates.

    All fields are optional to support PATCH semantics.
    Only provided fields will be updated.
    """

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated task title",
    )

    description: str | None = Field(
        default=None,
        max_length=4000,
        description="Updated task description",
    )

    is_completed: bool | None = Field(
        default=None,
        description="Updated completion status",
    )

    # Phase 5: Priority and due date updates
    priority: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="Updated priority level",
    )

    due: datetime | None = Field(
        default=None,
        description="Updated due date/time",
    )


# =============================================================================
# API Output Schema
# =============================================================================

class TaskPublic(TaskBase):
    """
    Schema for task data in API responses.

    Includes all fields needed by the client.
    """

    id: UUID = Field(description="Unique task identifier")
    user_id: UUID = Field(description="Owner user identifier")
    created_at: datetime = Field(description="Task creation timestamp (UTC)")
    updated_at: datetime = Field(description="Last update timestamp (UTC)")

    # Phase 5: Recurring task references
    recurrence_rule_id: UUID | None = Field(
        default=None,
        description="Recurrence pattern ID (null if not recurring)",
    )
    parent_task_id: UUID | None = Field(
        default=None,
        description="Parent task ID for recurring instances",
    )

    # Tags will be populated from relationship
    tags: list[str] = Field(
        default_factory=list,
        description="Tag names associated with this task",
    )

    model_config = {"from_attributes": True}


__all__ = [
    "TaskBase",
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskPublic",
]
