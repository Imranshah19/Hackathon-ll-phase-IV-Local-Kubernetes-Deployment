"""
Message entity and API schemas for Phase 3 AI Chat.

This module defines:
- MessageRole: Enum for message sender (user/assistant)
- Message: Database table model for individual messages
- MessageCreate: API input schema (internal use)
- MessagePublic: API output schema

From data-model.md:
- id: UUID (PK, auto-generated)
- conversation_id: UUID (FK → conversations.id, NOT NULL)
- role: enum ('user' | 'assistant', NOT NULL)
- content: text (NOT NULL, max 2000 chars)
- generated_command: string (nullable, max 500 chars, assistant only)
- confidence_score: float (nullable, 0.0-1.0, assistant only)
- timestamp: timestamp (NOT NULL, default NOW())

Validation Rules:
- content must not be empty or whitespace-only
- generated_command only populated for role='assistant'
- confidence_score only populated for role='assistant'
- Messages are immutable after creation

Implements FR-005: Return human-readable responses
Implements FR-010: Log AI interpretations with confidence scores
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

from src.models.base import utc_now

if TYPE_CHECKING:
    from src.models.conversation import Conversation


# =============================================================================
# Enums
# =============================================================================


class MessageRole(str, Enum):
    """Message sender role."""

    USER = "user"
    ASSISTANT = "assistant"


# =============================================================================
# Database Table Model
# =============================================================================


class Message(SQLModel, table=True):
    """
    Message database entity.

    An individual message within a conversation.
    Messages are immutable after creation.
    """

    __tablename__ = "messages"

    id: UUID | None = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique message identifier (UUID v4)",
    )

    conversation_id: UUID = Field(
        foreign_key="conversations.id",
        nullable=False,
        index=True,
        description="Parent conversation identifier",
    )

    role: MessageRole = Field(
        nullable=False,
        description="Who sent the message (user or assistant)",
    )

    content: str = Field(
        max_length=2000,
        nullable=False,
        description="Message content (max 2000 characters)",
    )

    generated_command: str | None = Field(
        default=None,
        max_length=500,
        description="Bonsai CLI command (assistant messages only)",
    )

    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="AI interpretation confidence (assistant messages only)",
    )

    timestamp: datetime | None = Field(
        default_factory=utc_now,
        index=True,
        description="Message timestamp (UTC)",
    )

    # Relationships
    conversation: "Conversation" = Relationship(back_populates="messages")


# =============================================================================
# API Input Schemas
# =============================================================================


class MessageCreate(SQLModel):
    """
    Schema for message creation (internal use).

    conversation_id is set by the service layer.
    role is determined by context (user input vs AI response).
    """

    content: str = Field(
        min_length=1,
        max_length=2000,
        description="Message content",
    )

    @field_validator("content")
    @classmethod
    def content_not_whitespace(cls, v: str) -> str:
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError("Message content cannot be empty or whitespace-only")
        return v


class AssistantMessageCreate(MessageCreate):
    """Schema for assistant message creation with AI metadata."""

    generated_command: str | None = Field(
        default=None,
        max_length=500,
        description="Bonsai CLI command that was executed",
    )

    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="AI interpretation confidence",
    )


# =============================================================================
# API Output Schemas
# =============================================================================


class MessagePublic(SQLModel):
    """
    Schema for message data in API responses.

    Includes all fields needed by the client.
    """

    id: UUID = Field(description="Unique message identifier")
    role: MessageRole = Field(description="Message sender role")
    content: str = Field(description="Message content")
    generated_command: str | None = Field(description="CLI command (assistant only)")
    confidence_score: float | None = Field(description="AI confidence (assistant only)")
    timestamp: datetime = Field(description="Message timestamp (UTC)")

    model_config = {"from_attributes": True}


__all__ = [
    "MessageRole",
    "Message",
    "MessageCreate",
    "AssistantMessageCreate",
    "MessagePublic",
]
