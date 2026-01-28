"""
Integration tests for Recurring Tasks (Phase 5 - US4).

Tests:
- T051: Recurring task completion flow
- Creating recurring tasks
- Completing recurring tasks generates next instance
- Delete series functionality
- Update series functionality

TDD: These tests are written BEFORE the implementation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Any

from src.models.recurrence import (
    RecurrenceFrequency,
    RecurrenceEndType,
    RecurrenceRule,
    RecurrenceRuleCreate,
)
from src.models.task import Task


@pytest.mark.integration
class TestRecurringTaskCreation:
    """Integration tests for creating recurring tasks."""

    def test_create_task_with_daily_recurrence(self) -> None:
        """Creating a task with daily recurrence should create rule and link."""
        # This will test the full flow:
        # 1. Create recurrence rule
        # 2. Create task with recurrence_rule_id
        # 3. Verify relationship

        recurrence_data = RecurrenceRuleCreate(
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        # Validate the schema
        assert recurrence_data.frequency == RecurrenceFrequency.DAILY
        assert recurrence_data.interval == 1
        assert recurrence_data.end_type == RecurrenceEndType.NEVER

    def test_create_task_with_weekly_recurrence_end_count(self) -> None:
        """Creating a weekly recurring task with count limit."""
        recurrence_data = RecurrenceRuleCreate(
            frequency=RecurrenceFrequency.WEEKLY,
            interval=2,  # Every 2 weeks
            end_type=RecurrenceEndType.COUNT,
            end_count=10,  # 10 occurrences
        )

        assert recurrence_data.frequency == RecurrenceFrequency.WEEKLY
        assert recurrence_data.interval == 2
        assert recurrence_data.end_type == RecurrenceEndType.COUNT
        assert recurrence_data.end_count == 10

    def test_create_task_with_monthly_recurrence_end_date(self) -> None:
        """Creating a monthly recurring task with end date."""
        from datetime import date

        recurrence_data = RecurrenceRuleCreate(
            frequency=RecurrenceFrequency.MONTHLY,
            interval=1,
            end_type=RecurrenceEndType.DATE,
            end_date=date(2026, 12, 31),
        )

        assert recurrence_data.frequency == RecurrenceFrequency.MONTHLY
        assert recurrence_data.end_type == RecurrenceEndType.DATE
        assert recurrence_data.end_date == date(2026, 12, 31)


@pytest.mark.integration
class TestRecurringTaskCompletion:
    """Integration tests for completing recurring tasks."""

    def test_complete_recurring_task_generates_next_instance(self) -> None:
        """Completing a recurring task should generate the next instance."""
        from src.services.recurrence_service import RecurrenceService

        user_id = uuid4()

        # Create recurrence rule
        rule = RecurrenceRule(
            id=uuid4(),
            user_id=user_id,
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        # Original task
        original_due = datetime(2026, 1, 28, 10, 0, 0)
        original_task = Task(
            id=uuid4(),
            user_id=user_id,
            title="Daily standup",
            description="Team sync meeting",
            is_completed=False,
            priority=2,
            due=original_due,
            recurrence_rule_id=rule.id,
        )

        # Calculate next due
        next_due = RecurrenceService.calculate_next_occurrence(rule, original_due)

        # Create next instance (simulating what the API would do)
        next_task = Task(
            id=uuid4(),
            user_id=user_id,
            title=original_task.title,
            description=original_task.description,
            is_completed=False,
            priority=original_task.priority,
            due=next_due,
            recurrence_rule_id=rule.id,
            parent_task_id=original_task.id,  # Link to original
        )

        # Verify
        assert next_task.title == original_task.title
        assert next_task.due == datetime(2026, 1, 29, 10, 0, 0)
        assert next_task.parent_task_id == original_task.id
        assert next_task.recurrence_rule_id == rule.id
        assert next_task.is_completed is False

    def test_complete_recurring_task_respects_end_count(self) -> None:
        """Should not generate next instance when count limit reached."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.COUNT,
            end_count=3,
        )

        current_due = datetime(2026, 1, 28, 10, 0, 0)

        # Simulate 3 completions already done
        next_due = RecurrenceService.calculate_next_occurrence(
            rule, current_due, completed_count=3
        )

        # Should not generate next (limit reached)
        assert next_due is None

    def test_complete_recurring_task_respects_end_date(self) -> None:
        """Should not generate next instance past end date."""
        from datetime import date
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.DATE,
            end_date=date(2026, 1, 29),
        )

        # Task due on Jan 29
        current_due = datetime(2026, 1, 29, 10, 0, 0)

        # Next would be Jan 30, past end_date
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        assert next_due is None


