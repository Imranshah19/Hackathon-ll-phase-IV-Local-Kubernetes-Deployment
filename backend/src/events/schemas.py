"""
Phase 5: Event Schema Definitions

CloudEvents format for task lifecycle events.
Reference: https://cloudevents.io/

Event Types:
- todo.task.created: Task was created
- todo.task.updated: Task was modified
- todo.task.completed: Task was marked complete
- todo.task.deleted: Task was deleted
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskEventType(str, Enum):
    """Task lifecycle event types."""
    CREATED = "todo.task.created"
    UPDATED = "todo.task.updated"
    COMPLETED = "todo.task.completed"
    DELETED = "todo.task.deleted"


class CloudEvent(BaseModel):
    """
    CloudEvents specification v1.0 compliant event schema.

    Used for all task lifecycle events published to Kafka via Dapr.
    """

    # Required attributes
    specversion: str = Field(default="1.0", description="CloudEvents spec version")
    type: str = Field(..., description="Event type (e.g., todo.task.created)")
    source: str = Field(default="/todo-app/backend", description="Event source URI")
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event ID")

    # Optional attributes
    time: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp (UTC)")
    datacontenttype: str = Field(default="application/json", description="Data content type")
    subject: str | None = Field(default=None, description="Subject (e.g., task ID)")

    # Event data
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload")

    model_config = {"extra": "allow"}


class TaskEventData(BaseModel):
    """
    Data payload for task events.

    Contains the task details at the time of the event.
    """

    task_id: UUID = Field(..., description="Task identifier")
    user_id: UUID = Field(..., description="Task owner identifier")
    title: str = Field(..., description="Task title")
    is_completed: bool = Field(default=False, description="Completion status")
    priority: int = Field(default=3, description="Priority level (1-5)")

    # Optional fields
    description: str | None = Field(default=None)
    due: datetime | None = Field(default=None)
    tags: list[str] = Field(default_factory=list, description="Tag names")

    # Audit
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


__all__ = [
    "TaskEventType",
    "CloudEvent",
    "TaskEventData",
]
