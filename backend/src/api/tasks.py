"""
Task CRUD API routes.

Endpoints:
- GET /api/tasks - List user's tasks
- POST /api/tasks - Create a new task
- GET /api/tasks/{task_id} - Get a specific task
- PATCH /api/tasks/{task_id} - Update a task
- DELETE /api/tasks/{task_id} - Delete a task

All endpoints enforce user isolation - users can only access their own tasks.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from src.auth.dependencies import CurrentUserId, DbSession
from src.models.base import utc_now
from src.models.task import Task, TaskCreate, TaskPublic, TaskUpdate

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
) -> list[TaskPublic]:
    """
    Get all tasks for the current user.

    Optional filters:
    - completed: Filter by completion status (true/false)
    - search: Filter by title containing search term (case-insensitive)

    Results are ordered by creation date (newest first).
    """
    query = select(Task).where(Task.user_id == user_id)

    if completed is not None:
        query = query.where(Task.is_completed == completed)

    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))  # type: ignore

    query = query.order_by(Task.created_at.desc())  # type: ignore

    tasks = session.exec(query).all()
    return [TaskPublic.model_validate(task) for task in tasks]


@router.post(
    "",
    response_model=TaskPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    task_data: TaskCreate,
    session: DbSession,
    user_id: CurrentUserId,
) -> TaskPublic:
    """
    Create a new task for the current user.

    The user_id is automatically set from the JWT token.
    """
    task = Task(
        title=task_data.title,
        description=task_data.description,
        is_completed=task_data.is_completed,
        user_id=user_id,
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    return TaskPublic.model_validate(task)


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
    """
    task = get_user_task(session, task_id, user_id)
    return TaskPublic.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskPublic,
    summary="Update a task",
)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    session: DbSession,
    user_id: CurrentUserId,
) -> TaskPublic:
    """
    Partially update a task.

    Only provided fields are updated.
    Returns 404 if task not found or belongs to another user.
    """
    task = get_user_task(session, task_id, user_id)

    # Update only provided fields
    update_data = task_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(task, field, value)

    # Update timestamp
    task.updated_at = utc_now()

    session.add(task)
    session.commit()
    session.refresh(task)

    return TaskPublic.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
async def delete_task(
    task_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
) -> None:
    """
    Delete a task by ID.

    Returns 404 if task not found or belongs to another user.
    Returns 204 No Content on success.
    """
    task = get_user_task(session, task_id, user_id)

    session.delete(task)
    session.commit()


__all__ = ["router"]
