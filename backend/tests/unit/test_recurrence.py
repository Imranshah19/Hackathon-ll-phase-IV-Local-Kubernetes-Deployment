"""
Unit tests for RecurrenceService next occurrence calculation (Phase 5 - US4).

Tests:
- T050: RRULE next occurrence calculation
- Daily, weekly, monthly, yearly patterns
- Intervals (e.g., every 2 weeks)
- End conditions (never, count, date)

TDD: These tests are written BEFORE the implementation.
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4

from src.models.recurrence import (
    RecurrenceFrequency,
    RecurrenceEndType,
    RecurrenceRule,
)


@pytest.mark.unit
class TestRecurrenceNextOccurrence:
    """Unit tests for next occurrence calculation."""

    def test_daily_recurrence_next_day(self) -> None:
        """Daily recurrence should return next day."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        current_due = datetime(2026, 1, 28, 10, 0, 0)
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        assert next_due == datetime(2026, 1, 29, 10, 0, 0)

    def test_daily_recurrence_with_interval(self) -> None:
        """Daily recurrence with interval=3 should skip 3 days."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=3,
            end_type=RecurrenceEndType.NEVER,
        )

        current_due = datetime(2026, 1, 28, 10, 0, 0)
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        assert next_due == datetime(2026, 1, 31, 10, 0, 0)

    def test_weekly_recurrence(self) -> None:
        """Weekly recurrence should return same day next week."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.WEEKLY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        current_due = datetime(2026, 1, 28, 10, 0, 0)  # Wednesday
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        assert next_due == datetime(2026, 2, 4, 10, 0, 0)  # Next Wednesday

    def test_weekly_recurrence_with_interval(self) -> None:
        """Weekly recurrence with interval=2 should skip 2 weeks."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.WEEKLY,
            interval=2,
            end_type=RecurrenceEndType.NEVER,
        )

        current_due = datetime(2026, 1, 28, 10, 0, 0)
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        assert next_due == datetime(2026, 2, 11, 10, 0, 0)

    def test_monthly_recurrence(self) -> None:
        """Monthly recurrence should return same day next month."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.MONTHLY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        current_due = datetime(2026, 1, 15, 10, 0, 0)
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        assert next_due == datetime(2026, 2, 15, 10, 0, 0)

    def test_monthly_recurrence_end_of_month(self) -> None:
        """Monthly recurrence on 31st should handle shorter months."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.MONTHLY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        # Jan 31 -> Feb should be Feb 28 (or 29 in leap year)
        current_due = datetime(2026, 1, 31, 10, 0, 0)
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        # 2026 is not a leap year, so Feb has 28 days
        assert next_due == datetime(2026, 2, 28, 10, 0, 0)

    def test_yearly_recurrence(self) -> None:
        """Yearly recurrence should return same date next year."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.YEARLY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        current_due = datetime(2026, 3, 15, 10, 0, 0)
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        assert next_due == datetime(2027, 3, 15, 10, 0, 0)

    def test_yearly_recurrence_leap_day(self) -> None:
        """Yearly recurrence on Feb 29 should handle non-leap years."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.YEARLY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        # Feb 29 in leap year -> Feb 28 in non-leap year
        current_due = datetime(2024, 2, 29, 10, 0, 0)  # 2024 is leap year
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        # 2025 is not a leap year
        assert next_due == datetime(2025, 2, 28, 10, 0, 0)


@pytest.mark.unit
class TestRecurrenceEndConditions:
    """Unit tests for recurrence end conditions."""

    def test_end_type_never_always_returns_next(self) -> None:
        """End type 'never' should always return next occurrence."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        current_due = datetime(2026, 12, 31, 10, 0, 0)
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        assert next_due is not None
        assert next_due == datetime(2027, 1, 1, 10, 0, 0)

    def test_end_type_count_within_limit(self) -> None:
        """End type 'count' should return next when under limit."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.COUNT,
            end_count=5,
        )

        current_due = datetime(2026, 1, 28, 10, 0, 0)
        completed_count = 3  # 3 completed, 2 remaining

        next_due = RecurrenceService.calculate_next_occurrence(
            rule, current_due, completed_count=completed_count
        )

        assert next_due == datetime(2026, 1, 29, 10, 0, 0)

    def test_end_type_count_at_limit(self) -> None:
        """End type 'count' should return None when limit reached."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.COUNT,
            end_count=5,
        )

        current_due = datetime(2026, 1, 28, 10, 0, 0)
        completed_count = 5  # Limit reached

        next_due = RecurrenceService.calculate_next_occurrence(
            rule, current_due, completed_count=completed_count
        )

        assert next_due is None

    def test_end_type_date_before_end(self) -> None:
        """End type 'date' should return next when before end date."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.DATE,
            end_date=date(2026, 2, 15),
        )

        current_due = datetime(2026, 1, 28, 10, 0, 0)
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        assert next_due == datetime(2026, 1, 29, 10, 0, 0)

    def test_end_type_date_after_end(self) -> None:
        """End type 'date' should return None when past end date."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.DATE,
            end_date=date(2026, 1, 28),
        )

        current_due = datetime(2026, 1, 28, 10, 0, 0)
        next_due = RecurrenceService.calculate_next_occurrence(rule, current_due)

        # Next would be Jan 29, which is after end_date Jan 28
        assert next_due is None


@pytest.mark.unit
class TestRecurrenceWithNoDueDate:
    """Unit tests for recurrence when task has no due date."""

    def test_no_due_date_uses_current_time(self) -> None:
        """When no due date, should calculate from current time."""
        from src.services.recurrence_service import RecurrenceService

        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.NEVER,
        )

        # When current_due is None, use now
        next_due = RecurrenceService.calculate_next_occurrence(rule, None)

        assert next_due is not None
        # Should be roughly 1 day from now
        assert next_due > datetime.utcnow()
        assert next_due < datetime.utcnow() + timedelta(days=2)


@pytest.mark.unit
class TestRecurrenceRuleValidation:
    """Unit tests for recurrence rule model validation."""

    def test_interval_minimum(self) -> None:
        """Interval must be at least 1."""
        with pytest.raises(ValueError):
            RecurrenceRule(
                id=uuid4(),
                user_id=uuid4(),
                frequency=RecurrenceFrequency.DAILY,
                interval=0,  # Invalid
                end_type=RecurrenceEndType.NEVER,
            )

    def test_end_count_required_for_count_type(self) -> None:
        """End count should be provided when end_type is COUNT."""
        # This is a business logic validation, not model validation
        # Model allows None, but service should validate
        rule = RecurrenceRule(
            id=uuid4(),
            user_id=uuid4(),
            frequency=RecurrenceFrequency.DAILY,
            interval=1,
            end_type=RecurrenceEndType.COUNT,
            end_count=None,  # Missing
        )

        # Service should handle this gracefully
        from src.services.recurrence_service import RecurrenceService

        # Should treat as "never" or raise meaningful error
        next_due = RecurrenceService.calculate_next_occurrence(
            rule, datetime(2026, 1, 28, 10, 0, 0)
        )
        # Should still work (treat as never-ending)
        assert next_due is not None
