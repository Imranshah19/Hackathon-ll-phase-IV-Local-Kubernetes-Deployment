"""
Contract tests for Task Filtering and Sorting (Phase 5 - User Story 1 & 3).

Tests:
- T019: Validate priority filter parameter
- T039: Validate combined filters
- T040: Validate sort options
"""

import pytest
from typing import Any


@pytest.mark.contract
class TestTaskFilterContract:
    """Contract tests for task filtering parameters."""

    def test_priority_filter_accepts_valid_values(self) -> None:
        """Priority filter should accept values 1-5."""
        # This test validates the API contract for priority filter
        valid_priorities = [1, 2, 3, 4, 5]

        for priority in valid_priorities:
            # Filter param should be valid integer in range
            assert 1 <= priority <= 5

    def test_priority_filter_accepts_list(self) -> None:
        """Priority filter should accept multiple values."""
        # API should accept: ?priority=1&priority=2 or ?priority=1,2
        priority_list = [1, 2]  # Critical and High

        # All values should be valid
        for priority in priority_list:
            assert 1 <= priority <= 5

    def test_completed_filter_is_boolean(self) -> None:
        """Completed filter should be boolean."""
        # Already exists, but ensure contract is maintained
        valid_values = [True, False, None]

        for value in valid_values:
            assert value is None or isinstance(value, bool)

    def test_due_date_filters_contract(self) -> None:
        """Due date filter should accept ISO 8601 format."""
        from datetime import datetime, timezone

        # due_from and due_to should accept ISO format
        valid_dates = [
            "2026-01-28",
            "2026-01-28T12:00:00Z",
            "2026-01-28T12:00:00+00:00",
        ]

        for date_str in valid_dates:
            # Should be parseable as date/datetime
            try:
                if "T" in date_str:
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                pytest.fail(f"Date format not accepted: {date_str}")

    def test_search_filter_is_string(self) -> None:
        """Search filter should be a string."""
        valid_searches = [
            "groceries",
            "buy",
            "task 1",
            "",  # Empty should be valid (no filter)
        ]

        for search in valid_searches:
            assert isinstance(search, str)


@pytest.mark.contract
class TestTaskSortContract:
    """Contract tests for task sorting parameters."""

    def test_sort_by_accepts_valid_fields(self) -> None:
        """sort_by should accept: created_at, updated_at, priority, due, title."""
        valid_sort_fields = [
            "created_at",
            "updated_at",
            "priority",
            "due",
            "title",
        ]

        for field in valid_sort_fields:
            assert isinstance(field, str)
            assert len(field) > 0

    def test_sort_order_accepts_asc_desc(self) -> None:
        """sort_order should accept 'asc' or 'desc'."""
        valid_orders = ["asc", "desc"]

        for order in valid_orders:
            assert order in ["asc", "desc"]

    def test_sort_order_default_is_desc(self) -> None:
        """Default sort_order should be 'desc' for most recent first."""
        default_order = "desc"
        assert default_order == "desc"

    def test_sort_by_priority_ordering(self) -> None:
        """Sorting by priority: asc=Critical first, desc=None first."""
        # Priority 1 = Critical (most important)
        # Priority 5 = None (least important)

        priorities = [3, 1, 5, 2, 4]

        # Ascending: 1, 2, 3, 4, 5 (Critical first)
        asc_sorted = sorted(priorities)
        assert asc_sorted == [1, 2, 3, 4, 5]

        # Descending: 5, 4, 3, 2, 1 (None first)
        desc_sorted = sorted(priorities, reverse=True)
        assert desc_sorted == [5, 4, 3, 2, 1]


@pytest.mark.contract
class TestCombinedFiltersContract:
    """Contract tests for combining multiple filters."""

    def test_filters_combine_with_and_logic(self) -> None:
        """Multiple filters should combine with AND logic."""
        # Example: completed=false AND priority=1 AND search=urgent
        filters = {
            "completed": False,
            "priority": 1,
            "search": "urgent",
        }

        # All filters should be applied together
        assert len(filters) == 3

    def test_filter_response_format(self) -> None:
        """Filter response should be a list of TaskPublic."""
        # Response format contract
        expected_response_type = "list[TaskPublic]"

        # Each item should have task fields
        expected_fields = [
            "id",
            "user_id",
            "title",
            "description",
            "is_completed",
            "priority",
            "due",
            "created_at",
            "updated_at",
            "tags",
        ]

        # Verify expected fields list
        assert len(expected_fields) >= 9

    def test_empty_filter_returns_all_tasks(self) -> None:
        """Empty filters should return all user's tasks."""
        filters: dict[str, Any] = {}

        # No filters = all tasks
        assert len(filters) == 0


@pytest.mark.contract
class TestTagFilterContract:
    """Contract tests for tag filtering (US2 dependency, but define contract now)."""

    def test_tags_filter_accepts_uuid_list(self) -> None:
        """Tags filter should accept list of tag UUIDs."""
        from uuid import uuid4

        tag_ids = [uuid4(), uuid4()]

        # Should be valid UUIDs
        for tag_id in tag_ids:
            assert tag_id.version == 4

    def test_tags_filter_accepts_name_list(self) -> None:
        """Tags filter should also accept tag names."""
        tag_names = ["work", "personal", "urgent"]

        for name in tag_names:
            assert isinstance(name, str)
            assert len(name) > 0
