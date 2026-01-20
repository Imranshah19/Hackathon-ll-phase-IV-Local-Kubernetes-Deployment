"""
Unit tests for ADD intent extraction in AIInterpreter.

Tests the interpretation of natural language task creation commands.

User Story 1: Natural Language Task Creation
"""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from src.ai.interpreter import AIInterpreter
from src.ai.types import CommandAction, ConfidenceLevel
from src.config.ai_config import AIConfig


@pytest.fixture
def interpreter():
    """Create interpreter with test config."""
    config = AIConfig(
        openai_api_key="test-key",
        ai_timeout_seconds=5.0,
    )
    return AIInterpreter(config=config)


@pytest.fixture
def mock_openai_add_response():
    """Mock OpenAI response for add intent."""
    return {
        "action": "add",
        "confidence": 0.95,
        "title": "buy groceries",
        "due_date": None,
        "needs_clarification": False,
    }


@pytest.fixture
def mock_openai_add_with_due_response():
    """Mock OpenAI response for add with due date."""
    return {
        "action": "add",
        "confidence": 0.92,
        "title": "buy groceries",
        "due_date": "tomorrow",
        "needs_clarification": False,
    }


@pytest.fixture
def mock_openai_ambiguous_add_response():
    """Mock OpenAI response for ambiguous add."""
    return {
        "action": "add",
        "confidence": 0.4,
        "title": None,
        "needs_clarification": True,
        "clarification_question": "What would you like to add?",
    }


