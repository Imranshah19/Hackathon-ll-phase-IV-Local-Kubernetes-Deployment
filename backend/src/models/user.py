"""
User entity and API schemas.

This module defines:
- UserBase: Shared validation for email
- User: Database table model with password_hash
- UserCreate: API input schema (accepts plain password)
- UserPublic: API output schema (excludes sensitive fields)

Implements requirements:
- FR-001: User schema with id, email, password_hash, created_at, updated_at
- FR-003: Unique constraint on email
- FR-005: UUID auto-generation for id
- FR-006: Auto-populate created_at
- FR-007: Auto-update updated_at
- FR-008: Email format validation
- FR-011: password_hash never exposed in API
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from src.models.base import utc_now

if TYPE_CHECKING:
    from src.models.conversation import Conversation
    from src.models.task import Task


# =============================================================================
# Base Schema (Shared Validation)
# =============================================================================

class UserBase(SQLModel):
    """
    Base user schema with shared email validation.

    Used as foundation for all user-related schemas.
    """

    email: EmailStr = Field(description="User's email address (RFC 5322 compliant)")


# =============================================================================
# Database Table Model
# =============================================================================

class User(UserBase, table=True):
    """
    User database entity.

    Represents an authenticated user account in the system.
    Contains identity (email), credentials (password_hash), and audit fields.
    """

    __tablename__ = "users"

    id: UUID | None = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique user identifier (UUID v4)",
    )

    password_hash: str = Field(description="Argon2id password hash (never exposed in API)")

    created_at: datetime | None = Field(
        default_factory=utc_now,
        description="Account creation timestamp (UTC)",
    )

    updated_at: datetime | None = Field(
        default_factory=utc_now,
        description="Last update timestamp (UTC)",
    )

    # Relationship to tasks (one-to-many with cascade delete)
    tasks: list["Task"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    # Relationship to conversations (one-to-many with cascade delete) - Phase 3
    conversations: list["Conversation"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# =============================================================================
# API Input Schema
# =============================================================================

class UserCreate(UserBase):
    """
    Schema for user registration.

    Accepts plain password which will be hashed before storage.
    Password must be at least 8 characters.
    """

    password: str = Field(
        min_length=8,
        description="Plain text password (min 8 characters)",
    )


# =============================================================================
# API Output Schema
# =============================================================================

class UserPublic(UserBase):
    """
    Schema for user data in API responses.

    Excludes sensitive fields (password_hash).
    Used when returning user data to clients.
    """

    id: UUID = Field(description="Unique user identifier")
    created_at: datetime = Field(description="Account creation timestamp (UTC)")
    updated_at: datetime = Field(description="Last update timestamp (UTC)")

    model_config = {"from_attributes": True}


__all__ = [
    "UserBase",
    "User",
    "UserCreate",
    "UserPublic",
]
