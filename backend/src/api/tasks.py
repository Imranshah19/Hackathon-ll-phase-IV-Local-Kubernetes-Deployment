"""
Task CRUD API routes.

Endpoints:
- GET /api/tasks - List user's tasks (with filters and sorting)
- POST /api/tasks - Create a new task
- GET /api/tasks/{task_id} - Get a specific task
- PATCH /api/tasks/{task_id} - Update a task
- DELETE /api/tasks/{task_id} - Delete a task
- POST /api/tasks/{task_id}/complete - Complete a task (with recurrence support)

All endpoints enforce user isolation - users can only access their own tasks.

Phase 5 additions:
- Priority filter and sort
- Due date filter
- Enhanced sorting options
- Tag association and filtering (US2)
- Recurring tasks (US4): Create with recurrence, auto-generate next instance
"""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import select

from src.auth.dependencies import CurrentUserId, DbSession
from src.models.base import utc_now
from src.models.task import Task, TaskCreate, TaskPublic, TaskUpdate
from src.models.tag import Tag
from src.models.task_tag import TaskTag
from src.models.recurrence import (
    RecurrenceRule,
    RecurrenceRuleCreate,
    RecurrenceRulePublic,
    RecurrenceFrequency,
    RecurrenceEndType,
)
from src.services.tag_service import TagService
from src.services.recurrence_service import RecurrenceService
from src.services.task_event_service import TaskEventService


# =============================================================================
# Extended Request Schemas (with tag and recurrence support)
# =============================================================================


class RecurrenceInput(BaseModel):
    """Recurrence configuration for task creation."""
    frequency: RecurrenceFrequency
    interval: int = 1
    end_type: RecurrenceEndType = RecurrenceEndType.NEVER
    end_count: Optional[int] = None
    end_date: Optional[str] = None  # ISO date string


class TaskCreateWithTags(TaskCreate):
    """Task creation with optional tag IDs and recurrence."""
    tag_ids: list[UUID] | None = None
    recurrence: Optional[RecurrenceInput] = None


class TaskUpdateWithTags(TaskUpdate):
    """Task update with optional tag IDs and series option."""
    tag_ids: list[UUID] | None = None
    update_series: bool = False  # If true, update all future instances


class TaskCompleteResponse(BaseModel):
    """Response for completing a task."""
    task: TaskPublic
    next_instance: Optional[TaskPublic] = None  # Created if recurring


class TaskDeleteRequest(BaseModel):
    """Request body for delete with series option."""
    delete_series: bool = False  # If true, delete all future instances


# =============================================================================
# Enums for Query Parameters
# =============================================================================


class SortField(str, Enum):
    """Valid fields for sorting tasks."""
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    PRIORITY = "priority"
    DUE = "due"
    TITLE = "title"

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def get_user_task(session: DbSession, task_id: UUID, user_id: UUID) -> Task:
    """
    Get a task by ID, ensuring it belongs to the current user.

    Args:
        session: Database session
        task_id: Task UUID
        user_id: Current user's UUID

    Returns:
        Task: The task entity

    Raises:
        HTTPException 404: If task not found or belongs to another user
    """
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


def get_task_tags(session: DbSession, task_id: UUID) -> list[str]:
    """Get tag names for a task."""
    query = (
        select(Tag.name)
        .join(TaskTag, Tag.id == TaskTag.tag_id)
        .where(TaskTag.task_id == task_id)
    )
    return list(session.exec(query).all())


def set_task_tags(session: DbSession, task_id: UUID, user_id: UUID, tag_ids: list[UUID]) -> None:
    """Set tags for a task (replaces existing associations)."""
    # Remove existing associations
    existing = session.exec(
        select(TaskTag).where(TaskTag.task_id == task_id)
    ).all()
    for tt in existing:
        session.delete(tt)

    # Validate tag ownership and add new associations
    tag_service = TagService(session, user_id)
    valid_tags = tag_service.get_tags_by_ids(tag_ids)

    for tag in valid_tags:
        session.add(TaskTag(task_id=task_id, tag_id=tag.id))


def task_to_public(session: DbSession, task: Task) -> TaskPublic:
    """Convert Task to TaskPublic with tags populated."""
    tags = get_task_tags(session, task.id)
    return TaskPublic(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        is_completed=task.is_completed,
        priority=task.priority,
        due=task.due,
        created_at=task.created_at,
        updated_at=task.updated_at,
        recurrence_rule_id=task.recurrence_rule_id,
        parent_task_id=task.parent_task_id,
        tags=tags,
    )


# =============================================================================
# Routes
# =============================================================================


