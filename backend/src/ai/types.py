"""
Type definitions for AI Chat interpretation.

This module defines the InterpretedCommand dataclass which represents
an AI-interpreted user intent. It is used for the processing pipeline
only and is NOT persisted to the database.

From data-model.md:
- original_text: User's raw input
- action: 'add' | 'list' | 'update' | 'delete' | 'complete' | 'unknown'
- task_id: Target task ID (for update/delete/complete)
- title: Task title (for add/update)
- due_date: Due date (for add/update)
- status_filter: 'pending' | 'completed' | 'all' (for list)
- confidence: 0.0-1.0 interpretation confidence
- clarification_needed: Question to ask user if ambiguous
- suggested_cli: Equivalent Bonsai CLI command

Phase 5 additions:
- detected_language: Language of the input (en/ur/mixed)
- priority: Priority level extracted from input (1-5)
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Literal, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from src.ai.urdu import Language


class CommandAction(str, Enum):
    """Possible actions from natural language interpretation."""

    ADD = "add"
    LIST = "list"
    UPDATE = "update"
    DELETE = "delete"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class StatusFilter(str, Enum):
    """Task status filter for list operations."""

    PENDING = "pending"
    COMPLETED = "completed"
    ALL = "all"


class ConfidenceLevel(str, Enum):
    """
    Confidence level categories for AI interpretation.

    From research.md RQ-005:
    - HIGH (>0.8): Execute immediately
    - MEDIUM (0.5-0.8): Show interpreted command, ask confirmation
    - LOW (<0.5): Suggest CLI command, ask for clarification
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class InterpretedCommand:
    """
    Runtime representation of an AI-interpreted user intent.

    This is used for the processing pipeline only and is NOT persisted.
    It contains all the information needed to execute a Bonsai CLI command.

    Attributes:
        original_text: The user's raw natural language input
        action: The interpreted action (add, list, update, delete, complete, unknown)
        confidence: Interpretation confidence score (0.0-1.0)
        suggested_cli: The equivalent Bonsai CLI command

        Optional action-specific fields:
        task_id: Target task UUID (for update/delete/complete)
        title: Task title (for add/update)
        due_date: Task due date (for add/update)
        status_filter: Filter for list operations

        Clarification fields:
        clarification_needed: Question to ask user if input is ambiguous
        multiple_matches: List of task IDs if multiple tasks match a reference
    """

    # Required fields
    original_text: str
    action: CommandAction
    confidence: float
    suggested_cli: str

    # Action-specific fields (optional)
    task_id: UUID | None = None
    title: str | None = None
    due_date: date | None = None
    status_filter: StatusFilter | None = None

    # Phase 5: Additional fields
    priority: int | None = None  # 1-5 priority level
    detected_language: "Language | None" = None  # en/ur/mixed

    # Clarification fields
    clarification_needed: str | None = None
    multiple_matches: list[UUID] = field(default_factory=list)

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """
        Categorize confidence into HIGH/MEDIUM/LOW.

        Returns:
            ConfidenceLevel based on configured thresholds.
        """
        if self.confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    @property
    def needs_clarification(self) -> bool:
        """Check if this command needs user clarification."""
        return (
            self.clarification_needed is not None
            or len(self.multiple_matches) > 1
            or self.action == CommandAction.UNKNOWN
        )

    @property
    def is_executable(self) -> bool:
        """Check if this command can be executed without clarification."""
        return (
            self.action != CommandAction.UNKNOWN
            and not self.needs_clarification
            and self.confidence_level != ConfidenceLevel.LOW
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "original_text": self.original_text,
            "action": self.action.value,
            "confidence": self.confidence,
            "suggested_cli": self.suggested_cli,
            "task_id": str(self.task_id) if self.task_id else None,
            "title": self.title,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status_filter": self.status_filter.value if self.status_filter else None,
            "priority": self.priority,
            "detected_language": self.detected_language.value if self.detected_language else None,
            "clarification_needed": self.clarification_needed,
            "multiple_matches": [str(m) for m in self.multiple_matches],
            "confidence_level": self.confidence_level.value,
            "needs_clarification": self.needs_clarification,
            "is_executable": self.is_executable,
        }


__all__ = [
    "CommandAction",
    "StatusFilter",
    "ConfidenceLevel",
    "InterpretedCommand",
]
