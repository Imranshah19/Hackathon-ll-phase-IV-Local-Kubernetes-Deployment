"""
Conversations API routes for Phase 3 AI Chat.

Endpoints:
- GET /api/conversations - List user's conversations
- POST /api/conversations - Create a new conversation
- GET /api/conversations/{id} - Get conversation with messages
- DELETE /api/conversations/{id} - Delete a conversation
- PATCH /api/conversations/{id} - Update conversation title

All endpoints enforce user isolation - users can only access their own conversations.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.dependencies import CurrentUserId, DbSession
from src.models.conversation import ConversationCreate, ConversationPublic, ConversationList
from src.models.message import MessagePublic
from src.services.conversation_service import ConversationService

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================


class ConversationDetail(BaseModel):
    """Conversation with messages."""

    id: UUID
    user_id: UUID
    title: str | None
    created_at: str
    updated_at: str
    messages: list[MessagePublic]


class ConversationUpdateRequest(BaseModel):
    """Request body for updating conversation."""

    title: str = Field(min_length=1, max_length=100, description="New conversation title")


# =============================================================================
# Routes
# =============================================================================


@router.get(
    "",
    response_model=ConversationList,
    summary="List conversations",
)
async def list_conversations(
    session: DbSession,
    user_id: CurrentUserId,
    limit: int = 50,
    offset: int = 0,
) -> ConversationList:
    """
    List all conversations for the current user.

    Results are ordered by last activity (most recent first).
    Supports pagination with limit and offset parameters.
    """
    service = ConversationService(session, user_id)
    conversations, total = service.list_conversations(limit=limit, offset=offset)

    return ConversationList(
        conversations=[ConversationPublic.model_validate(c) for c in conversations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ConversationPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
)
async def create_conversation(
    data: ConversationCreate,
    session: DbSession,
    user_id: CurrentUserId,
) -> ConversationPublic:
    """
    Create a new conversation.

    The conversation is associated with the current user.
    Title is optional and can be auto-generated later.
    """
    service = ConversationService(session, user_id)
    conversation = service.create_conversation(title=data.title)
    return ConversationPublic.model_validate(conversation)


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get conversation with messages",
)
async def get_conversation(
    conversation_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
) -> ConversationDetail:
    """
    Get a conversation with its messages.

    Returns 404 if conversation not found or belongs to another user.
    Messages are ordered chronologically (oldest first).
    """
    service = ConversationService(session, user_id)
    conversation = service.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = service.get_conversation_messages(conversation_id)

    return ConversationDetail(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at.isoformat() if conversation.created_at else "",
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
        messages=[MessagePublic.model_validate(m) for m in messages],
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationPublic,
    summary="Update conversation",
)
async def update_conversation(
    conversation_id: UUID,
    data: ConversationUpdateRequest,
    session: DbSession,
    user_id: CurrentUserId,
) -> ConversationPublic:
    """
    Update a conversation's title.

    Returns 404 if conversation not found or belongs to another user.
    """
    service = ConversationService(session, user_id)
    conversation = service.update_conversation_title(conversation_id, data.title)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return ConversationPublic.model_validate(conversation)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
)
async def delete_conversation(
    conversation_id: UUID,
    session: DbSession,
    user_id: CurrentUserId,
) -> None:
    """
    Delete a conversation and all its messages.

    Returns 404 if conversation not found or belongs to another user.
    Returns 204 No Content on success.
    """
    service = ConversationService(session, user_id)
    deleted = service.delete_conversation(conversation_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )


__all__ = ["router"]