@router.get(
    "",
    response_model=list[TaskPublic],
    summary="List all tasks",
)
async def list_tasks(
    session: DbSession,
    user_id: CurrentUserId,
    completed: bool | None = None,
    search: str | None = None,
    priority: list[int] | None = Query(default=None, ge=1, le=5),
    due_from: datetime | None = None,
    due_to: datetime | None = None,
    tags: list[UUID] | None = Query(default=None),
    sort_by: SortField = SortField.CREATED_AT,
    sort_order: Literal["asc", "desc"] = "desc",
) -> list[TaskPublic]:
    """
    Get all tasks for the current user.

    Optional filters:
    - completed: Filter by completion status (true/false)
    - search: Filter by title containing search term (case-insensitive)
    - priority: Filter by priority levels (1-5, can specify multiple)
    - due_from: Filter tasks due on or after this date
    - due_to: Filter tasks due on or before this date
    - tags: Filter by tag IDs (tasks must have ALL specified tags)

    Sorting:
    - sort_by: Field to sort by (created_at, updated_at, priority, due, title)
    - sort_order: Sort direction (asc, desc)

    Results are ordered by the specified sort field (default: created_at desc).
    """
    query = select(Task).where(Task.user_id == user_id)

    # Completion filter
    if completed is not None:
        query = query.where(Task.is_completed == completed)

    # Search filter
    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))  # type: ignore

    # Priority filter (Phase 5)
    if priority:
        query = query.where(Task.priority.in_(priority))  # type: ignore

    # Due date range filter (Phase 5)
    if due_from:
        query = query.where(Task.due >= due_from)  # type: ignore

    if due_to:
        query = query.where(Task.due <= due_to)  # type: ignore

    # Tag filter (Phase 5 - US2)
    if tags:
        # Tasks must have ALL specified tags (AND logic)
        for tag_id in tags:
            subquery = select(TaskTag.task_id).where(TaskTag.tag_id == tag_id)
            query = query.where(Task.id.in_(subquery))  # type: ignore

    # Sorting (Phase 5)
    sort_column = getattr(Task, sort_by.value)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())  # type: ignore
    else:
        query = query.order_by(sort_column.asc())  # type: ignore

    tasks = session.exec(query).all()
    return [task_to_public(session, task) for task in tasks]


