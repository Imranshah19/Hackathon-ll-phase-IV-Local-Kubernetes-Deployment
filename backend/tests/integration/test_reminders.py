"""
Integration tests for Reminder CRUD lifecycle (Phase 5 - User Story 5).

Tests:
- T063: Full CRUD lifecycle for reminders
- Auto-cancel on task completion
- Multiple reminders per task
- Background checker logic
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlmodel import Session, create_engine, SQLModel


@pytest.fixture
def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(test_engine):
    """Provide a database session for testing."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def test_user(session):
    """Create a test user."""
    from src.models.user import User

    user = User(
        email="test@example.com",
        hashed_password="hashed_password_here",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_task(session, test_user):
    """Create a test task."""
    from src.models.task import Task

    task = Task(
        user_id=test_user.id,
        title="Test Task",
        description="A task for reminder testing",
        due=datetime.now(timezone.utc) + timedelta(days=1),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.mark.integration
class TestReminderCRUDLifecycle:
    """Integration tests for reminder CRUD operations."""

    def test_create_reminder_success(self, session, test_user, test_task) -> None:
        """Should create a reminder for a task."""
        from src.models.reminder import ReminderCreate
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)

        reminder = service.create_reminder(
            ReminderCreate(
                task_id=test_task.id,
                remind_at=future_time,
                message="Don't forget!",
            )
        )

        assert reminder.id is not None
        assert reminder.task_id == test_task.id
        assert reminder.message == "Don't forget!"
        assert reminder.sent is False

    def test_create_reminder_rejects_past_time(self, session, test_user, test_task) -> None:
        """Should reject reminder with past remind_at."""
        from src.models.reminder import ReminderCreate
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)

        with pytest.raises(ValueError, match="future"):
            service.create_reminder(
                ReminderCreate(
                    task_id=test_task.id,
                    remind_at=past_time,
                )
            )

    def test_create_reminder_rejects_nonexistent_task(self, session, test_user) -> None:
        """Should reject reminder for nonexistent task."""
        from src.models.reminder import ReminderCreate
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)

        with pytest.raises(ValueError, match="not found"):
            service.create_reminder(
                ReminderCreate(
                    task_id=uuid4(),  # Nonexistent task
                    remind_at=future_time,
                )
            )

    def test_list_reminders(self, session, test_user, test_task) -> None:
        """Should list all reminders for a user."""
        from src.models.reminder import ReminderCreate
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)

        # Create multiple reminders
        for i in range(2):
            service.create_reminder(
                ReminderCreate(
                    task_id=test_task.id,
                    remind_at=datetime.now(timezone.utc) + timedelta(hours=i + 1),
                )
            )

        reminders = service.list_reminders()
        assert len(reminders) == 2

    def test_list_reminders_filter_by_task(self, session, test_user, test_task) -> None:
        """Should filter reminders by task_id."""
        from src.models.reminder import ReminderCreate
        from src.models.task import Task
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)

        # Create another task
        task2 = Task(
            user_id=test_user.id,
            title="Second Task",
        )
        session.add(task2)
        session.commit()
        session.refresh(task2)

        # Create reminders for both tasks
        service.create_reminder(
            ReminderCreate(
                task_id=test_task.id,
                remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        service.create_reminder(
            ReminderCreate(
                task_id=task2.id,
                remind_at=datetime.now(timezone.utc) + timedelta(hours=2),
            )
        )

        # Filter by first task
        reminders = service.list_reminders(task_id=test_task.id)
        assert len(reminders) == 1
        assert reminders[0].task_id == test_task.id

    def test_get_reminder(self, session, test_user, test_task) -> None:
        """Should get a specific reminder by ID."""
        from src.models.reminder import ReminderCreate
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)

        created = service.create_reminder(
            ReminderCreate(
                task_id=test_task.id,
                remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )

        fetched = service.get_reminder(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_reminder_not_found(self, session, test_user) -> None:
        """Should return None for nonexistent reminder."""
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)
        result = service.get_reminder(uuid4())
        assert result is None

    def test_delete_reminder(self, session, test_user, test_task) -> None:
        """Should delete a reminder."""
        from src.models.reminder import ReminderCreate
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)

        reminder = service.create_reminder(
            ReminderCreate(
                task_id=test_task.id,
                remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )

        result = service.delete_reminder(reminder.id)
        assert result is True

        # Verify deleted
        assert service.get_reminder(reminder.id) is None

    def test_delete_reminder_not_found(self, session, test_user) -> None:
        """Should return False when deleting nonexistent reminder."""
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)
        result = service.delete_reminder(uuid4())
        assert result is False


@pytest.mark.integration
class TestReminderLimits:
    """Integration tests for reminder limits (FR-018)."""

    def test_max_three_reminders_per_task(self, session, test_user, test_task) -> None:
        """Should enforce max 3 reminders per task."""
        from src.models.reminder import ReminderCreate
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)

        # Create 3 reminders (should succeed)
        for i in range(3):
            service.create_reminder(
                ReminderCreate(
                    task_id=test_task.id,
                    remind_at=datetime.now(timezone.utc) + timedelta(hours=i + 1),
                )
            )

        # Fourth reminder should fail
        with pytest.raises(ValueError, match="Maximum 3 reminders"):
            service.create_reminder(
                ReminderCreate(
                    task_id=test_task.id,
                    remind_at=datetime.now(timezone.utc) + timedelta(hours=5),
                )
            )


