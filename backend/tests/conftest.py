"""
Pytest configuration and shared fixtures for the skills library tests.

Test Categories:
- unit: Fast, isolated tests for individual components
- integration: Tests that may use database or external services
- contract: Schema validation tests for skill inputs/outputs
"""

import pytest
from typing import Any, Generator
from uuid import uuid4


# =============================================================================
# Markers
# =============================================================================

def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "contract: Contract tests (schema validation)")
    config.addinivalue_line("markers", "slow: Slow tests (AI operations, etc.)")


# =============================================================================
# Common Fixtures
# =============================================================================

@pytest.fixture
def correlation_id() -> str:
    """Generate a unique correlation ID for test tracing."""
    return str(uuid4())


@pytest.fixture
def sample_user_id() -> str:
    """Generate a sample user UUID."""
    return str(uuid4())


@pytest.fixture
def sample_task_id() -> str:
    """Generate a sample task UUID."""
    return str(uuid4())


@pytest.fixture
def sample_task_data() -> dict[str, Any]:
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "A test task description",
        "is_completed": False,
        "metadata": {},
    }


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
    }


# =============================================================================
# Skill Testing Fixtures
# =============================================================================

@pytest.fixture
def skill_context(correlation_id: str, sample_user_id: str) -> dict[str, Any]:
    """Base context for skill execution."""
    return {
        "correlation_id": correlation_id,
        "user_id": sample_user_id,
        "timestamp": "2026-01-12T00:00:00Z",
    }


# =============================================================================
# Mock Fixtures (to be expanded in Phase 2)
# =============================================================================

@pytest.fixture
def mock_database() -> Generator[None, None, None]:
    """Mock database connection for unit tests."""
    # TODO: Implement in Phase 2 when database is configured
    yield


@pytest.fixture
def mock_ai_service() -> Generator[None, None, None]:
    """Mock AI service for unit tests."""
    # TODO: Implement in Phase 8 when AI skills are implemented
    yield


# =============================================================================
# Data Schema Testing Fixtures (Phase 2 - Data Schemas)
# =============================================================================

@pytest.fixture
def valid_user_email() -> str:
    """Valid email for user creation tests."""
    return "testuser@example.com"


@pytest.fixture
def valid_password() -> str:
    """Valid password meeting minimum requirements (8+ chars)."""
    return "SecurePass123!"


@pytest.fixture
def invalid_emails() -> list[str]:
    """List of invalid email formats for validation testing."""
    return [
        "not-an-email",
        "@missing-local.com",
        "missing-domain@",
        "spaces in@email.com",
        "",
    ]


@pytest.fixture
def invalid_passwords() -> list[str]:
    """List of invalid passwords (too short)."""
    return [
        "",
        "1234567",  # 7 chars - below minimum
        "short",    # 5 chars
    ]


@pytest.fixture
def valid_task_title() -> str:
    """Valid task title for testing."""
    return "Buy groceries"


@pytest.fixture
def valid_task_description() -> str:
    """Valid task description for testing."""
    return "Milk, eggs, bread, and vegetables from the store"


@pytest.fixture
def invalid_task_titles() -> list[str]:
    """List of invalid task titles for validation testing."""
    return [
        "",                    # Empty
        "x" * 256,            # Exceeds 255 char limit
    ]


@pytest.fixture
def invalid_task_descriptions() -> list[str]:
    """List of invalid task descriptions for validation testing."""
    return [
        "x" * 4001,           # Exceeds 4000 char limit
    ]


# =============================================================================
# Phase 3 AI Chat Fixtures
# =============================================================================

from src.ai.types import CommandAction, InterpretedCommand, StatusFilter
from src.config.ai_config import AIConfig


@pytest.fixture
def ai_config() -> AIConfig:
    """Provide test AI configuration."""
    return AIConfig(
        openai_api_key="test-key",
        ai_timeout_seconds=5.0,
        confidence_threshold_high=0.8,
        confidence_threshold_low=0.5,
    )


@pytest.fixture
def high_confidence_add_command() -> InterpretedCommand:
    """Provide a high-confidence ADD command for testing."""
    return InterpretedCommand(
        original_text="Add a task to buy groceries",
        action=CommandAction.ADD,
        confidence=0.95,
        suggested_cli='bonsai add "buy groceries"',
        title="buy groceries",
    )


@pytest.fixture
def low_confidence_command() -> InterpretedCommand:
    """Provide a low-confidence command for testing."""
    return InterpretedCommand(
        original_text="maybe do something",
        action=CommandAction.ADD,
        confidence=0.3,
        suggested_cli='bonsai add "something"',
        clarification_needed="What would you like to add?",
    )


@pytest.fixture
def medium_confidence_delete_command() -> InterpretedCommand:
    """Provide a medium-confidence DELETE command for testing."""
    task_id = uuid4()
    return InterpretedCommand(
        original_text="delete task 1",
        action=CommandAction.DELETE,
        confidence=0.65,
        suggested_cli=f"bonsai delete {task_id}",
        task_id=task_id,
    )


@pytest.fixture
def list_pending_command() -> InterpretedCommand:
    """Provide a LIST command with pending filter."""
    return InterpretedCommand(
        original_text="show my pending tasks",
        action=CommandAction.LIST,
        confidence=0.9,
        suggested_cli="bonsai list --pending",
        status_filter=StatusFilter.PENDING,
    )


@pytest.fixture
def unknown_command() -> InterpretedCommand:
    """Provide an UNKNOWN command for testing."""
    return InterpretedCommand(
        original_text="blah blah blah",
        action=CommandAction.UNKNOWN,
        confidence=0.1,
        suggested_cli="bonsai help",
    )


@pytest.fixture
def sample_tasks_for_ai() -> list[dict[str, Any]]:
    """Provide sample tasks for AI context."""
    return [
        {"id": str(uuid4()), "title": "Buy groceries", "is_completed": False},
        {"id": str(uuid4()), "title": "Call mom", "is_completed": False},
        {"id": str(uuid4()), "title": "Finish report", "is_completed": True},
    ]
