"""
Unit tests for AI types and data structures.

Tests the InterpretedCommand dataclass and related types.
"""

import pytest
from datetime import date
from uuid import uuid4

from src.ai.types import (
    CommandAction,
    ConfidenceLevel,
    InterpretedCommand,
    StatusFilter,
)


class TestCommandAction:
    """Tests for CommandAction enum."""

    def test_all_actions_defined(self):
        """Verify all expected actions are defined."""
        assert CommandAction.ADD.value == "add"
        assert CommandAction.LIST.value == "list"
        assert CommandAction.UPDATE.value == "update"
        assert CommandAction.DELETE.value == "delete"
        assert CommandAction.COMPLETE.value == "complete"
        assert CommandAction.UNKNOWN.value == "unknown"


class TestConfidenceLevel:
    """Tests for ConfidenceLevel enum."""

    def test_all_levels_defined(self):
        """Verify all confidence levels are defined."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"


class TestStatusFilter:
    """Tests for StatusFilter enum."""

    def test_all_filters_defined(self):
        """Verify all status filters are defined."""
        assert StatusFilter.PENDING.value == "pending"
        assert StatusFilter.COMPLETED.value == "completed"
        assert StatusFilter.ALL.value == "all"


class TestInterpretedCommand:
    """Tests for InterpretedCommand dataclass."""

    def test_create_basic_command(self):
        """Test creating a basic interpreted command."""
        cmd = InterpretedCommand(
            original_text="Add a task to buy groceries",
            action=CommandAction.ADD,
            confidence=0.9,
            suggested_cli='bonsai add "buy groceries"',
        )

        assert cmd.original_text == "Add a task to buy groceries"
        assert cmd.action == CommandAction.ADD
        assert cmd.confidence == 0.9
        assert cmd.suggested_cli == 'bonsai add "buy groceries"'

    def test_confidence_level_high(self):
        """Test HIGH confidence level classification."""
        cmd = InterpretedCommand(
            original_text="test",
            action=CommandAction.ADD,
            confidence=0.85,
            suggested_cli="bonsai add",
        )
        assert cmd.confidence_level == ConfidenceLevel.HIGH

    def test_confidence_level_medium(self):
        """Test MEDIUM confidence level classification."""
        cmd = InterpretedCommand(
            original_text="test",
            action=CommandAction.ADD,
            confidence=0.65,
            suggested_cli="bonsai add",
        )
        assert cmd.confidence_level == ConfidenceLevel.MEDIUM

    def test_confidence_level_low(self):
        """Test LOW confidence level classification."""
        cmd = InterpretedCommand(
            original_text="test",
            action=CommandAction.ADD,
            confidence=0.3,
            suggested_cli="bonsai add",
        )
        assert cmd.confidence_level == ConfidenceLevel.LOW

    def test_needs_clarification_with_question(self):
        """Test needs_clarification when question is set."""
        cmd = InterpretedCommand(
            original_text="add something",
            action=CommandAction.ADD,
            confidence=0.6,
            suggested_cli="bonsai add",
            clarification_needed="What would you like to add?",
        )
        assert cmd.needs_clarification is True

    def test_needs_clarification_with_multiple_matches(self):
        """Test needs_clarification when multiple matches exist."""
        cmd = InterpretedCommand(
            original_text="delete the grocery task",
            action=CommandAction.DELETE,
            confidence=0.8,
            suggested_cli="bonsai delete",
            multiple_matches=[uuid4(), uuid4()],
        )
        assert cmd.needs_clarification is True

    def test_needs_clarification_with_unknown_action(self):
        """Test needs_clarification for unknown actions."""
        cmd = InterpretedCommand(
            original_text="blah blah",
            action=CommandAction.UNKNOWN,
            confidence=0.1,
            suggested_cli="bonsai help",
        )
        assert cmd.needs_clarification is True

    def test_is_executable_high_confidence(self):
        """Test is_executable for high confidence commands."""
        cmd = InterpretedCommand(
            original_text="add groceries",
            action=CommandAction.ADD,
            confidence=0.9,
            suggested_cli="bonsai add groceries",
            title="groceries",
        )
        assert cmd.is_executable is True

    def test_is_executable_false_for_unknown(self):
        """Test is_executable is False for unknown actions."""
        cmd = InterpretedCommand(
            original_text="test",
            action=CommandAction.UNKNOWN,
            confidence=0.9,
            suggested_cli="bonsai help",
        )
        assert cmd.is_executable is False

    def test_is_executable_false_for_low_confidence(self):
        """Test is_executable is False for low confidence."""
        cmd = InterpretedCommand(
            original_text="add groceries",
            action=CommandAction.ADD,
            confidence=0.3,
            suggested_cli="bonsai add groceries",
        )
        assert cmd.is_executable is False

    def test_to_dict_serialization(self):
        """Test to_dict produces valid JSON-serializable dict."""
        task_id = uuid4()
        cmd = InterpretedCommand(
            original_text="complete task 1",
            action=CommandAction.COMPLETE,
            confidence=0.85,
            suggested_cli=f"bonsai complete {task_id}",
            task_id=task_id,
            title=None,
            due_date=date(2026, 1, 20),
            status_filter=StatusFilter.PENDING,
        )

        result = cmd.to_dict()

        assert result["original_text"] == "complete task 1"
        assert result["action"] == "complete"
        assert result["confidence"] == 0.85
        assert result["task_id"] == str(task_id)
        assert result["due_date"] == "2026-01-20"
        assert result["status_filter"] == "pending"
        assert result["confidence_level"] == "high"
        assert result["is_executable"] is True