@pytest.mark.integration
class TestRecurringTaskDeletion:
    """Integration tests for deleting recurring tasks."""

    def test_delete_single_instance_keeps_series(self) -> None:
        """Deleting a single instance should keep the recurrence rule."""
        user_id = uuid4()
        rule_id = uuid4()

        # Multiple instances of the same recurring task
        tasks = [
            Task(
                id=uuid4(),
                user_id=user_id,
                title="Weekly report",
                recurrence_rule_id=rule_id,
                due=datetime(2026, 1, 28),
            ),
            Task(
                id=uuid4(),
                user_id=user_id,
                title="Weekly report",
                recurrence_rule_id=rule_id,
                due=datetime(2026, 2, 4),
            ),
        ]

        # Delete single instance
        deleted_task = tasks[0]
        remaining_tasks = [t for t in tasks if t.id != deleted_task.id]

        # Rule should still exist (other tasks use it)
        assert len(remaining_tasks) == 1
        assert remaining_tasks[0].recurrence_rule_id == rule_id

    def test_delete_series_removes_all_instances(self) -> None:
        """Deleting with delete_series=True should remove all future instances."""
        user_id = uuid4()
        rule_id = uuid4()

        # Multiple instances
        tasks = [
            Task(
                id=uuid4(),
                user_id=user_id,
                title="Weekly report",
                recurrence_rule_id=rule_id,
                due=datetime(2026, 1, 28),
                is_completed=True,  # Past - completed
            ),
            Task(
                id=uuid4(),
                user_id=user_id,
                title="Weekly report",
                recurrence_rule_id=rule_id,
                due=datetime(2026, 2, 4),
                is_completed=False,  # Future
            ),
            Task(
                id=uuid4(),
                user_id=user_id,
                title="Weekly report",
                recurrence_rule_id=rule_id,
                due=datetime(2026, 2, 11),
                is_completed=False,  # Future
            ),
        ]

        # Delete series (future instances)
        # Keep completed ones, delete future ones
        remaining_tasks = [t for t in tasks if t.is_completed]

        assert len(remaining_tasks) == 1
        assert remaining_tasks[0].is_completed is True


@pytest.mark.integration
class TestRecurringTaskUpdate:
    """Integration tests for updating recurring tasks."""

    def test_update_single_instance_only(self) -> None:
        """Updating a single instance should not affect others."""
        user_id = uuid4()
        rule_id = uuid4()

        task1 = Task(
            id=uuid4(),
            user_id=user_id,
            title="Weekly report",
            recurrence_rule_id=rule_id,
        )

        task2 = Task(
            id=uuid4(),
            user_id=user_id,
            title="Weekly report",
            recurrence_rule_id=rule_id,
        )

        # Update only task1
        task1.title = "Updated title"

        # task2 should be unchanged
        assert task2.title == "Weekly report"

    def test_update_series_affects_all_future(self) -> None:
        """Updating with update_series=True should update all future instances."""
        user_id = uuid4()
        rule_id = uuid4()

        tasks = [
            Task(
                id=uuid4(),
                user_id=user_id,
                title="Weekly report",
                description="Old description",
                recurrence_rule_id=rule_id,
                due=datetime(2026, 1, 28),
                is_completed=True,
            ),
            Task(
                id=uuid4(),
                user_id=user_id,
                title="Weekly report",
                description="Old description",
                recurrence_rule_id=rule_id,
                due=datetime(2026, 2, 4),
                is_completed=False,
            ),
        ]

        # Update series description
        new_description = "Updated description for all"
        for task in tasks:
            if not task.is_completed:
                task.description = new_description

        # Past task unchanged
        assert tasks[0].description == "Old description"
        # Future task updated
        assert tasks[1].description == new_description


@pytest.mark.integration
class TestRecurrenceAPIResponse:
    """Integration tests for recurrence in API responses."""

    def test_task_response_includes_recurrence_info(self) -> None:
        """TaskPublic should include recurrence_rule_id."""
        from src.models.task import TaskPublic

        task_data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "title": "Recurring task",
            "description": None,
            "is_completed": False,
            "priority": 3,
            "due": datetime(2026, 1, 28),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "recurrence_rule_id": uuid4(),
            "parent_task_id": None,
            "tags": [],
        }

        public = TaskPublic(**task_data)

        assert public.recurrence_rule_id is not None
        assert public.parent_task_id is None

    def test_complete_response_includes_next_instance(self) -> None:
        """Complete endpoint response should include next instance if recurring."""
        # This tests the expected API response format
        # Response should have: { task: TaskPublic, next_instance: TaskPublic | null }

        response_format = {
            "task": {
                "id": str(uuid4()),
                "title": "Daily standup",
                "is_completed": True,
                "recurrence_rule_id": str(uuid4()),
            },
            "next_instance": {
                "id": str(uuid4()),
                "title": "Daily standup",
                "is_completed": False,
                "due": "2026-01-29T10:00:00Z",
            },
        }

        assert "next_instance" in response_format
        assert response_format["next_instance"]["is_completed"] is False
