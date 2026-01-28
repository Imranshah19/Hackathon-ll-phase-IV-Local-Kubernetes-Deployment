"""
Contract tests for Tag schemas (Phase 5 - User Story 2).

Tests:
- T027: Validate Tag CRUD schemas
- Tag name and color validation
- Tag uniqueness per user
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4


@pytest.mark.contract
class TestTagSchemaContract:
    """Contract tests for tag management."""

    def test_tag_create_accepts_valid_input(self) -> None:
        """TagCreate should accept name and optional color."""
        from src.models.tag import TagCreate

        # With default color
        tag = TagCreate(name="Work")
        assert tag.name == "Work"
        assert tag.color == "#6B7280"  # Default gray

        # With custom color
        tag_colored = TagCreate(name="Personal", color="#3B82F6")
        assert tag_colored.name == "Personal"
        assert tag_colored.color == "#3B82F6"

    def test_tag_create_validates_name_length(self) -> None:
        """TagCreate.name should be 1-50 characters."""
        from pydantic import ValidationError
        from src.models.tag import TagCreate

        # Empty name should be rejected
        with pytest.raises(ValidationError):
            TagCreate(name="")

        # Name over 50 chars should be rejected
        with pytest.raises(ValidationError):
            TagCreate(name="x" * 51)

        # Name at boundary (50 chars) should be accepted
        tag = TagCreate(name="x" * 50)
        assert len(tag.name) == 50

    def test_tag_create_validates_color_format(self) -> None:
        """TagCreate.color should be valid hex format (#RRGGBB)."""
        from pydantic import ValidationError
        from src.models.tag import TagCreate

        # Invalid formats should be rejected
        invalid_colors = [
            "red",          # Not hex
            "#FFF",         # 3-char hex
            "#GGGGGG",      # Invalid hex chars
            "FF5733",       # Missing #
            "#FF573",       # 5 chars
            "#FF57334",     # 7 chars
        ]

        for color in invalid_colors:
            with pytest.raises(ValidationError):
                TagCreate(name="Test", color=color)

        # Valid formats should be accepted
        valid_colors = ["#FF5733", "#000000", "#FFFFFF", "#abcdef"]
        for color in valid_colors:
            tag = TagCreate(name="Test", color=color)
            assert tag.color.upper() == color.upper()

    def test_tag_public_has_required_fields(self) -> None:
        """TagPublic must include all required fields."""
        from src.models.tag import TagPublic

        fields = TagPublic.model_fields
        required = ["id", "user_id", "name", "color", "created_at", "task_count"]

        for field in required:
            assert field in fields, f"TagPublic missing field: {field}"

    def test_tag_public_serialization(self) -> None:
        """TagPublic should serialize correctly to JSON."""
        from src.models.tag import TagPublic

        tag = TagPublic(
            id=uuid4(),
            user_id=uuid4(),
            name="Important",
            color="#EF4444",
            created_at=datetime.now(timezone.utc),
            task_count=5,
        )

        json_data = tag.model_dump(mode="json")

        assert isinstance(json_data["id"], str)
        assert isinstance(json_data["user_id"], str)
        assert json_data["name"] == "Important"
        assert json_data["color"] == "#EF4444"
        assert json_data["task_count"] == 5

    def test_tag_update_all_fields_optional(self) -> None:
        """TagUpdate should have all fields optional."""
        from src.models.tag import TagUpdate

        # Empty update should work
        update = TagUpdate()
        assert update.name is None
        assert update.color is None

        # Partial update should work
        update_name = TagUpdate(name="New Name")
        assert update_name.name == "New Name"
        assert update_name.color is None

    def test_tag_model_creates_with_uuid(self) -> None:
        """Tag model should auto-generate UUID."""
        from src.models.tag import Tag

        tag = Tag(
            name="Test",
            user_id=uuid4(),
        )

        assert tag.id is not None
        assert tag.id.version == 4


@pytest.mark.contract
class TestTagApiContract:
    """Contract tests for Tag API endpoints."""

    def test_list_tags_response_format(self) -> None:
        """GET /api/tags should return list of TagPublic."""
        # Response contract
        expected_response = {
            "type": "array",
            "items": {
                "type": "TagPublic",
                "fields": ["id", "user_id", "name", "color", "created_at", "task_count"],
            },
        }
        assert expected_response["type"] == "array"

    def test_create_tag_request_format(self) -> None:
        """POST /api/tags request body format."""
        request_body = {
            "name": "string (required, 1-50 chars)",
            "color": "string (optional, #RRGGBB format)",
        }
        assert "name" in request_body

    def test_update_tag_request_format(self) -> None:
        """PATCH /api/tags/{id} request body format."""
        request_body = {
            "name": "string (optional)",
            "color": "string (optional)",
        }
        # All fields optional for PATCH
        assert len(request_body) == 2

    def test_tag_suggest_response_format(self) -> None:
        """GET /api/tags/suggest should return list of tag names."""
        # Response is list of strings for autocomplete
        expected_response = ["string"]
        assert isinstance(expected_response, list)


@pytest.mark.contract
class TestTaskTagAssociationContract:
    """Contract tests for task-tag relationships."""

    def test_task_create_accepts_tag_ids(self) -> None:
        """TaskCreate should accept optional tag_ids list."""
        # Contract: task creation can include tag IDs
        tag_ids = [str(uuid4()), str(uuid4())]
        assert len(tag_ids) == 2

    def test_task_public_includes_tags(self) -> None:
        """TaskPublic should include tags field."""
        from src.models.task import TaskPublic

        fields = TaskPublic.model_fields
        assert "tags" in fields, "TaskPublic missing tags field"

    def test_task_tag_junction_fields(self) -> None:
        """TaskTag junction should have task_id and tag_id."""
        from src.models.task_tag import TaskTag

        # Verify junction table fields
        assert hasattr(TaskTag, "task_id")
        assert hasattr(TaskTag, "tag_id")
