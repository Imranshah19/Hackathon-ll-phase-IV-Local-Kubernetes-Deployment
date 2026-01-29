"""
Reminder API routes for Phase 5 - User Story 5.

Endpoints:
- GET /api/reminders - List user's reminders (with optional task filter)
- POST /api/reminders - Create a new reminder
- GET /api/reminders/{reminder_id} - Get a specific reminder
- DELETE /api/reminders/{reminder_id} - Delete a reminder
- GET /api/reminders/stream - SSE stream for real-time notifications

All endpoints enforce user isolation via task ownership.
"""

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from src.auth.dependencies import CurrentUserId, DbSession
from src.config.scheduler import connection_manager
from src.models.reminder import ReminderCreate, ReminderPublic
from src.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def reminder_to_public(reminder) -> ReminderPublic:
    """Convert Reminder entity to ReminderPublic schema."""
    return ReminderPublic(
        id=reminder.id,
        task_id=reminder.task_id,
        remind_at=reminder.remind_at,
        message=reminder.message,
        sent=reminder.sent,
        sent_at=reminder.sent_at,
        created_at=reminder.created_at,
    )


# =============================================================================
# Routes
# =============================================================================


@router.get(
    "",
    response_model=list[ReminderPublic],
    summary="List all reminders",
)
async def list_reminders(
    session: DbSession,
    user_id: CurrentUserId,
    task_id: UUID | None = Query(default=None, description="Filter by task ID"),
) -> list[ReminderPublic]:
    """
    Get all reminders for the current user's tasks.

    Optional filter:
    - task_id: Filter reminders for a specific task
    """
    service = ReminderService(session, user_id)
    reminders = service.list_reminders(task_id)
    return [reminder_to_public(r) for r in reminders]


@router.post(
    "",
    response_model=ReminderPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new reminder",
)
async def create_reminder(
    data: ReminderCreate,
    session: DbSession,
    user_id: CurrentUserId,
) -> ReminderPublic:
    """
    Create a new reminder for a task.

    Validations:
    - Task must exist and belong to the current user
    - remind_at must be in the future
    - Maximum 3 reminders per task (FR-018)
    """
    service = ReminderService(session, user_id)
    try:
        reminder = service.create_reminder(data)
        return reminder_to_public(reminder)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/stream",
    summary="SSE stream for reminder notifications",
)
async def reminder_stream(
    user_id: CurrentUserId,
):
    """
    Server-Sent Events (SSE) stream for real-time reminder notifications.

    Connect to this endpoint to receive reminder notifications as they become due.
    The connection stays open and messages are pushed to the client.

    Message format:
    ```
    data: {"type": "reminder", "data": {...}, "timestamp": "..."}
    ```
    """

    async def event_generator():
        queue = await connection_manager.connect(user_id)
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE connection established'})}\n\n"

            while True:
                try:
                    # Wait for message with timeout to allow periodic keepalive
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield f": keepalive\n\n"
                except asyncio.CancelledError:
                    break
        finally:
            await connection_manager.disconnect(user_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get(
    "/{reminder_id}",
    response_model=ReminderPublic,
    summary="Get a specific reminder",
)
async def get_reminder(
    reminder_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
) -> ReminderPublic:
    """
    Get a reminder by ID.

    Returns 404 if reminder not found or belongs to another user's task.
    """
    service = ReminderService(session, user_id)
    reminder = service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )
    return reminder_to_public(reminder)


@router.delete(
    "/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a reminder",
)
async def delete_reminder(
    reminder_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
) -> None:
    """
    Delete a reminder by ID.

    Returns 404 if reminder not found or belongs to another user's task.
    Returns 204 No Content on success.
    """
    service = ReminderService(session, user_id)
    deleted = service.delete_reminder(reminder_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )


__all__ = ["router"]
