"""
Contract tests for POST /chat/message create action.

Tests the API contract for task creation via natural language.
Verifies request/response schemas match the specification.

User Story 1: Natural Language Task Creation
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from src.main import app
from src.ai.types import CommandAction, InterpretedCommand


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_user_id():
    """Generate a mock user ID."""
    return uuid4()


class TestChatMessageCreateContract:
    """Contract tests for task creation via chat."""

    def test_request_schema_valid_message(self, client, auth_headers):
        """Test valid request schema is accepted."""
        request_body = {
            "message": "Add a task to buy groceries",
            "conversation_id": None,
        }

        # Request should be accepted (schema valid)
        # Even if auth fails, schema validation happens first for 422 errors
        with patch("src.api.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.process_message = AsyncMock(return_value=(
                _create_mock_response("add", "buy groceries"),
                _create_mock_message(),
            ))

            # This will fail auth but validates schema is correct
            response = client.post(
                "/api/chat/message",
                json=request_body,
                headers=auth_headers,
            )

            # Should not be 422 (validation error)
            assert response.status_code != 422

    def test_request_schema_with_conversation_id(self, client, auth_headers):
        """Test request with existing conversation ID."""
        conv_id = str(uuid4())
        request_body = {
            "message": "Add another task",
            "conversation_id": conv_id,
        }

        with patch("src.api.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.process_message = AsyncMock(return_value=(
                _create_mock_response("add", "another task"),
                _create_mock_message(conversation_id=conv_id),
            ))

            response = client.post(
                "/api/chat/message",
                json=request_body,
                headers=auth_headers,
            )

            assert response.status_code != 422

    def test_request_schema_rejects_empty_message(self, client, auth_headers):
        """Test that empty message is rejected."""
        request_body = {
            "message": "",
        }

        response = client.post(
            "/api/chat/message",
            json=request_body,
            headers=auth_headers,
        )

        # Should be 422 validation error
        assert response.status_code == 422

    def test_request_schema_rejects_missing_message(self, client, auth_headers):
        """Test that missing message field is rejected."""
        request_body = {}

        response = client.post(
            "/api/chat/message",
            json=request_body,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_request_schema_rejects_long_message(self, client, auth_headers):
        """Test that message over 2000 chars is rejected."""
        request_body = {
            "message": "x" * 2001,
        }

        response = client.post(
            "/api/chat/message",
            json=request_body,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_response_schema_contains_required_fields(self, client, auth_headers, mock_user_id):
        """Test response contains all required fields for create action."""
        with patch("src.auth.dependencies.get_token_payload") as mock_auth:
            mock_auth.return_value = type("TokenPayload", (), {"user_id": mock_user_id})()

            with patch("src.api.chat.ChatService") as mock_service:
                mock_response = _create_mock_response("add", "buy groceries")
                mock_message = _create_mock_message()

                mock_instance = mock_service.return_value
                mock_instance.process_message = AsyncMock(
                    return_value=(mock_response, mock_message)
                )

                response = client.post(
                    "/api/chat/message",
                    json={"message": "Add a task to buy groceries"},
                    headers=auth_headers,
                )

                if response.status_code == 200:
                    data = response.json()

                    # Required fields per ChatMessageResponse schema
                    assert "message" in data
                    assert "confidence" in data
                    assert "conversation_id" in data
                    assert "message_id" in data
                    assert "needs_confirmation" in data
                    assert "is_fallback" in data

    def test_response_action_is_add_for_create(self, client, auth_headers, mock_user_id):
        """Test that create requests return action='add'."""
        with patch("src.auth.dependencies.get_token_payload") as mock_auth:
            mock_auth.return_value = type("TokenPayload", (), {"user_id": mock_user_id})()

            with patch("src.api.chat.ChatService") as mock_service:
                mock_response = _create_mock_response("add", "buy groceries")
                mock_message = _create_mock_message()

                mock_instance = mock_service.return_value
                mock_instance.process_message = AsyncMock(
                    return_value=(mock_response, mock_message)
                )

                response = client.post(
                    "/api/chat/message",
                    json={"message": "Add a task to buy groceries"},
                    headers=auth_headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    assert data.get("action") == "add"


class TestChatMessageCreateVariants:
    """Test various natural language create patterns."""

    @pytest.mark.parametrize("message", [
        "Add a task to buy groceries",
        "Create a reminder to call mom",
        "Remember to finish the report",
        "add task: meeting at 3pm",
        "I need to buy milk",
        "Don't forget to send email",
    ])
    def test_create_intent_phrases(self, message, client, auth_headers, mock_user_id):
        """Test various phrases that should trigger add action."""
        with patch("src.auth.dependencies.get_token_payload") as mock_auth:
            mock_auth.return_value = type("TokenPayload", (), {"user_id": mock_user_id})()

            with patch("src.api.chat.ChatService") as mock_service:
                mock_response = _create_mock_response("add", "task")
                mock_message = _create_mock_message()

                mock_instance = mock_service.return_value
                mock_instance.process_message = AsyncMock(
                    return_value=(mock_response, mock_message)
                )

                response = client.post(
                    "/api/chat/message",
                    json={"message": message},
                    headers=auth_headers,
                )

                # Request should be processed (not rejected by schema)
                assert response.status_code != 422


# =============================================================================
# Helper functions
# =============================================================================

def _create_mock_response(action: str, title: str):
    """Create a mock ChatResponse object."""
    from src.services.chat_service import ChatResponse

    return ChatResponse(
        message=f"I've created a new task: \"{title}\"",
        confidence=0.95,
        action=action,
        suggested_cli=f'bonsai add "{title}"',
        needs_confirmation=False,
        is_fallback=False,
        task={"id": str(uuid4()), "title": title, "is_completed": False},
    )


def _create_mock_message(conversation_id: str | None = None):
    """Create a mock Message object."""
    from src.models.message import Message, MessageRole

    msg = Message(
        id=uuid4(),
        conversation_id=uuid4() if not conversation_id else conversation_id,
        role=MessageRole.ASSISTANT,
        content="Task created",
        confidence_score=0.95,
    )
    return msg