@pytest.mark.integration
class TestReminderAutoCancel:
    """Integration tests for auto-cancel on task completion (FR-020)."""

    def test_cancel_task_reminders(self, session, test_user, test_task) -> None:
        """Should cancel all unsent reminders for a task."""
        from src.models.reminder import ReminderCreate
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)

        # Create reminders
        for i in range(2):
            service.create_reminder(
                ReminderCreate(
                    task_id=test_task.id,
                    remind_at=datetime.now(timezone.utc) + timedelta(hours=i + 1),
                )
            )

        # Cancel all reminders
        canceled_count = service.cancel_task_reminders(test_task.id)
        assert canceled_count == 2

        # Verify no reminders left
        reminders = service.list_reminders(task_id=test_task.id)
        assert len(reminders) == 0

    def test_cancel_only_unsent_reminders(self, session, test_user, test_task) -> None:
        """Should only cancel unsent reminders."""
        from src.models.reminder import Reminder, ReminderCreate
        from src.services.reminder_service import ReminderService

        service = ReminderService(session, test_user.id)

        # Create a reminder
        reminder = service.create_reminder(
            ReminderCreate(
                task_id=test_task.id,
                remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )

        # Mark as sent
        reminder.sent = True
        reminder.sent_at = datetime.now(timezone.utc)
        session.add(reminder)
        session.commit()

        # Create another unsent reminder
        service.create_reminder(
            ReminderCreate(
                task_id=test_task.id,
                remind_at=datetime.now(timezone.utc) + timedelta(hours=2),
            )
        )

        # Cancel should only affect unsent
        canceled_count = service.cancel_task_reminders(test_task.id)
        assert canceled_count == 1

        # Sent reminder should still exist
        reminders = service.list_reminders(task_id=test_task.id)
        assert len(reminders) == 1
        assert reminders[0].sent is True


@pytest.mark.integration
class TestBackgroundChecker:
    """Integration tests for background reminder checker."""

    def test_get_due_reminders(self, session, test_user, test_task) -> None:
        """Should get all due, unsent reminders."""
        from src.models.reminder import Reminder
        from src.services.reminder_service import ReminderService

        # Create a past (due) reminder directly
        past_reminder = Reminder(
            task_id=test_task.id,
            remind_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            sent=False,
        )
        session.add(past_reminder)

        # Create a future reminder
        future_reminder = Reminder(
            task_id=test_task.id,
            remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
            sent=False,
        )
        session.add(future_reminder)
        session.commit()

        due = ReminderService.get_due_reminders_for_all_users(session)
        assert len(due) == 1
        assert due[0].id == past_reminder.id

    def test_mark_as_sent(self, session, test_user, test_task) -> None:
        """Should mark reminder as sent with timestamp."""
        from src.models.reminder import Reminder
        from src.services.reminder_service import ReminderService

        reminder = Reminder(
            task_id=test_task.id,
            remind_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            sent=False,
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)

        ReminderService.mark_as_sent(session, reminder.id)

        # Refresh to get updated values
        session.refresh(reminder)
        assert reminder.sent is True
        assert reminder.sent_at is not None


@pytest.mark.integration
class TestUserIsolation:
    """Integration tests for user isolation in reminder operations."""

    def test_cannot_access_other_users_reminders(self, session, test_user, test_task) -> None:
        """Should not be able to access reminders from other users' tasks."""
        from src.models.reminder import ReminderCreate
        from src.models.user import User
        from src.services.reminder_service import ReminderService

        # Create reminder with first user
        service1 = ReminderService(session, test_user.id)
        reminder = service1.create_reminder(
            ReminderCreate(
                task_id=test_task.id,
                remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )

        # Create second user
        user2 = User(
            email="user2@example.com",
            hashed_password="hashed_password_here",
        )
        session.add(user2)
        session.commit()
        session.refresh(user2)

        # Try to access reminder with second user
        service2 = ReminderService(session, user2.id)

        # Should not be able to get the reminder
        assert service2.get_reminder(reminder.id) is None

        # Should not be able to delete the reminder
        assert service2.delete_reminder(reminder.id) is False

        # List should be empty for second user
        assert len(service2.list_reminders()) == 0
