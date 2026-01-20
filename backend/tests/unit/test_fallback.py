"""
Unit tests for AI fallback handler.

Tests confidence-based fallback logic per Constitution Principle X.
"""

import pytest

from src.ai.fallback import FallbackHandler, FallbackResponse
from src.ai.types import CommandAction, ConfidenceLevel, InterpretedCommand


class TestFallbackHandler:
    """Tests for FallbackHandler class."""

    @pytest.fixture
    def handler(self, ai_config):
        """Create handler with test config."""
        return FallbackHandler(config=ai_config)

    def test_should_fallback_for_unknown_action(self, handler, unknown_command):
        """Test fallback triggers for unknown actions."""
        assert handler.should_fallback(unknown_command) is True

    def test_should_fallback_for_low_confidence(self, handler, low_confidence_command):
        """Test fallback triggers for low confidence."""
        assert handler.should_fallback(low_confidence_command) is True

    def test_should_not_fallback_for_high_confidence(self, handler, high_confidence_add_command):
        """Test no fallback for high confidence commands."""
        assert handler.should_fallback(high_confidence_add_command) is False

    def test_should_confirm_for_medium_confidence(self, handler, medium_confidence_delete_command):
        """Test confirmation required for medium confidence."""
        assert handler.should_confirm(medium_confidence_delete_command) is True

    def test_should_confirm_for_delete_action(self, handler):
        """Test confirmation always required for delete actions."""
        cmd = InterpretedCommand(
            original_text="delete task 1",
            action=CommandAction.DELETE,
            confidence=0.95,  # High confidence
            suggested_cli="bonsai delete 1",
        )
        assert handler.should_confirm(cmd) is True

    def test_should_not_confirm_for_high_confidence_non_delete(self, handler, high_confidence_add_command):
        """Test no confirmation for high confidence non-delete."""
        assert handler.should_confirm(high_confidence_add_command) is False

    def test_create_fallback_for_unknown(self, handler, unknown_command):
        """Test fallback response for unknown command."""
        response = handler.create_fallback(unknown_command)

        assert isinstance(response, FallbackResponse)
        assert "help" in response.message.lower() or "not sure" in response.message.lower()
        assert response.suggested_cli == "bonsai help"
        assert response.confidence_level == ConfidenceLevel.LOW

    def test_create_fallback_for_low_confidence(self, handler, low_confidence_command):
        """Test fallback response for low confidence command."""
        response = handler.create_fallback(low_confidence_command)

        assert isinstance(response, FallbackResponse)
        # Low confidence responses should have a message asking for clarification or indicating uncertainty
        assert response.message is not None and len(response.message) > 0
        assert response.confidence_level == ConfidenceLevel.LOW

    def test_create_confirmation_for_delete(self, handler, medium_confidence_delete_command):
        """Test confirmation response for delete."""
        response = handler.create_confirmation(medium_confidence_delete_command)

        assert isinstance(response, FallbackResponse)
        assert response.show_confirmation is True
        assert "sure" in response.message.lower() or "confirm" in response.message.lower()

    def test_create_ai_unavailable(self, handler):
        """Test response when AI is unavailable."""
        response = handler.create_ai_unavailable()

        assert isinstance(response, FallbackResponse)
        assert "unavailable" in response.message.lower()
        assert "bonsai" in response.message.lower()  # CLI commands mentioned
        assert response.confidence_level == ConfidenceLevel.LOW

    def test_create_timeout(self, handler):
        """Test response when AI times out."""
        response = handler.create_timeout()

        assert isinstance(response, FallbackResponse)
        assert "long" in response.message.lower() or "timeout" in response.message.lower()
        assert response.confidence_level == ConfidenceLevel.LOW


class TestFallbackConfidenceThresholds:
    """Tests for confidence threshold behavior."""

    @pytest.fixture
    def handler(self, ai_config):
        return FallbackHandler(config=ai_config)

    def test_boundary_high_confidence(self, handler):
        """Test exactly at high confidence threshold (0.8)."""
        cmd = InterpretedCommand(
            original_text="test",
            action=CommandAction.ADD,
            confidence=0.8,
            suggested_cli="bonsai add",
        )
        assert handler.should_fallback(cmd) is False
        assert handler.should_confirm(cmd) is False  # At threshold, no confirm

    def test_boundary_low_confidence(self, handler):
        """Test exactly at low confidence threshold (0.5)."""
        cmd = InterpretedCommand(
            original_text="test",
            action=CommandAction.ADD,
            confidence=0.5,
            suggested_cli="bonsai add",
        )
        assert handler.should_fallback(cmd) is False  # At threshold, no fallback
        assert handler.should_confirm(cmd) is True   # At threshold, needs confirm

    def test_below_low_confidence(self, handler):
        """Test below low confidence threshold."""
        cmd = InterpretedCommand(
            original_text="test",
            action=CommandAction.ADD,
            confidence=0.49,
            suggested_cli="bonsai add",
        )
        assert handler.should_fallback(cmd) is True
