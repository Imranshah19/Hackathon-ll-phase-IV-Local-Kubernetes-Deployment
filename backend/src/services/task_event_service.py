"""
Task Event Service for Phase 5 - US7 Event-Driven Architecture.

Publishes task lifecycle events to Dapr pub/sub (Kafka).
Events are published asynchronously after task operations complete.

Implements:
- FR-025: Publish TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted events
- FR-026: Include full task details in event payloads
- FR-027: Operations succeed even if event publishing fails
- FR-028: Support event replay via TaskEvent table

Usage:
    from src.services.task_event_service import TaskEventService

    event_service = TaskEventService(session, user_id)
    await event_service.publish_task_created(task)
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlmodel import Session

from src.events.publisher import get_publisher, EventPublisher
from src.events.schemas import TaskEventType, TaskEventData
from src.models.task import Task
from src.models.task_event import TaskEvent

logger = logging.getLogger(__name__)


class TaskEventService:
    """
    Service for publishing task lifecycle events.

    Events are published to Dapr pub/sub and stored in task_events table
    for replay/recovery scenarios.
    """

    def __init__(self, session: Session, user_id: UUID):
        """
        Initialize the event service.

        Args:
            session: Database session for storing events
            user_id: Current user's UUID
        """
        self.session = session
        self.user_id = user_id
        self._publisher: EventPublisher | None = None

    @property
    def publisher(self) -> EventPublisher:
        """Get the Dapr event publisher."""
        if self._publisher is None:
            self._publisher = get_publisher()
        return self._publisher

    def _task_to_event_data(self, task: Task, tags: list[str] | None = None) -> TaskEventData:
        """
        Convert a Task to TaskEventData.

        Args:
            task: The task entity
            tags: Optional list of tag names

        Returns:
            TaskEventData for the event payload
        """
        return TaskEventData(
            task_id=task.id,
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            is_completed=task.is_completed,
            priority=task.priority,
            due=task.due,
            tags=tags or [],
            timestamp=datetime.utcnow(),
        )

    def _store_event(
        self,
        task: Task,
        event_type: TaskEventType,
        event_data: dict,
    ) -> TaskEvent:
        """
        Store event in database for replay/recovery.

        Args:
            task: The task entity
            event_type: Type of event
            event_data: Event payload data

        Returns:
            Created TaskEvent record
        """
        task_event = TaskEvent(
            task_id=task.id,
            user_id=self.user_id,
            event_type=event_type.value,
            event_data=event_data,
            published=False,
        )
        self.session.add(task_event)
        self.session.commit()
        self.session.refresh(task_event)
        return task_event

    def _mark_event_published(self, task_event: TaskEvent) -> None:
        """Mark an event as successfully published."""
        task_event.published = True
        task_event.published_at = datetime.utcnow()
        self.session.add(task_event)
        self.session.commit()

    async def publish_task_created(
        self,
        task: Task,
        tags: list[str] | None = None,
    ) -> bool:
        """
        Publish a TaskCreated event.

        Args:
            task: The created task
            tags: Tag names associated with the task

        Returns:
            True if published successfully
        """
        event_data = self._task_to_event_data(task, tags)

        # Store event first
        task_event = self._store_event(
            task,
            TaskEventType.CREATED,
            event_data.model_dump(mode="json"),
        )

        # Check if Dapr is available
        if not self.publisher.is_available():
            logger.info("Dapr not available, event stored for later delivery")
            return False

        # Publish to Dapr
        try:
            success = await self.publisher.publish_task_event(
                TaskEventType.CREATED,
                event_data,
            )
            if success:
                self._mark_event_published(task_event)
            return success
        except Exception as e:
            logger.error(f"Failed to publish TaskCreated event: {e}")
            return False

    async def publish_task_updated(
        self,
        task: Task,
        tags: list[str] | None = None,
    ) -> bool:
        """
        Publish a TaskUpdated event.

        Args:
            task: The updated task
            tags: Current tag names

        Returns:
            True if published successfully
        """
        event_data = self._task_to_event_data(task, tags)

        task_event = self._store_event(
            task,
            TaskEventType.UPDATED,
            event_data.model_dump(mode="json"),
        )

        if not self.publisher.is_available():
            logger.info("Dapr not available, event stored for later delivery")
            return False

        try:
            success = await self.publisher.publish_task_event(
                TaskEventType.UPDATED,
                event_data,
            )
            if success:
                self._mark_event_published(task_event)
            return success
        except Exception as e:
            logger.error(f"Failed to publish TaskUpdated event: {e}")
            return False

    async def publish_task_completed(
        self,
        task: Task,
        tags: list[str] | None = None,
        next_instance_id: UUID | None = None,
    ) -> bool:
        """
        Publish a TaskCompleted event.

        Args:
            task: The completed task
            tags: Current tag names
            next_instance_id: ID of next recurring instance (if any)

        Returns:
            True if published successfully
        """
        event_data = self._task_to_event_data(task, tags)

        # Add recurring task info
        extra_data = event_data.model_dump(mode="json")
        if next_instance_id:
            extra_data["next_instance_id"] = str(next_instance_id)
        if task.recurrence_rule_id:
            extra_data["is_recurring"] = True
            extra_data["recurrence_rule_id"] = str(task.recurrence_rule_id)

        task_event = self._store_event(
            task,
            TaskEventType.COMPLETED,
            extra_data,
        )

        if not self.publisher.is_available():
            logger.info("Dapr not available, event stored for later delivery")
            return False

        try:
            success = await self.publisher.publish_task_event(
                TaskEventType.COMPLETED,
                event_data,
            )
            if success:
                self._mark_event_published(task_event)
            return success
        except Exception as e:
            logger.error(f"Failed to publish TaskCompleted event: {e}")
            return False

    async def publish_task_deleted(
        self,
        task: Task,
        delete_series: bool = False,
    ) -> bool:
        """
        Publish a TaskDeleted event.

        Args:
            task: The deleted task
            delete_series: Whether the entire recurring series was deleted

        Returns:
            True if published successfully
        """
        event_data = self._task_to_event_data(task)

        extra_data = event_data.model_dump(mode="json")
        extra_data["delete_series"] = delete_series

        task_event = self._store_event(
            task,
            TaskEventType.DELETED,
            extra_data,
        )

        if not self.publisher.is_available():
            logger.info("Dapr not available, event stored for later delivery")
            return False

        try:
            success = await self.publisher.publish_task_event(
                TaskEventType.DELETED,
                event_data,
            )
            if success:
                self._mark_event_published(task_event)
            return success
        except Exception as e:
            logger.error(f"Failed to publish TaskDeleted event: {e}")
            return False


# Dependency injection helper
def get_task_event_service(session: Session, user_id: UUID) -> TaskEventService:
    """Get a TaskEventService instance."""
    return TaskEventService(session, user_id)


__all__ = ["TaskEventService", "get_task_event_service"]
