"""
Conversation entity and API schemas for Phase 3 AI Chat.

This module defines:
- Conversation: Database table model for chat sessions
- ConversationCreate: API input schema
- ConversationPublic: API output schema

From data-model.md:
- id: UUID (PK, auto-generated)
- user_id: UUID (FK → users.id, NOT NULL)
- title: string (max 100 chars, nullable)
- created_at: timestamp (NOT NULL, default NOW())
- updated_at: timestamp (NOT NULL, auto-update)

Relationships:
- User → Conversation (1:N)
- Conversation → Message (1:N)

Implements FR-006: Persist conversation history per user session
Implements FR-013: User data isolation (users only access own conversations)
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from src.models.base import utc_now

if TYPE_CHECKING:
    from src.models.message import Message
    from src.models.user import User


# =============================================================================
# Database Table Model
# =============================================================================


class Conversation(SQLModel, table=True):
    """
    Conversation database entity.

    Represents a chat session between a user and the AI assistant.
    Contains messages and is owned by a single user.
    """

    __tablename__ = "conversations"

    id: UUID | None = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique conversation identifier (UUID v4)",
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
        description="Owner user identifier (FK -> users.id)",
    )

    title: str | None = Field(
        default=None,
        max_length=100,
        description="Optional conversation title (auto-generated from first message)",
    )

    created_at: datetime | None = Field(
        default_factory=utc_now,
        description="Conversation creation timestamp (UTC)",
    )

    updated_at: datetime | None = Field(
        default_factory=utc_now,
        description="Last activity timestamp (UTC)",
    )

    # Relationships
    user: "User" = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# =============================================================================
# API Input Schemas
# =============================================================================


class ConversationCreate(SQLModel):
    """
    Schema for conversation creation.

    user_id is NOT included here - it will be injected from auth context.
    """

    title: str | None = Field(
        default=None,
        max_length=100,
        description="Optional conversation title",
    )


# =============================================================================
# API Output Schemas
# =============================================================================


class ConversationPublic(SQLModel):
    """
    Schema for conversation data in API responses.

    Includes all fields needed by the client.
    Does NOT include messages - use ConversationDetail for that.
    """

    id: UUID = Field(description="Unique conversation identifier")
    user_id: UUID = Field(description="Owner user identifier")
    title: str | None = Field(description="Conversation title")
    created_at: datetime = Field(description="Conversation creation timestamp (UTC)")
    updated_at: datetime = Field(description="Last activity timestamp (UTC)")

    model_config = {"from_attributes": True}


class ConversationList(SQLModel):
    """Schema for paginated list of conversations."""

    conversations: list[ConversationPublic]
    total: int
    limit: int
    offset: int


__all__ = [
    "Conversation",
    "ConversationCreate",
    "ConversationPublic",
    "ConversationList",
]
