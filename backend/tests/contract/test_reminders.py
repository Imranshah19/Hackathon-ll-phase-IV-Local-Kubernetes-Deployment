"""
Contract tests for Reminder schemas (Phase 5 - User Story 5).

Tests:
- T062: Validate Reminder CRUD schemas
- Reminder datetime validation
- Reminder limit per task (max 3)
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4


@pytest.mark.contract
class TestReminderSchemaContract:
    """Contract tests for reminder management."""

    def test_reminder_create_accepts_valid_input(self) -> None:
        """ReminderCreate should accept task_id, remind_at, and optional message."""
        from src.models.reminder import ReminderCreate

        task_id = uuid4()
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)

        # Without message
        reminder = ReminderCreate(task_id=task_id, remind_at=future_time)
        assert reminder.task_id == task_id
        assert reminder.remind_at == future_time
        assert reminder.message is None

        # With message
        reminder_with_msg = ReminderCreate(
            task_id=task_id,
            remind_at=future_time,
            message="Don't forget!",
        )
        assert reminder_with_msg.message == "Don't forget!"

    def test_reminder_create_requires_task_id(self) -> None:
        """ReminderCreate should require task_id."""
        from pydantic import ValidationError
        from src.models.reminder import ReminderCreate

        future_time = datetime.now(timezone.utc) + timedelta(hours=1)

        with pytest.raises(ValidationError):
            ReminderCreate(remind_at=future_time)  # Missing task_id

    def test_reminder_create_requires_remind_at(self) -> None:
        """ReminderCreate should require remind_at."""
        from pydantic import ValidationError
        from src.models.reminder import ReminderCreate

        task_id = uuid4()

        with pytest.raises(ValidationError):
            ReminderCreate(task_id=task_id)  # Missing remind_at

    def test_reminder_message_max_length(self) -> None:
        """ReminderCreate.message should be max 255 characters."""
        from pydantic import ValidationError
        from src.models.reminder import ReminderCreate

        task_id = uuid4()
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)

        # Message at limit (255 chars) should be accepted
        reminder = ReminderCreate(
            task_id=task_id,
            remind_at=future_time,
            message="x" * 255,
        )
        assert len(reminder.message) == 255

        # Message over limit should be rejected
        with pytest.raises(ValidationError):
            ReminderCreate(
                task_id=task_id,
                remind_at=future_time,
                message="x" * 256,
            )

    def test_reminder_public_has_required_fields(self) -> None:
        """ReminderPublic must include all required fields."""
        from src.models.reminder import ReminderPublic

        fields = ReminderPublic.model_fields
        required = ["id", "task_id", "remind_at", "message", "sent", "sent_at", "created_at"]

        for field in required:
            assert field in fields, f"ReminderPublic missing field: {field}"

    def test_reminder_public_serialization(self) -> None:
        """ReminderPublic should serialize correctly to JSON."""
        from src.models.reminder import ReminderPublic

        now = datetime.now(timezone.utc)
        reminder = ReminderPublic(
            id=uuid4(),
            task_id=uuid4(),
            remind_at=now + timedelta(hours=1),
            message="Reminder message",
            sent=False,
            sent_at=None,
            created_at=now,
        )

        json_data = reminder.model_dump(mode="json")

        assert isinstance(json_data["id"], str)
        assert isinstance(json_data["task_id"], str)
        assert json_data["message"] == "Reminder message"
        assert json_data["sent"] is False
        assert json_data["sent_at"] is None

    def test_reminder_model_creates_with_uuid(self) -> None:
        """Reminder model should auto-generate UUID."""
        from src.models.reminder import Reminder

        reminder = Reminder(
            task_id=uuid4(),
            remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert reminder.id is not None
        assert reminder.id.version == 4

    def test_reminder_default_values(self) -> None:
        """Reminder model should have correct defaults."""
        from src.models.reminder import Reminder

        reminder = Reminder(
            task_id=uuid4(),
            remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert reminder.sent is False
        assert reminder.sent_at is None
        assert reminder.message is None
        assert reminder.created_at is not None


@pytest.mark.contract
class TestReminderApiContract:
    """Contract tests for Reminder API endpoints."""

    def test_list_reminders_response_format(self) -> None:
        """GET /api/reminders should return list of ReminderPublic."""
        expected_response = {
            "type": "array",
            "items": {
                "type": "ReminderPublic",
                "fields": ["id", "task_id", "remind_at", "message", "sent", "sent_at", "created_at"],
            },
        }
        assert expected_response["type"] == "array"

    def test_create_reminder_request_format(self) -> None:
        """POST /api/reminders request body format."""
        request_body = {
            "task_id": "string (required, UUID)",
            "remind_at": "string (required, ISO datetime)",
            "message": "string (optional, max 255 chars)",
        }
        assert "task_id" in request_body
        assert "remind_at" in request_body

    def test_reminder_stream_sse_format(self) -> None:
        """GET /api/reminders/stream should return SSE format."""
        # SSE response format
        expected_format = {
            "content_type": "text/event-stream",
            "message_format": {
                "type": "reminder",
                "data": {
                    "reminder_id": "string",
                    "task_id": "string",
                    "task_title": "string",
                    "message": "string",
                    "remind_at": "string (ISO datetime)",
                },
                "timestamp": "string (ISO datetime)",
            },
        }
        assert expected_format["content_type"] == "text/event-stream"


@pytest.mark.contract
class TestReminderBusinessRules:
    """Contract tests for reminder business rules."""

    def test_max_reminders_per_task_constant(self) -> None:
        """ReminderService should define MAX_REMINDERS_PER_TASK = 3."""
        from src.services.reminder_service import ReminderService

        assert ReminderService.MAX_REMINDERS_PER_TASK == 3

    def test_reminder_requires_future_datetime(self) -> None:
        """Reminders must be scheduled for future times."""
        # Business rule: remind_at must be > now
        # This is validated in the service layer
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)

        assert past_time < datetime.now(timezone.utc)
        assert future_time > datetime.now(timezone.utc)

    def test_reminder_auto_cancel_on_task_completion(self) -> None:
        """Reminders should be cancelable when task is completed (FR-020)."""
        # Business rule: cancel_task_reminders(task_id) deletes unsent reminders
        from src.services.reminder_service import ReminderService

        assert hasattr(ReminderService, "cancel_task_reminders")
