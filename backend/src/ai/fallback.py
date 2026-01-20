"""
Confidence-based fallback logic for AI Chat.

This module implements graceful degradation when AI interpretation
has low confidence or when the AI service is unavailable.

Implements:
- FR-008: Provide CLI command alternatives when AI fails
- FR-011: Timeout fallback to CLI mode
- Constitution Principle X: Graceful AI Degradation

Confidence Tiers (from research.md RQ-005):
- HIGH (>0.8): Execute immediately
- MEDIUM (0.5-0.8): Show interpreted command, ask confirmation
- LOW (<0.5): Suggest CLI command, ask for clarification
"""

from dataclasses import dataclass
from typing import Any

from src.ai.types import ConfidenceLevel, InterpretedCommand, CommandAction
from src.config.ai_config import AIConfig, get_ai_config


@dataclass
class FallbackResponse:
    """Response when AI fallback is triggered."""

    message: str
    suggested_cli: str
    show_confirmation: bool = False
    interpreted_action: str | None = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW


class FallbackHandler:
    """
    Handles fallback scenarios when AI interpretation is uncertain.

    Provides helpful CLI alternatives and guidance to users.
    """

    def __init__(self, config: AIConfig | None = None):
        """Initialize with configuration."""
        self.config = config or get_ai_config()

    def should_fallback(self, command: InterpretedCommand) -> bool:
        """
        Determine if fallback should be triggered.

        Args:
            command: The interpreted command

        Returns:
            True if fallback should be triggered
        """
        # Always fallback for unknown actions
        if command.action == CommandAction.UNKNOWN:
            return True

        # Fallback for low confidence
        if command.confidence < self.config.confidence_threshold_low:
            return True

        # Fallback if clarification is needed
        if command.needs_clarification:
            return True

        return False

    def should_confirm(self, command: InterpretedCommand) -> bool:
        """
        Determine if confirmation should be requested.

        Args:
            command: The interpreted command

        Returns:
            True if user confirmation should be requested
        """
        # Medium confidence requires confirmation
        if (
            self.config.confidence_threshold_low
            <= command.confidence
            < self.config.confidence_threshold_high
        ):
            return True

        # Destructive actions (delete) always confirm
        if command.action == CommandAction.DELETE:
            return True

        return False

    def create_fallback(self, command: InterpretedCommand) -> FallbackResponse:
        """
        Create a fallback response for low-confidence interpretation.

        Args:
            command: The interpreted command

        Returns:
            FallbackResponse with CLI suggestion
        """
        if command.action == CommandAction.UNKNOWN:
            return FallbackResponse(
                message=self._get_help_message(),
                suggested_cli="bonsai help",
                show_confirmation=False,
                confidence_level=ConfidenceLevel.LOW,
            )

        if command.needs_clarification:
            return FallbackResponse(
                message=command.clarification_needed or "Could you clarify what you'd like to do?",
                suggested_cli=command.suggested_cli,
                show_confirmation=False,
                interpreted_action=command.action.value,
                confidence_level=command.confidence_level,
            )

        # Low confidence but has an action
        action_desc = self._describe_action(command)
        return FallbackResponse(
            message=f"I think you want to {action_desc}, but I'm not certain. You can use this command directly:",
            suggested_cli=command.suggested_cli,
            show_confirmation=False,
            interpreted_action=command.action.value,
            confidence_level=command.confidence_level,
        )

    def create_confirmation(self, command: InterpretedCommand) -> FallbackResponse:
        """
        Create a confirmation request for medium-confidence interpretation.

        Args:
            command: The interpreted command

        Returns:
            FallbackResponse requesting confirmation
        """
        action_desc = self._describe_action(command)

        if command.action == CommandAction.DELETE:
            message = f"Are you sure you want to {action_desc}? This cannot be undone."
        else:
            message = f"I'll {action_desc}. Is this correct?"

        return FallbackResponse(
            message=message,
            suggested_cli=command.suggested_cli,
            show_confirmation=True,
            interpreted_action=command.action.value,
            confidence_level=command.confidence_level,
        )

    def create_ai_unavailable(self) -> FallbackResponse:
        """Create response when AI service is unavailable."""
        return FallbackResponse(
            message=(
                "I'm temporarily unavailable. You can still manage your tasks using CLI commands:\n\n"
                "• `bonsai add \"task title\"` - Create a task\n"
                "• `bonsai list` - Show all tasks\n"
                "• `bonsai complete <id>` - Mark task done\n"
                "• `bonsai delete <id>` - Remove a task"
            ),
            suggested_cli="bonsai help",
            show_confirmation=False,
            confidence_level=ConfidenceLevel.LOW,
        )

    def create_timeout(self) -> FallbackResponse:
        """Create response when AI times out."""
        return FallbackResponse(
            message=(
                "I'm taking too long to respond. Please try using a CLI command directly, "
                "or try rephrasing your request more simply."
            ),
            suggested_cli="bonsai help",
            show_confirmation=False,
            confidence_level=ConfidenceLevel.LOW,
        )

    def _describe_action(self, command: InterpretedCommand) -> str:
        """Generate human-readable description of the action."""
        if command.action == CommandAction.ADD:
            title = command.title or "a task"
            return f"create a task called \"{title}\""

        elif command.action == CommandAction.LIST:
            if command.status_filter:
                return f"show your {command.status_filter.value} tasks"
            return "show all your tasks"

        elif command.action == CommandAction.COMPLETE:
            return f"mark task {command.task_id or 'that'} as complete"

        elif command.action == CommandAction.UPDATE:
            parts = [f"update task {command.task_id or 'that'}"]
            if command.title:
                parts.append(f"title to \"{command.title}\"")
            return " ".join(parts)

        elif command.action == CommandAction.DELETE:
            return f"delete task {command.task_id or 'that'}"

        return "perform that action"

    def _get_help_message(self) -> str:
        """Get the help message for unknown commands."""
        return (
            "I'm not sure what you'd like to do. Here are some things I can help with:\n\n"
            "• \"Add a task to buy groceries\"\n"
            "• \"Show my pending tasks\"\n"
            "• \"Mark task 3 as done\"\n"
            "• \"Delete the meeting task\"\n\n"
            "Or you can use CLI commands directly."
        )


# Singleton instance
_fallback_handler: FallbackHandler | None = None


def get_fallback_handler() -> FallbackHandler:
    """Get the singleton fallback handler."""
    global _fallback_handler
    if _fallback_handler is None:
        _fallback_handler = FallbackHandler()
    return _fallback_handler


__all__ = ["FallbackHandler", "FallbackResponse", "get_fallback_handler"]
