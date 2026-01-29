"""
Background task scheduler and SSE connection manager for Phase 5 reminders.

Provides:
- ConnectionManager: Manages SSE connections per user
- check_due_reminders: Background task that checks and sends due reminders
"""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session

from src.db import engine
from src.models.reminder import Reminder
from src.models.task import Task
from src.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages Server-Sent Events (SSE) connections for real-time notifications.

    Each user has a queue for receiving reminder notifications.
    """

    def __init__(self):
        # Map user_id -> asyncio.Queue for SSE messages
        self._connections: dict[UUID, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: UUID) -> asyncio.Queue:
        """
        Register a new SSE connection for a user.

        Args:
            user_id: The user's UUID

        Returns:
            asyncio.Queue for receiving messages
        """
        async with self._lock:
            # Disconnect any existing connection
            if user_id in self._connections:
                await self.disconnect(user_id)

            queue: asyncio.Queue = asyncio.Queue()
            self._connections[user_id] = queue
            logger.debug(f"User {user_id} connected to SSE")
            return queue

    async def disconnect(self, user_id: UUID) -> None:
        """
        Remove a user's SSE connection.

        Args:
            user_id: The user's UUID
        """
        async with self._lock:
            if user_id in self._connections:
                del self._connections[user_id]
                logger.debug(f"User {user_id} disconnected from SSE")

    async def send_reminder(
        self, user_id: UUID, reminder: Reminder, task: Task
    ) -> bool:
        """
        Send a reminder notification to a user's SSE connection.

        Args:
            user_id: The user's UUID
            reminder: The reminder to send
            task: The associated task

        Returns:
            True if message was queued, False if user not connected
        """
        async with self._lock:
            if user_id not in self._connections:
                return False

            message = {
                "type": "reminder",
                "data": {
                    "reminder_id": str(reminder.id),
                    "task_id": str(task.id),
                    "task_title": task.title,
                    "message": reminder.message or f"Reminder: {task.title}",
                    "remind_at": reminder.remind_at.isoformat() if reminder.remind_at else None,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            try:
                await self._connections[user_id].put(message)
                return True
            except Exception as e:
                logger.error(f"Failed to queue reminder for user {user_id}: {e}")
                return False

    def is_connected(self, user_id: UUID) -> bool:
        """Check if a user has an active SSE connection."""
        return user_id in self._connections

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)


# Global connection manager instance
connection_manager = ConnectionManager()


async def check_due_reminders() -> None:
    """
    Background task that periodically checks for due reminders.

    Runs every 10 seconds and:
    1. Queries reminders where remind_at <= now() AND sent = False
    2. For each due reminder, sends to user's SSE queue
    3. Marks reminder as sent
    """
    logger.info("Starting reminder checker background task")

    while True:
        try:
            with Session(engine) as session:
                # Get all due reminders
                due_reminders = ReminderService.get_due_reminders_for_all_users(session)

                for reminder in due_reminders:
                    try:
                        # Load the task for context
                        task = session.get(Task, reminder.task_id)
                        if not task:
                            logger.warning(f"Task {reminder.task_id} not found for reminder {reminder.id}")
                            ReminderService.mark_as_sent(session, reminder.id)
                            continue

                        # Send to user's SSE connection
                        sent = await connection_manager.send_reminder(
                            task.user_id, reminder, task
                        )

                        # Mark as sent regardless of connection status
                        # (user might not be online, but reminder should not repeat)
                        ReminderService.mark_as_sent(session, reminder.id)

                        if sent:
                            logger.info(
                                f"Sent reminder {reminder.id} for task '{task.title}' to user {task.user_id}"
                            )
                        else:
                            logger.debug(
                                f"User {task.user_id} not connected, marked reminder {reminder.id} as sent"
                            )

                    except Exception as e:
                        logger.error(f"Error processing reminder {reminder.id}: {e}")

        except Exception as e:
            logger.error(f"Error in reminder checker: {e}")

        # Wait 10 seconds before next check
        await asyncio.sleep(10)


__all__ = ["ConnectionManager", "connection_manager", "check_due_reminders"]
