"""
Contract tests for Task Priority (Phase 5 - User Story 1).

Tests:
- T018: Validate priority field in task creation
- Priority values 1-5 (Critical, High, Medium, Low, None)
- Default priority is 3 (Medium)
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4


@pytest.mark.contract
class TestTaskPriorityContract:
    """Contract tests for task priority management."""

    def test_task_create_accepts_priority(self) -> None:
        """TaskCreate should accept priority field (1-5)."""
        from src.models.task import TaskCreate

        # Valid priorities: 1 (Critical) to 5 (None)
        for priority in [1, 2, 3, 4, 5]:
            task = TaskCreate(title="Test task", priority=priority)
            assert task.priority == priority

    def test_task_create_default_priority_is_medium(self) -> None:
        """TaskCreate priority should default to 3 (Medium)."""
        from src.models.task import TaskCreate

        task = TaskCreate(title="Test task")
        assert task.priority == 3

    def test_task_create_rejects_invalid_priority(self) -> None:
        """TaskCreate should reject priority outside 1-5 range."""
        from pydantic import ValidationError
        from src.models.task import TaskCreate

        # Priority 0 should be rejected
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="Test", priority=0)
        assert "priority" in str(exc_info.value).lower()

        # Priority 6 should be rejected
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="Test", priority=6)
        assert "priority" in str(exc_info.value).lower()

        # Negative priority should be rejected
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="Test", priority=-1)
        assert "priority" in str(exc_info.value).lower()

    def test_task_public_includes_priority(self) -> None:
        """TaskPublic must include priority field."""
        from src.models.task import TaskPublic

        fields = TaskPublic.model_fields
        assert "priority" in fields, "TaskPublic missing priority field"

    def test_task_public_priority_serialization(self) -> None:
        """TaskPublic should serialize priority to JSON."""
        from src.models.task import TaskPublic

        task_public = TaskPublic(
            id=uuid4(),
            user_id=uuid4(),
            title="Test task",
            description=None,
            is_completed=False,
            priority=1,  # Critical
            due=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        json_data = task_public.model_dump(mode="json")

        assert "priority" in json_data
        assert json_data["priority"] == 1
        assert isinstance(json_data["priority"], int)

    def test_task_update_accepts_priority(self) -> None:
        """TaskUpdate should accept optional priority field."""
        from src.models.task import TaskUpdate

        # Update with priority
        update = TaskUpdate(priority=2)
        assert update.priority == 2

        # Update without priority (should be None)
        update_no_priority = TaskUpdate(title="New title")
        assert update_no_priority.priority is None

    def test_task_update_validates_priority_range(self) -> None:
        """TaskUpdate should validate priority range (1-5)."""
        from pydantic import ValidationError
        from src.models.task import TaskUpdate

        # Invalid priority should be rejected
        with pytest.raises(ValidationError):
            TaskUpdate(priority=0)

        with pytest.raises(ValidationError):
            TaskUpdate(priority=6)

    def test_task_model_priority_default(self) -> None:
        """Task database model should have priority default to 3."""
        from src.models.task import Task

        task = Task(
            title="Test task",
            user_id=uuid4(),
        )

        assert task.priority == 3

    def test_task_model_accepts_due_date(self) -> None:
        """Task model should accept due date."""
        from src.models.task import Task

        due_date = datetime.now(timezone.utc)
        task = Task(
            title="Test task",
            user_id=uuid4(),
            due=due_date,
        )

        assert task.due == due_date

    def test_task_public_includes_due(self) -> None:
        """TaskPublic must include due field."""
        from src.models.task import TaskPublic

        fields = TaskPublic.model_fields
        assert "due" in fields, "TaskPublic missing due field"


@pytest.mark.contract
class TestPriorityLabels:
    """Contract tests for priority label mapping."""

    def test_priority_labels_mapping(self) -> None:
        """Priority values should map to expected labels."""
        # This defines the contract for frontend display
        priority_labels = {
            1: "Critical",
            2: "High",
            3: "Medium",
            4: "Low",
            5: "None",
        }

        # Verify mapping is consistent
        assert priority_labels[1] == "Critical"
        assert priority_labels[2] == "High"
        assert priority_labels[3] == "Medium"
        assert priority_labels[4] == "Low"
        assert priority_labels[5] == "None"

    def test_priority_colors_contract(self) -> None:
        """Priority colors should follow expected pattern."""
        # This defines the color contract for frontend
        priority_colors = {
            1: "#EF4444",  # Red - Critical
            2: "#F97316",  # Orange - High
            3: "#EAB308",  # Yellow - Medium
            4: "#22C55E",  # Green - Low
            5: "#6B7280",  # Gray - None
        }

        # All priorities should have assigned colors
        for priority in range(1, 6):
            assert priority in priority_colors
            assert priority_colors[priority].startswith("#")
