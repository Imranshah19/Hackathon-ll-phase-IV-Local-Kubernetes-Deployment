"""
Reminder Service for Phase 5 - User Story 5.

Provides business logic for task reminders:
- CRUD operations for reminders
- Auto-cancel on task completion
- Due reminder queries for background checker
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from src.models.reminder import Reminder, ReminderCreate
from src.models.task import Task


class ReminderService:
    """
    Service for reminder management operations.

    All operations are scoped to the authenticated user via task ownership.
    """

    MAX_REMINDERS_PER_TASK = 3

    def __init__(self, session: Session, user_id: UUID):
        """
        Initialize the reminder service.

        Args:
            session: Database session
            user_id: Current user's UUID
        """
        self.session = session
        self.user_id = user_id

    def _get_user_task(self, task_id: UUID) -> Task | None:
        """Get a task owned by the current user."""
        return self.session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == self.user_id)
        ).first()

    def _validate_task_ownership(self, task_id: UUID) -> Task:
        """
        Validate that the task exists and belongs to the current user.

        Raises:
            ValueError: If task not found or doesn't belong to user
        """
        task = self._get_user_task(task_id)
        if not task:
            raise ValueError("Task not found")
        return task

    def list_reminders(self, task_id: UUID | None = None) -> list[Reminder]:
        """
        Get all reminders for the current user's tasks.

        Args:
            task_id: Optional filter by specific task

        Returns:
            List of reminders
        """
        query = (
            select(Reminder)
            .join(Task, Reminder.task_id == Task.id)
            .where(Task.user_id == self.user_id)
        )

        if task_id is not None:
            query = query.where(Reminder.task_id == task_id)

        query = query.order_by(Reminder.remind_at)
        return list(self.session.exec(query).all())

    def get_reminder(self, reminder_id: UUID) -> Reminder | None:
        """
        Get a specific reminder by ID.

        Args:
            reminder_id: Reminder UUID

        Returns:
            Reminder if found and belongs to user's task, None otherwise
        """
        return self.session.exec(
            select(Reminder)
            .join(Task, Reminder.task_id == Task.id)
            .where(Reminder.id == reminder_id, Task.user_id == self.user_id)
        ).first()

    def create_reminder(self, data: ReminderCreate) -> Reminder:
        """
        Create a new reminder.

        Args:
            data: Reminder creation data

        Returns:
            Created reminder

        Raises:
            ValueError: If task not found, remind_at in past, or max reminders reached
        """
        # Validate task ownership
        task = self._validate_task_ownership(data.task_id)

        # Reject remind_at in the past
        now = datetime.now(timezone.utc)
        remind_at = data.remind_at
        if remind_at.tzinfo is None:
            remind_at = remind_at.replace(tzinfo=timezone.utc)

        if remind_at <= now:
            raise ValueError("Reminder time must be in the future")

        # Check max reminders limit (FR-018)
        existing_count = len(self.list_reminders(data.task_id))
        if existing_count >= self.MAX_REMINDERS_PER_TASK:
            raise ValueError(
                f"Maximum {self.MAX_REMINDERS_PER_TASK} reminders per task allowed"
            )

        reminder = Reminder(
            task_id=data.task_id,
            remind_at=data.remind_at,
            message=data.message,
        )

        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)

        return reminder

    def delete_reminder(self, reminder_id: UUID) -> bool:
        """
        Delete a reminder.

        Args:
            reminder_id: Reminder UUID

        Returns:
            True if deleted, False if not found
        """
        reminder = self.get_reminder(reminder_id)
        if not reminder:
            return False

        self.session.delete(reminder)
        self.session.commit()
        return True

    def cancel_task_reminders(self, task_id: UUID) -> int:
        """
        Cancel all unsent reminders for a task (FR-020).

        Called when a task is completed.

        Args:
            task_id: Task UUID

        Returns:
            Number of reminders canceled
        """
        # Validate task ownership
        self._validate_task_ownership(task_id)

        # Get unsent reminders
        reminders = self.session.exec(
            select(Reminder).where(
                Reminder.task_id == task_id,
                Reminder.sent == False,  # noqa: E712
            )
        ).all()

        count = len(reminders)
        for reminder in reminders:
            self.session.delete(reminder)

        if count > 0:
            self.session.commit()

        return count

    @staticmethod
    def get_due_reminders_for_all_users(session: Session) -> list[Reminder]:
        """
        Get all due reminders across all users (for background checker).

        This is a static method because it's called from the background task
        without user context.

        Args:
            session: Database session

        Returns:
            List of due, unsent reminders
        """
        now = datetime.now(timezone.utc)
        return list(
            session.exec(
                select(Reminder)
                .where(
                    Reminder.remind_at <= now,
                    Reminder.sent == False,  # noqa: E712
                )
                .order_by(Reminder.remind_at)
            ).all()
        )

    @staticmethod
    def mark_as_sent(session: Session, reminder_id: UUID) -> None:
        """
        Mark a reminder as sent (for background checker).

        Args:
            session: Database session
            reminder_id: Reminder UUID
        """
        reminder = session.get(Reminder, reminder_id)
        if reminder:
            reminder.sent = True
            reminder.sent_at = datetime.now(timezone.utc)
            session.add(reminder)
            session.commit()


__all__ = ["ReminderService"]
