"""
Tag entity and API schemas.

Phase 5: Task categorization with user-defined tags.

This module defines:
- TagBase: Shared validation for name, color
- Tag: Database table model with user_id FK
- TagCreate: API input schema
- TagUpdate: API input schema for updates
- TagPublic: API output schema

Implements requirements:
- FR-006: Tags with name and color per user
- Unique constraint on (user_id, name) - no duplicate tag names per user
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from src.models.base import utc_now

if TYPE_CHECKING:
    from src.models.user import User


# =============================================================================
# Base Schema (Shared Validation)
# =============================================================================

class TagBase(SQLModel):
    """
    Base tag schema with shared validation.

    Used as foundation for all tag-related schemas.
    """

    name: str = Field(
        min_length=1,
        max_length=50,
        description="Tag name (1-50 characters, unique per user)",
    )

    color: str = Field(
        default="#6B7280",
        max_length=7,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Tag color as hex code (e.g., #FF5733)",
    )


# =============================================================================
# Database Table Model
# =============================================================================

class Tag(TagBase, table=True):
    """
    Tag database entity.

    Represents a user-defined category for organizing tasks.
    Each user can have multiple tags with unique names.
    """

    __tablename__ = "tags"

    id: UUID | None = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique tag identifier (UUID v4)",
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
        description="Owner user identifier (FK -> users.id)",
    )

    created_at: datetime | None = Field(
        default_factory=utc_now,
        description="Tag creation timestamp (UTC)",
    )

    # Relationship back to User
    user: "User" = Relationship(back_populates="tags")


# =============================================================================
# API Input Schemas
# =============================================================================

class TagCreate(TagBase):
    """
    Schema for tag creation.

    user_id is NOT included - it will be injected from auth context.
    """

    pass


class TagUpdate(SQLModel):
    """
    Schema for partial tag updates.

    All fields are optional to support PATCH semantics.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Updated tag name",
    )

    color: str | None = Field(
        default=None,
        max_length=7,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Updated tag color",
    )


# =============================================================================
# API Output Schema
# =============================================================================

class TagPublic(TagBase):
    """
    Schema for tag data in API responses.

    Includes task count for UI display.
    """

    id: UUID = Field(description="Unique tag identifier")
    user_id: UUID = Field(description="Owner user identifier")
    created_at: datetime = Field(description="Tag creation timestamp (UTC)")
    task_count: int = Field(default=0, description="Number of tasks with this tag")

    model_config = {"from_attributes": True}


__all__ = [
    "TagBase",
    "Tag",
    "TagCreate",
    "TagUpdate",
    "TagPublic",
]