@router.post(
    "",
    response_model=TaskPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    task_data: TaskCreateWithTags,
    session: DbSession,
    user_id: CurrentUserId,
    background_tasks: BackgroundTasks,
) -> TaskPublic:
    """
    Create a new task for the current user.

    The user_id is automatically set from the JWT token.

    Phase 5: Supports priority (1-5), due date, tag_ids, and recurrence fields.
    Phase 5 US7: Publishes TaskCreated event via Dapr pub/sub.
    """
    recurrence_rule_id = None

    # Create recurrence rule if provided
    if task_data.recurrence:
        from datetime import date as date_type

        recurrence_service = RecurrenceService(session, user_id)
        end_date = None
        if task_data.recurrence.end_date:
            end_date = date_type.fromisoformat(task_data.recurrence.end_date)

        rule = recurrence_service.create_rule(
            RecurrenceRuleCreate(
                frequency=task_data.recurrence.frequency,
                interval=task_data.recurrence.interval,
                end_type=task_data.recurrence.end_type,
                end_count=task_data.recurrence.end_count,
                end_date=end_date,
            )
        )
        recurrence_rule_id = rule.id

    task = Task(
        title=task_data.title,
        description=task_data.description,
        is_completed=task_data.is_completed,
        priority=task_data.priority,
        due=task_data.due,
        user_id=user_id,
        recurrence_rule_id=recurrence_rule_id,
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    # Add tag associations if provided
    if task_data.tag_ids:
        set_task_tags(session, task.id, user_id, task_data.tag_ids)
        session.commit()

    # Publish TaskCreated event (Phase 5 - US7)
    tags = get_task_tags(session, task.id)
    event_service = TaskEventService(session, user_id)
    background_tasks.add_task(event_service.publish_task_created, task, tags)

    return task_to_public(session, task)


@router.get(
    "/{task_id}",
    response_model=TaskPublic,
    summary="Get a specific task",
)
async def get_task(
    task_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
) -> TaskPublic:
    """
    Get a task by ID.

    Returns 404 if task not found or belongs to another user.
    Includes associated tag names.
    """
    task = get_user_task(session, task_id, user_id)
    return task_to_public(session, task)


@router.patch(
    "/{task_id}",
    response_model=TaskPublic,
    summary="Update a task",
)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdateWithTags,
    session: DbSession,
    user_id: CurrentUserId,
    background_tasks: BackgroundTasks,
) -> TaskPublic:
    """
    Partially update a task.

    Only provided fields are updated.
    Returns 404 if task not found or belongs to another user.

    Phase 5: Supports updating tag_ids (replaces all existing tag associations).
    Phase 5 US4: If update_series=true, updates all future instances of recurring task.
    Phase 5 US7: Publishes TaskUpdated event via Dapr pub/sub.
    """
    task = get_user_task(session, task_id, user_id)

    # Update only provided fields (excluding tag_ids and update_series)
    update_data = task_data.model_dump(exclude_unset=True, exclude={"tag_ids", "update_series"})

    for field, value in update_data.items():
        setattr(task, field, value)

    # Update timestamp
    task.updated_at = utc_now()

    session.add(task)

    # Update tags if provided
    if task_data.tag_ids is not None:
        set_task_tags(session, task_id, user_id, task_data.tag_ids)

    # Update series if requested (Phase 5 - US4)
    if task_data.update_series and task.recurrence_rule_id:
        recurrence_service = RecurrenceService(session, user_id)
        recurrence_service.update_future_instances(
            task,
            title=update_data.get("title"),
            description=update_data.get("description"),
            priority=update_data.get("priority"),
        )

    session.commit()
    session.refresh(task)

    # Publish TaskUpdated event (Phase 5 - US7)
    tags = get_task_tags(session, task.id)
    event_service = TaskEventService(session, user_id)
    background_tasks.add_task(event_service.publish_task_updated, task, tags)

    return task_to_public(session, task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
async def delete_task(
    task_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
    background_tasks: BackgroundTasks,
    delete_series: bool = Query(default=False),
) -> None:
    """
    Delete a task by ID.

    Returns 404 if task not found or belongs to another user.
    Returns 204 No Content on success.

    Phase 5 US4: If delete_series=true, deletes all future instances of recurring task.
    Phase 5 US7: Publishes TaskDeleted event via Dapr pub/sub.
    """
    task = get_user_task(session, task_id, user_id)

    # Store task info for event before deletion
    task_copy = Task(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        is_completed=task.is_completed,
        priority=task.priority,
        due=task.due,
    )

    # Delete series if requested (Phase 5 - US4)
    if delete_series and task.recurrence_rule_id:
        recurrence_service = RecurrenceService(session, user_id)
        recurrence_service.delete_future_instances(task)

        # Also delete the recurrence rule if no tasks remain
        remaining = session.exec(
            select(Task).where(Task.recurrence_rule_id == task.recurrence_rule_id)
        ).all()
        if len(remaining) <= 1:  # Only the task being deleted
            recurrence_service.delete_rule(task.recurrence_rule_id)
    else:
        session.delete(task)

    session.commit()

    # Publish TaskDeleted event (Phase 5 - US7)
    event_service = TaskEventService(session, user_id)
    background_tasks.add_task(event_service.publish_task_deleted, task_copy, delete_series)


@router.post(
    "/{task_id}/complete",
    response_model=TaskCompleteResponse,
    summary="Complete a task",
)
async def complete_task(
    task_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
    background_tasks: BackgroundTasks,
) -> TaskCompleteResponse:
    """
    Mark a task as completed.

    Phase 5 US4: If the task is recurring, automatically creates the next instance.
    Phase 5 US7: Publishes TaskCompleted event via Dapr pub/sub.

    Returns:
        TaskCompleteResponse with completed task and next_instance (if recurring)
    """
    task = get_user_task(session, task_id, user_id)

    # Mark as completed
    task.is_completed = True
    task.updated_at = utc_now()
    session.add(task)
    session.commit()
    session.refresh(task)

    next_instance = None
    next_task_id = None

    # Create next instance if recurring (Phase 5 - US4)
    if task.recurrence_rule_id:
        recurrence_service = RecurrenceService(session, user_id)
        rule = recurrence_service.get_rule(task.recurrence_rule_id)

        if rule:
            next_task = recurrence_service.create_next_instance(task, rule)
            if next_task:
                next_task_id = next_task.id
                # Copy tags to next instance
                original_tags = get_task_tags(session, task.id)
                if original_tags:
                    tag_service = TagService(session, user_id)
                    tags = tag_service.get_or_create_tags_by_names(original_tags)
                    for tag in tags:
                        session.add(TaskTag(task_id=next_task.id, tag_id=tag.id))
                    session.commit()

                next_instance = task_to_public(session, next_task)

    # Publish TaskCompleted event (Phase 5 - US7)
    tags = get_task_tags(session, task.id)
    event_service = TaskEventService(session, user_id)
    background_tasks.add_task(
        event_service.publish_task_completed,
        task,
        tags,
        next_task_id,
    )

    return TaskCompleteResponse(
        task=task_to_public(session, task),
        next_instance=next_instance,
    )


__all__ = ["router", "SortField", "TaskCompleteResponse"]
