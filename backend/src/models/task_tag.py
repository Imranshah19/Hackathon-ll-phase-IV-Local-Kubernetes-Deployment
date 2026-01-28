"""
TaskTag junction table for many-to-many relationship.

Phase 5: Task-Tag association.

This module defines:
- TaskTag: Junction table linking tasks and tags

Implements requirements:
- FR-007: Task-tag association with junction table
- CASCADE DELETE on both FKs
"""

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from src.models.base import utc_now


class TaskTag(SQLModel, table=True):
    """
    TaskTag junction table.

    Links tasks to tags in a many-to-many relationship.
    A task can have multiple tags, and a tag can be on multiple tasks.
    """

    __tablename__ = "task_tag"

    task_id: UUID = Field(
        foreign_key="tasks.id",
        primary_key=True,
        description="Task identifier (FK -> tasks.id)",
    )

    tag_id: UUID = Field(
        foreign_key="tags.id",
        primary_key=True,
        description="Tag identifier (FK -> tags.id)",
    )

    created_at: datetime | None = Field(
        default_factory=utc_now,
        description="Association creation timestamp (UTC)",
    )


__all__ = [
    "TaskTag",
]
