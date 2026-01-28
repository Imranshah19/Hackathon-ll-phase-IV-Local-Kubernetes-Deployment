"""
Tag CRUD API routes (Phase 5 - User Story 2).

Endpoints:
- GET /api/tags - List user's tags with task counts
- POST /api/tags - Create a new tag
- GET /api/tags/suggest - Get tag name suggestions
- GET /api/tags/{tag_id} - Get a specific tag
- PATCH /api/tags/{tag_id} - Update a tag
- DELETE /api/tags/{tag_id} - Delete a tag

All endpoints enforce user isolation - users can only access their own tags.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.auth.dependencies import CurrentUserId, DbSession
from src.models.tag import Tag, TagCreate, TagPublic, TagUpdate
from src.services.tag_service import TagService

router = APIRouter()


# =============================================================================
# Routes
# =============================================================================


@router.get(
    "",
    response_model=list[TagPublic],
    summary="List all tags",
)
async def list_tags(
    session: DbSession,
    user_id: CurrentUserId,
) -> list[TagPublic]:
    """
    Get all tags for the current user.

    Returns tags with task_count indicating how many tasks use each tag.
    Results are ordered alphabetically by name.
    """
    service = TagService(session, user_id)
    return service.list_tags()


@router.post(
    "",
    response_model=TagPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
)
async def create_tag(
    tag_data: TagCreate,
    session: DbSession,
    user_id: CurrentUserId,
) -> TagPublic:
    """
    Create a new tag for the current user.

    Tag names must be unique per user (case-insensitive).
    """
    service = TagService(session, user_id)
    try:
        tag = service.create_tag(tag_data)
        return TagPublic(
            id=tag.id,
            user_id=tag.user_id,
            name=tag.name,
            color=tag.color,
            created_at=tag.created_at,
            task_count=0,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/suggest",
    response_model=list[str],
    summary="Get tag suggestions",
)
async def suggest_tags(
    session: DbSession,
    user_id: CurrentUserId,
    prefix: str = Query(default="", max_length=50),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[str]:
    """
    Get tag name suggestions for autocomplete.

    Returns tag names matching the prefix, ordered alphabetically.
    """
    service = TagService(session, user_id)
    return service.suggest_tags(prefix, limit)


@router.get(
    "/{tag_id}",
    response_model=TagPublic,
    summary="Get a specific tag",
)
async def get_tag(
    tag_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
) -> TagPublic:
    """
    Get a tag by ID.

    Returns 404 if tag not found or belongs to another user.
    """
    service = TagService(session, user_id)
    tag = service.get_tag(tag_id)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    # Get task count
    tags = service.list_tags()
    tag_data = next((t for t in tags if t.id == tag_id), None)

    return TagPublic(
        id=tag.id,
        user_id=tag.user_id,
        name=tag.name,
        color=tag.color,
        created_at=tag.created_at,
        task_count=tag_data.task_count if tag_data else 0,
    )


@router.patch(
    "/{tag_id}",
    response_model=TagPublic,
    summary="Update a tag",
)
async def update_tag(
    tag_id: UUID,
    tag_data: TagUpdate,
    session: DbSession,
    user_id: CurrentUserId,
) -> TagPublic:
    """
    Partially update a tag.

    Only provided fields are updated.
    Returns 404 if tag not found or belongs to another user.
    Returns 409 if new name already exists.
    """
    service = TagService(session, user_id)
    try:
        tag = service.update_tag(tag_id, tag_data)

        # Get updated task count
        tags = service.list_tags()
        tag_info = next((t for t in tags if t.id == tag_id), None)

        return TagPublic(
            id=tag.id,
            user_id=tag.user_id,
            name=tag.name,
            color=tag.color,
            created_at=tag.created_at,
            task_count=tag_info.task_count if tag_info else 0,
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tag",
)
async def delete_tag(
    tag_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
) -> None:
    """
    Delete a tag by ID.

    Returns 404 if tag not found or belongs to another user.
    Returns 204 No Content on success.

    Note: Task-tag associations are automatically removed.
    """
    service = TagService(session, user_id)
    deleted = service.delete_tag(tag_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )


__all__ = ["router"]
