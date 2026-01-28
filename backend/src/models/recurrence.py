"""
RecurrenceRule entity and API schemas.

Phase 5: Recurring task patterns.

This module defines:
- RecurrenceFrequency: Enum for frequency types
- RecurrenceEndType: Enum for end conditions
- RecurrenceRuleBase: Shared validation
- RecurrenceRule: Database table model
- RecurrenceRuleCreate: API input schema
- RecurrenceRulePublic: API output schema

Implements requirements:
- FR-013: Recurrence rules with frequency, interval, end conditions
"""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from src.models.base import utc_now

if TYPE_CHECKING:
    from src.models.user import User


# =============================================================================
# Enums
# =============================================================================

class RecurrenceFrequency(str, Enum):
    """Frequency types for recurring tasks."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class RecurrenceEndType(str, Enum):
    """End condition types for recurrence."""
    NEVER = "never"
    COUNT = "count"
    DATE = "date"


# =============================================================================
# Base Schema (Shared Validation)
# =============================================================================

class RecurrenceRuleBase(SQLModel):
    """
    Base recurrence rule schema with shared validation.

    Used as foundation for all recurrence-related schemas.
    """

    frequency: RecurrenceFrequency = Field(
        description="Recurrence frequency (daily, weekly, monthly, yearly, custom)",
    )

    interval: int = Field(
        default=1,
        ge=1,
        le=365,
        description="Interval between occurrences (e.g., every 2 weeks)",
    )

    end_type: RecurrenceEndType = Field(
        default=RecurrenceEndType.NEVER,
        description="How the recurrence ends (never, count, date)",
    )

    end_count: int | None = Field(
        default=None,
        ge=1,
        le=999,
        description="Number of occurrences (when end_type=count)",
    )

    end_date: date | None = Field(
        default=None,
        description="End date (when end_type=date)",
    )


# =============================================================================
# Database Table Model
# =============================================================================

class RecurrenceRule(RecurrenceRuleBase, table=True):
    """
    RecurrenceRule database entity.

    Defines a pattern for recurring tasks.
    Multiple tasks can share the same recurrence rule.
    """

    __tablename__ = "recurrence_rules"

    id: UUID | None = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique recurrence rule identifier (UUID v4)",
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
        description="Owner user identifier (FK -> users.id)",
    )

    created_at: datetime | None = Field(
        default_factory=utc_now,
        description="Rule creation timestamp (UTC)",
    )

    # Relationship back to User
    user: "User" = Relationship(back_populates="recurrence_rules")


# =============================================================================
# API Input Schemas
# =============================================================================

class RecurrenceRuleCreate(RecurrenceRuleBase):
    """
    Schema for recurrence rule creation.

    user_id is NOT included - it will be injected from auth context.
    """

    pass


# =============================================================================
# API Output Schema
# =============================================================================

class RecurrenceRulePublic(RecurrenceRuleBase):
    """
    Schema for recurrence rule data in API responses.
    """

    id: UUID = Field(description="Unique recurrence rule identifier")
    user_id: UUID = Field(description="Owner user identifier")
    created_at: datetime = Field(description="Rule creation timestamp (UTC)")

    model_config = {"from_attributes": True}


__all__ = [
    "RecurrenceFrequency",
    "RecurrenceEndType",
    "RecurrenceRuleBase",
    "RecurrenceRule",
    "RecurrenceRuleCreate",
    "RecurrenceRulePublic",
]
