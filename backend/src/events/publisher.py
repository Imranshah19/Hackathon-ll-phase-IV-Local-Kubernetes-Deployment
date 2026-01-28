"""
Phase 5: Dapr Pub/Sub Publisher Client

Publishes task lifecycle events to Kafka via Dapr sidecar.

Usage:
    publisher = EventPublisher()
    await publisher.publish(event)

Configuration:
    DAPR_HTTP_PORT: Dapr sidecar HTTP port (default: 3500)
    PUBSUB_NAME: Dapr pub/sub component name (default: kafka-pubsub)
    TOPIC_NAME: Topic to publish to (default: task-events)
"""

import os
import logging
from datetime import datetime
from typing import Any

import httpx

from src.events.schemas import CloudEvent, TaskEventData, TaskEventType

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Dapr pub/sub publisher for task events.

    Publishes CloudEvents-formatted messages to Kafka via Dapr sidecar.
    Implements retry logic for failed publishes.
    """

    def __init__(
        self,
        dapr_port: int | None = None,
        pubsub_name: str | None = None,
        topic_name: str | None = None,
    ):
        """
        Initialize the event publisher.

        Args:
            dapr_port: Dapr sidecar HTTP port (default from DAPR_HTTP_PORT env)
            pubsub_name: Dapr pub/sub component name (default from PUBSUB_NAME env)
            topic_name: Topic to publish to (default from TOPIC_NAME env)
        """
        self.dapr_port = dapr_port or int(os.getenv("DAPR_HTTP_PORT", "3500"))
        self.pubsub_name = pubsub_name or os.getenv("PUBSUB_NAME", "todo-pubsub")
        self.topic_name = topic_name or os.getenv("TOPIC_NAME", "task-events")
        self.base_url = f"http://localhost:{self.dapr_port}"
        self._client: httpx.AsyncClient | None = None

    @property
    def publish_url(self) -> str:
        """Construct the Dapr publish URL."""
        return f"{self.base_url}/v1.0/publish/{self.pubsub_name}/{self.topic_name}"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def publish(
        self,
        event: CloudEvent,
        retry_count: int = 3,
    ) -> bool:
        """
        Publish a CloudEvent to the message broker.

        Args:
            event: CloudEvent to publish
            retry_count: Number of retries on failure

        Returns:
            bool: True if published successfully, False otherwise
        """
        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(retry_count):
            try:
                response = await client.post(
                    self.publish_url,
                    json=event.model_dump(mode="json"),
                    headers={
                        "Content-Type": "application/cloudevents+json",
                    },
                )

                if response.status_code in (200, 204):
                    logger.info(
                        "Event published successfully",
                        extra={
                            "event_id": event.id,
                            "event_type": event.type,
                            "attempt": attempt + 1,
                        },
                    )
                    return True

                logger.warning(
                    "Publish failed with status %d: %s",
                    response.status_code,
                    response.text,
                    extra={"attempt": attempt + 1},
                )

            except httpx.HTTPError as e:
                last_error = e
                logger.warning(
                    "Publish attempt %d failed: %s",
                    attempt + 1,
                    str(e),
                )

        logger.error(
            "All publish attempts failed for event %s",
            event.id,
            exc_info=last_error,
        )
        return False

    async def publish_task_event(
        self,
        event_type: TaskEventType,
        task_data: TaskEventData,
    ) -> bool:
        """
        Convenience method to publish a task lifecycle event.

        Args:
            event_type: Type of task event
            task_data: Task data for the event payload

        Returns:
            bool: True if published successfully
        """
        event = CloudEvent(
            type=event_type.value,
            subject=str(task_data.task_id),
            data=task_data.model_dump(mode="json"),
        )
        return await self.publish(event)

    def is_available(self) -> bool:
        """
        Check if Dapr sidecar is available.

        Returns:
            bool: True if Dapr is running and accessible
        """
        # Check if running in Dapr environment
        return os.getenv("DAPR_HTTP_PORT") is not None


# Global publisher instance (lazy initialization)
_publisher: EventPublisher | None = None


def get_publisher() -> EventPublisher:
    """Get the global event publisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher


__all__ = [
    "EventPublisher",
    "get_publisher",
]
