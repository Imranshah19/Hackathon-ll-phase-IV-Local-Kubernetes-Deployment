"""
Recurrence Service for Phase 5 - User Story 4.

Provides business logic for recurring tasks:
- Next occurrence calculation
- Recurrence rule management
- Series operations (delete/update all)

Uses python-dateutil for reliable date arithmetic.
"""

from datetime import datetime, timedelta, date
from typing import Optional
from uuid import UUID

from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select

from src.models.recurrence import (
    RecurrenceRule,
    RecurrenceRuleCreate,
    RecurrenceEndType,
    RecurrenceFrequency,
)
from src.models.task import Task


class RecurrenceService:
    """
    Service for recurring task operations.

    Provides static methods for calculation and instance methods for DB operations.
    """

    def __init__(self, session: Session, user_id: UUID):
        """
        Initialize the recurrence service.

        Args:
            session: Database session
            user_id: Current user's UUID
        """
        self.session = session
        self.user_id = user_id

    # =========================================================================
    # Static Methods - Pure Calculation (No DB)
    # =========================================================================

    @staticmethod
    def calculate_next_occurrence(
        rule: RecurrenceRule,
        current_due: Optional[datetime],
        completed_count: int = 0,
    ) -> Optional[datetime]:
        """
        Calculate the next occurrence date based on recurrence rule.

        Args:
            rule: The recurrence rule defining the pattern
            current_due: Current due date (or None to use now)
            completed_count: Number of completions so far (for count-based end)

        Returns:
            Next due datetime, or None if recurrence has ended
        """
        # Use current time if no due date
        if current_due is None:
            current_due = datetime.utcnow()

        # Check end conditions first
        if not RecurrenceService._should_continue(rule, current_due, completed_count):
            return None

        # Calculate next date based on frequency
        next_due = RecurrenceService._add_interval(
            current_due,
            rule.frequency,
            rule.interval,
        )

        # Verify next date is still valid (for date-based end)
        if rule.end_type == RecurrenceEndType.DATE and rule.end_date:
            if next_due.date() > rule.end_date:
                return None

        return next_due

    @staticmethod
    def _should_continue(
        rule: RecurrenceRule,
        current_due: datetime,
        completed_count: int,
    ) -> bool:
        """
        Check if recurrence should continue based on end conditions.

        Args:
            rule: Recurrence rule
            current_due: Current due datetime
            completed_count: Number of completions so far

        Returns:
            True if recurrence should continue
        """
        if rule.end_type == RecurrenceEndType.NEVER:
            return True

        if rule.end_type == RecurrenceEndType.COUNT:
            # If end_count is not set, treat as never-ending
            if rule.end_count is None:
                return True
            return completed_count < rule.end_count

        if rule.end_type == RecurrenceEndType.DATE:
            # If end_date is not set, treat as never-ending
            if rule.end_date is None:
                return True
            # Check if current date is still before or on end date
            return current_due.date() <= rule.end_date

        return True

    @staticmethod
    def _add_interval(
        base_date: datetime,
        frequency: RecurrenceFrequency,
        interval: int,
    ) -> datetime:
        """
        Add the interval to base date based on frequency.

        Uses dateutil.relativedelta for accurate month/year arithmetic.

        Args:
            base_date: Starting datetime
            frequency: Recurrence frequency type
            interval: Number of units to add

        Returns:
            New datetime with interval added
        """
        if frequency == RecurrenceFrequency.DAILY:
            return base_date + timedelta(days=interval)

        if frequency == RecurrenceFrequency.WEEKLY:
            return base_date + timedelta(weeks=interval)

        if frequency == RecurrenceFrequency.MONTHLY:
            # Use relativedelta for proper month arithmetic
            # Handles end-of-month cases (Jan 31 -> Feb 28)
            return base_date + relativedelta(months=interval)

        if frequency == RecurrenceFrequency.YEARLY:
            # Use relativedelta for proper year arithmetic
            # Handles leap year cases (Feb 29 -> Feb 28)
            return base_date + relativedelta(years=interval)

        if frequency == RecurrenceFrequency.CUSTOM:
            # Custom defaults to daily for now
            # Could be extended with additional rule fields
            return base_date + timedelta(days=interval)

        # Fallback to daily
        return base_date + timedelta(days=interval)

    # =========================================================================
    # Instance Methods - Database Operations
    # =========================================================================

    def create_rule(self, data: RecurrenceRuleCreate) -> RecurrenceRule:
        """
        Create a new recurrence rule.

        Args:
            data: Recurrence rule creation data

        Returns:
            Created recurrence rule
        """
        rule = RecurrenceRule(
            user_id=self.user_id,
            frequency=data.frequency,
            interval=data.interval,
            end_type=data.end_type,
            end_count=data.end_count,
            end_date=data.end_date,
        )

        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)

        return rule

    def get_rule(self, rule_id: UUID) -> Optional[RecurrenceRule]:
        """
        Get a recurrence rule by ID.

        Args:
            rule_id: Rule UUID

        Returns:
            RecurrenceRule if found and belongs to user, None otherwise
        """
        return self.session.exec(
            select(RecurrenceRule).where(
                RecurrenceRule.id == rule_id,
                RecurrenceRule.user_id == self.user_id,
            )
        ).first()

    def delete_rule(self, rule_id: UUID) -> bool:
        """
        Delete a recurrence rule.

        Args:
            rule_id: Rule UUID

        Returns:
            True if deleted, False if not found

        Note:
            Tasks with this rule_id will have recurrence_rule_id set to NULL.
        """
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        self.session.delete(rule)
        self.session.commit()
        return True

    def get_completed_count(self, task: Task) -> int:
        """
        Get the count of completed instances for a recurring task.

        Counts all tasks with the same recurrence_rule_id that are completed.

        Args:
            task: The task to count completions for

        Returns:
            Number of completed instances
        """
        if not task.recurrence_rule_id:
            return 0

        count = self.session.exec(
            select(Task).where(
                Task.recurrence_rule_id == task.recurrence_rule_id,
                Task.user_id == self.user_id,
                Task.is_completed == True,
            )
        ).all()

        return len(count)

    def create_next_instance(self, task: Task, rule: RecurrenceRule) -> Optional[Task]:
        """
        Create the next instance of a recurring task.

        Args:
            task: The completed task
            rule: The recurrence rule

        Returns:
            New task instance, or None if recurrence has ended
        """
        completed_count = self.get_completed_count(task) + 1  # Include current

        next_due = self.calculate_next_occurrence(
            rule,
            task.due,
            completed_count=completed_count,
        )

        if next_due is None:
            return None

        # Create new task instance
        next_task = Task(
            user_id=self.user_id,
            title=task.title,
            description=task.description,
            is_completed=False,
            priority=task.priority,
            due=next_due,
            recurrence_rule_id=task.recurrence_rule_id,
            parent_task_id=task.id,
        )

        self.session.add(next_task)
        self.session.commit()
        self.session.refresh(next_task)

        return next_task

    def delete_future_instances(self, task: Task) -> int:
        """
        Delete all future (non-completed) instances of a recurring task series.

        Args:
            task: Any task in the series

        Returns:
            Number of tasks deleted
        """
        if not task.recurrence_rule_id:
            return 0

        future_tasks = self.session.exec(
            select(Task).where(
                Task.recurrence_rule_id == task.recurrence_rule_id,
                Task.user_id == self.user_id,
                Task.is_completed == False,
            )
        ).all()

        count = len(future_tasks)
        for t in future_tasks:
            self.session.delete(t)

        self.session.commit()
        return count

    def update_future_instances(
        self,
        task: Task,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> int:
        """
        Update all future (non-completed) instances of a recurring task series.

        Args:
            task: Any task in the series
            title: New title (optional)
            description: New description (optional)
            priority: New priority (optional)

        Returns:
            Number of tasks updated
        """
        if not task.recurrence_rule_id:
            return 0

        future_tasks = self.session.exec(
            select(Task).where(
                Task.recurrence_rule_id == task.recurrence_rule_id,
                Task.user_id == self.user_id,
                Task.is_completed == False,
            )
        ).all()

        count = 0
        for t in future_tasks:
            if title is not None:
                t.title = title
            if description is not None:
                t.description = description
            if priority is not None:
                t.priority = priority
            self.session.add(t)
            count += 1

        self.session.commit()
        return count


__all__ = ["RecurrenceService"]
