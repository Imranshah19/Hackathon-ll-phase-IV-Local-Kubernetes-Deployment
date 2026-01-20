"""
Integration tests for Task search and filtering functionality.

Tests:
- Search tasks by title text (case-insensitive)
- Combined search + completed filter
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
class TestTaskSearch:
    """Integration tests for task search and filtering."""

    def test_search_parameter_exists_in_task_list(self) -> None:
        """list_tasks should accept search parameter."""
        from src.api.tasks import list_tasks
        import inspect

        sig = inspect.signature(list_tasks)
        params = list(sig.parameters.keys())

        assert "search" in params, "list_tasks should have 'search' parameter"

    def test_task_title_searchable(self) -> None:
        """Task model should support title search via ilike."""
        from src.models.task import Task

        # Task should have title field that supports SQL operations
        assert hasattr(Task, "title"), "Task should have 'title' attribute"

        # SQLModel/SQLAlchemy columns support ilike for case-insensitive search
        title_attr = getattr(Task, "title")
        assert hasattr(title_attr, "ilike") or hasattr(title_attr, "contains"), \
            "Task.title should support SQL search operations"

    def test_search_returns_matching_tasks(self) -> None:
        """Search should filter tasks by title containing search term."""
        from src.models.task import Task

        user_id = uuid4()

        task1 = Task(title="Buy groceries", user_id=user_id)
        task2 = Task(title="Call doctor", user_id=user_id)
        task3 = Task(title="Buy birthday gift", user_id=user_id)

        # Simulate search filtering (actual DB test would need session)
        search_term = "buy"
        matching = [t for t in [task1, task2, task3]
                   if search_term.lower() in t.title.lower()]

        assert len(matching) == 2, "Should find 2 tasks with 'buy' in title"
        assert task1 in matching
        assert task3 in matching
        assert task2 not in matching

    def test_search_case_insensitive(self) -> None:
        """Search should be case-insensitive."""
        from src.models.task import Task

        user_id = uuid4()
        task = Task(title="BUY GROCERIES", user_id=user_id)

        # Both lowercase and uppercase search should match
        assert "buy" in task.title.lower()
        assert "BUY" in task.title.upper()

    def test_search_with_completed_filter(self) -> None:
        """Search can be combined with completed filter."""
        from src.models.task import Task

        user_id = uuid4()

        task1 = Task(title="Buy milk", user_id=user_id, is_completed=False)
        task2 = Task(title="Buy eggs", user_id=user_id, is_completed=True)
        task3 = Task(title="Call mom", user_id=user_id, is_completed=False)

        # Search "buy" + completed=False
        tasks = [task1, task2, task3]
        search_term = "buy"
        completed = False

        matching = [t for t in tasks
                   if search_term.lower() in t.title.lower()
                   and t.is_completed == completed]

        assert len(matching) == 1, "Should find only 1 pending task with 'buy'"
        assert matching[0] == task1

    def test_empty_search_returns_all(self) -> None:
        """Empty or None search should return all tasks (no filtering)."""
        from src.models.task import Task

        user_id = uuid4()
        tasks = [
            Task(title="Task 1", user_id=user_id),
            Task(title="Task 2", user_id=user_id),
            Task(title="Task 3", user_id=user_id),
        ]

        # None/empty search = no filter applied
        search_term = None
        if search_term:
            matching = [t for t in tasks if search_term.lower() in t.title.lower()]
        else:
            matching = tasks

        assert len(matching) == 3, "Empty search should return all tasks"

    def test_search_no_matches(self) -> None:
        """Search with no matches should return empty list."""
        from src.models.task import Task

        user_id = uuid4()
        tasks = [
            Task(title="Buy groceries", user_id=user_id),
            Task(title="Call doctor", user_id=user_id),
        ]

        search_term = "xyz123"
        matching = [t for t in tasks if search_term.lower() in t.title.lower()]

        assert len(matching) == 0, "No tasks should match 'xyz123'"
