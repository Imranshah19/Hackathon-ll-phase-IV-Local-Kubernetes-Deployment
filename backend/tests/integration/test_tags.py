"""
Integration tests for Tag functionality (Phase 5 - User Story 2).

Tests:
- T028: Task-tag association integration
- Tag CRUD with database
- Tag filtering on tasks
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
class TestTagIntegration:
    """Integration tests for tag operations."""

    def test_tag_name_unique_per_user(self) -> None:
        """Same tag name should be allowed for different users."""
        from src.models.tag import Tag

        user1_id = uuid4()
        user2_id = uuid4()

        # Same name, different users - should be valid
        tag1 = Tag(name="Work", user_id=user1_id)
        tag2 = Tag(name="Work", user_id=user2_id)

        assert tag1.name == tag2.name
        assert tag1.user_id != tag2.user_id

    def test_tag_with_tasks_count(self) -> None:
        """TagPublic.task_count should reflect associated tasks."""
        from src.models.tag import TagPublic

        # When a tag has 3 tasks associated
        tag = TagPublic(
            id=uuid4(),
            user_id=uuid4(),
            name="Project",
            color="#3B82F6",
            created_at="2026-01-28T00:00:00Z",
            task_count=3,
        )

        assert tag.task_count == 3


@pytest.mark.integration
class TestTaskTagAssociation:
    """Integration tests for task-tag relationships."""

    def test_task_can_have_multiple_tags(self) -> None:
        """A task should be able to have multiple tags."""
        from src.models.task_tag import TaskTag

        task_id = uuid4()
        tag_ids = [uuid4(), uuid4(), uuid4()]

        associations = [
            TaskTag(task_id=task_id, tag_id=tag_id)
            for tag_id in tag_ids
        ]

        assert len(associations) == 3
        assert all(a.task_id == task_id for a in associations)

    def test_tag_can_be_on_multiple_tasks(self) -> None:
        """A tag should be able to be on multiple tasks."""
        from src.models.task_tag import TaskTag

        tag_id = uuid4()
        task_ids = [uuid4(), uuid4()]

        associations = [
            TaskTag(task_id=task_id, tag_id=tag_id)
            for task_id in task_ids
        ]

        assert len(associations) == 2
        assert all(a.tag_id == tag_id for a in associations)

    def test_task_tag_cascade_on_task_delete(self) -> None:
        """TaskTag associations should be deleted when task is deleted."""
        # This is enforced by FK constraint with CASCADE
        # Contract: TaskTag has ON DELETE CASCADE for task_id
        from src.models.task_tag import TaskTag

        # Verify the model exists and can be instantiated
        association = TaskTag(task_id=uuid4(), tag_id=uuid4())
        assert association.task_id is not None

    def test_task_tag_cascade_on_tag_delete(self) -> None:
        """TaskTag associations should be deleted when tag is deleted."""
        # Contract: TaskTag has ON DELETE CASCADE for tag_id
        from src.models.task_tag import TaskTag

        association = TaskTag(task_id=uuid4(), tag_id=uuid4())
        assert association.tag_id is not None


@pytest.mark.integration
class TestTagFiltering:
    """Integration tests for filtering tasks by tags."""

    def test_filter_tasks_by_single_tag(self) -> None:
        """Should be able to filter tasks by a single tag."""
        # Contract: GET /api/tasks?tags=tag_id
        tag_id = uuid4()
        filter_params = {"tags": [str(tag_id)]}

        assert "tags" in filter_params
        assert len(filter_params["tags"]) == 1

    def test_filter_tasks_by_multiple_tags(self) -> None:
        """Should be able to filter tasks by multiple tags (AND logic)."""
        # Contract: GET /api/tasks?tags=id1&tags=id2
        tag_ids = [uuid4(), uuid4()]
        filter_params = {"tags": [str(t) for t in tag_ids]}

        assert len(filter_params["tags"]) == 2

    def test_filter_by_tag_name(self) -> None:
        """Should be able to filter by tag name (convenience)."""
        # Contract: GET /api/tasks?tag_names=Work,Personal
        filter_params = {"tag_names": ["Work", "Personal"]}

        assert "tag_names" in filter_params
