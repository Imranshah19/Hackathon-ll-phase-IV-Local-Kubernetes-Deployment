"""
Tag Service for Phase 5 - User Story 2.

Provides business logic for tag management:
- CRUD operations for tags
- Task-tag association management
- Tag suggestions and counts
"""

from uuid import UUID

from sqlmodel import Session, select, func

from src.models.tag import Tag, TagCreate, TagUpdate, TagPublic
from src.models.task_tag import TaskTag


class TagService:
    """
    Service for tag management operations.

    All operations are scoped to the authenticated user.
    """

    def __init__(self, session: Session, user_id: UUID):
        """
        Initialize the tag service.

        Args:
            session: Database session
            user_id: Current user's UUID
        """
        self.session = session
        self.user_id = user_id

    def list_tags(self) -> list[TagPublic]:
        """
        Get all tags for the current user with task counts.

        Returns:
            List of TagPublic with task_count populated
        """
        # Query tags with task count
        query = (
            select(Tag, func.count(TaskTag.task_id).label("task_count"))
            .outerjoin(TaskTag, Tag.id == TaskTag.tag_id)
            .where(Tag.user_id == self.user_id)
            .group_by(Tag.id)
            .order_by(Tag.name)
        )

        results = self.session.exec(query).all()

        return [
            TagPublic(
                id=tag.id,
                user_id=tag.user_id,
                name=tag.name,
                color=tag.color,
                created_at=tag.created_at,
                task_count=count,
            )
            for tag, count in results
        ]

    def get_tag(self, tag_id: UUID) -> Tag | None:
        """
        Get a specific tag by ID.

        Args:
            tag_id: Tag UUID

        Returns:
            Tag if found and belongs to user, None otherwise
        """
        return self.session.exec(
            select(Tag).where(Tag.id == tag_id, Tag.user_id == self.user_id)
        ).first()

    def get_tag_by_name(self, name: str) -> Tag | None:
        """
        Get a tag by name for the current user.

        Args:
            name: Tag name (case-insensitive)

        Returns:
            Tag if found, None otherwise
        """
        return self.session.exec(
            select(Tag).where(
                Tag.user_id == self.user_id,
                func.lower(Tag.name) == name.lower()
            )
        ).first()

    def create_tag(self, data: TagCreate) -> Tag:
        """
        Create a new tag.

        Args:
            data: Tag creation data

        Returns:
            Created tag

        Raises:
            ValueError: If tag name already exists for user
        """
        # Check for duplicate name
        existing = self.get_tag_by_name(data.name)
        if existing:
            raise ValueError(f"Tag '{data.name}' already exists")

        tag = Tag(
            name=data.name,
            color=data.color,
            user_id=self.user_id,
        )

        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)

        return tag

    def update_tag(self, tag_id: UUID, data: TagUpdate) -> Tag:
        """
        Update an existing tag.

        Args:
            tag_id: Tag UUID
            data: Update data

        Returns:
            Updated tag

        Raises:
            ValueError: If tag not found or name already exists
        """
        tag = self.get_tag(tag_id)
        if not tag:
            raise ValueError("Tag not found")

        update_data = data.model_dump(exclude_unset=True)

        # Check for duplicate name if changing
        if "name" in update_data and update_data["name"] != tag.name:
            existing = self.get_tag_by_name(update_data["name"])
            if existing:
                raise ValueError(f"Tag '{update_data['name']}' already exists")

        for field, value in update_data.items():
            setattr(tag, field, value)

        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)

        return tag

    def delete_tag(self, tag_id: UUID) -> bool:
        """
        Delete a tag.

        Args:
            tag_id: Tag UUID

        Returns:
            True if deleted, False if not found

        Note:
            TaskTag associations are automatically deleted via CASCADE.
        """
        tag = self.get_tag(tag_id)
        if not tag:
            return False

        self.session.delete(tag)
        self.session.commit()
        return True

    def suggest_tags(self, prefix: str = "", limit: int = 10) -> list[str]:
        """
        Get tag name suggestions for autocomplete.

        Args:
            prefix: Prefix to match (case-insensitive)
            limit: Maximum number of suggestions

        Returns:
            List of tag names matching prefix
        """
        query = select(Tag.name).where(Tag.user_id == self.user_id)

        if prefix:
            query = query.where(Tag.name.ilike(f"{prefix}%"))

        query = query.order_by(Tag.name).limit(limit)

        return list(self.session.exec(query).all())

    def get_tags_by_ids(self, tag_ids: list[UUID]) -> list[Tag]:
        """
        Get multiple tags by their IDs.

        Args:
            tag_ids: List of tag UUIDs

        Returns:
            List of tags belonging to user
        """
        if not tag_ids:
            return []

        return list(self.session.exec(
            select(Tag).where(
                Tag.id.in_(tag_ids),
                Tag.user_id == self.user_id
            )
        ).all())

    def get_or_create_tags_by_names(self, names: list[str]) -> list[Tag]:
        """
        Get existing tags or create new ones by name.

        Useful for quick tag assignment without explicit creation.

        Args:
            names: List of tag names

        Returns:
            List of tags (existing or newly created)
        """
        tags = []
        for name in names:
            name = name.strip()
            if not name:
                continue

            tag = self.get_tag_by_name(name)
            if not tag:
                tag = Tag(name=name, user_id=self.user_id)
                self.session.add(tag)

            tags.append(tag)

        if tags:
            self.session.commit()
            for tag in tags:
                self.session.refresh(tag)

        return tags


__all__ = ["TagService"]