class TestAddIntentExtraction:
    """Tests for ADD action intent extraction."""

    @pytest.mark.asyncio
    async def test_extract_simple_add_intent(self, interpreter, mock_openai_add_response):
        """Test extraction of simple add command."""
        with patch.object(interpreter, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_add_response

            result = await interpreter.interpret(
                user_message="Add a task to buy groceries",
                user_id=uuid4(),
            )

            assert result.action == CommandAction.ADD
            assert result.title == "buy groceries"
            assert result.confidence >= 0.8
            assert result.confidence_level == ConfidenceLevel.HIGH

    @pytest.mark.asyncio
    async def test_extract_add_with_due_date(self, interpreter, mock_openai_add_with_due_response):
        """Test extraction of add command with due date."""
        with patch.object(interpreter, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_add_with_due_response

            result = await interpreter.interpret(
                user_message="Add a task to buy groceries tomorrow",
                user_id=uuid4(),
            )

            assert result.action == CommandAction.ADD
            assert result.title == "buy groceries"
            assert result.due_date is not None
            # Due date should be tomorrow
            expected_date = date.today() + timedelta(days=1)
            assert result.due_date == expected_date

    @pytest.mark.asyncio
    async def test_extract_ambiguous_add_needs_clarification(
        self, interpreter, mock_openai_ambiguous_add_response
    ):
        """Test that ambiguous add commands request clarification."""
        with patch.object(interpreter, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_ambiguous_add_response

            result = await interpreter.interpret(
                user_message="add something",
                user_id=uuid4(),
            )

            assert result.action == CommandAction.ADD
            assert result.needs_clarification is True
            assert result.clarification_needed is not None
            assert result.confidence_level == ConfidenceLevel.LOW

    @pytest.mark.asyncio
    async def test_suggested_cli_for_add(self, interpreter, mock_openai_add_response):
        """Test that suggested CLI command is generated correctly."""
        with patch.object(interpreter, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_add_response

            result = await interpreter.interpret(
                user_message="Add a task to buy groceries",
                user_id=uuid4(),
            )

            assert "bonsai add" in result.suggested_cli
            assert "buy groceries" in result.suggested_cli

    @pytest.mark.asyncio
    async def test_suggested_cli_includes_due_date(self, interpreter, mock_openai_add_with_due_response):
        """Test that suggested CLI includes due date flag."""
        with patch.object(interpreter, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_add_with_due_response

            result = await interpreter.interpret(
                user_message="Add a task to buy groceries tomorrow",
                user_id=uuid4(),
            )

            assert "--due" in result.suggested_cli

    @pytest.mark.asyncio
    async def test_is_executable_for_high_confidence_add(self, interpreter, mock_openai_add_response):
        """Test that high confidence add is executable."""
        with patch.object(interpreter, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_add_response

            result = await interpreter.interpret(
                user_message="Add a task to buy groceries",
                user_id=uuid4(),
            )

            assert result.is_executable is True

    @pytest.mark.asyncio
    async def test_not_executable_for_ambiguous_add(
        self, interpreter, mock_openai_ambiguous_add_response
    ):
        """Test that ambiguous add is not executable."""
        with patch.object(interpreter, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_ambiguous_add_response

            result = await interpreter.interpret(
                user_message="add something",
                user_id=uuid4(),
            )

            assert result.is_executable is False


class TestAddIntentVariations:
    """Test various natural language patterns for add intent."""

    @pytest.fixture
    def base_add_response(self):
        """Base response for add variations."""
        return {
            "action": "add",
            "confidence": 0.9,
            "needs_clarification": False,
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message,expected_title", [
        ("Add a task to buy groceries", "buy groceries"),
        ("Create a reminder to call mom", "call mom"),
        ("Remember to finish the report", "finish the report"),
        ("I need to buy milk", "buy milk"),
        ("Don't forget to send email", "send email"),
    ])
    async def test_various_add_phrases(
        self, interpreter, base_add_response, message, expected_title
    ):
        """Test that various add phrases are recognized."""
        response = {**base_add_response, "title": expected_title}

        with patch.object(interpreter, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = response

            result = await interpreter.interpret(
                user_message=message,
                user_id=uuid4(),
            )

            assert result.action == CommandAction.ADD
            assert result.title == expected_title


class TestDueDateParsing:
    """Tests for due date parsing in interpreter."""

    @pytest.fixture
    def interpreter(self):
        """Create interpreter for date parsing tests."""
        config = AIConfig(openai_api_key="test-key")
        return AIInterpreter(config=config)

    def test_parse_today(self, interpreter):
        """Test parsing 'today' as due date."""
        result = interpreter._parse_due_date("today")
        assert result == date.today()

    def test_parse_tomorrow(self, interpreter):
        """Test parsing 'tomorrow' as due date."""
        result = interpreter._parse_due_date("tomorrow")
        assert result == date.today() + timedelta(days=1)

    def test_parse_next_week(self, interpreter):
        """Test parsing 'next week' as due date."""
        result = interpreter._parse_due_date("next week")
        assert result == date.today() + timedelta(weeks=1)

    def test_parse_in_days(self, interpreter):
        """Test parsing 'in 3 days' as due date."""
        result = interpreter._parse_due_date("in 3 days")
        assert result == date.today() + timedelta(days=3)

    def test_parse_iso_format(self, interpreter):
        """Test parsing ISO date format."""
        result = interpreter._parse_due_date("2026-01-25")
        assert result == date(2026, 1, 25)

    def test_parse_none(self, interpreter):
        """Test parsing None returns None."""
        result = interpreter._parse_due_date(None)
        assert result is None

    def test_parse_invalid(self, interpreter):
        """Test parsing invalid date returns None."""
        result = interpreter._parse_due_date("not a date")
        assert result is None


class TestCLICommandGeneration:
    """Tests for CLI command generation."""

    @pytest.fixture
    def interpreter(self):
        """Create interpreter for CLI tests."""
        config = AIConfig(openai_api_key="test-key")
        return AIInterpreter(config=config)

    def test_build_add_cli_simple(self, interpreter):
        """Test building simple add CLI command."""
        result = interpreter._build_cli_command(
            action=CommandAction.ADD,
            title="buy groceries",
            task_id=None,
            due_date=None,
            status_filter=None,
        )

        assert result == 'bonsai add "buy groceries"'

    def test_build_add_cli_with_due(self, interpreter):
        """Test building add CLI command with due date."""
        result = interpreter._build_cli_command(
            action=CommandAction.ADD,
            title="buy groceries",
            task_id=None,
            due_date=date(2026, 1, 25),
            status_filter=None,
        )

        assert 'bonsai add "buy groceries"' in result
        assert "--due 2026-01-25" in result

    def test_build_add_cli_no_title(self, interpreter):
        """Test building add CLI command with no title defaults to 'task'."""
        result = interpreter._build_cli_command(
            action=CommandAction.ADD,
            title=None,
            task_id=None,
            due_date=None,
            status_filter=None,
        )

        assert 'bonsai add "task"' in result
