"""
Phase 5: Event-Driven Architecture Module

This module provides event publishing and handling for the Todo App:
- Task lifecycle events (created, updated, completed, deleted)
- Dapr pub/sub integration with Kafka
- CloudEvents format for message schema

Exports:
- EventPublisher: Publishes events to Dapr pub/sub
- TaskEventType: Enum of task event types
- CloudEvent: Event schema following CloudEvents spec
"""

from src.events.schemas import CloudEvent, TaskEventData, TaskEventType
from src.events.publisher import EventPublisher, get_publisher

__all__ = [
    "CloudEvent",
    "TaskEventData",
    "TaskEventType",
    "EventPublisher",
    "get_publisher",
]
