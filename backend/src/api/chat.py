"""
Chat API routes for Phase 3 AI Chat.

Endpoints:
- POST /api/chat/message - Send a chat message and get AI response
- POST /api/chat/confirm - Confirm a pending action

All endpoints require authentication.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.dependencies import CurrentUserId, DbSession
from src.models.message import MessagePublic
from src.services.chat_service import ChatService

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================


class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message."""

    message: str = Field(
        min_length=1,
        max_length=2000,
        description="The user's natural language message",
    )
    conversation_id: UUID | None = Field(
        default=None,
        description="Optional existing conversation ID to continue",
    )


class ChatMessageResponse(BaseModel):
    """Response from chat message endpoint."""

    message: str = Field(description="The assistant's response text")
    confidence: float = Field(description="AI interpretation confidence (0.0-1.0)")
    action: str | None = Field(default=None, description="The interpreted action (add, list, etc.)")
    suggested_cli: str | None = Field(default=None, description="Equivalent CLI command")
    needs_confirmation: bool = Field(default=False, description="Whether user confirmation is needed")
    is_fallback: bool = Field(default=False, description="Whether this is a fallback response")
    conversation_id: UUID = Field(description="The conversation ID (new or existing)")
    message_id: UUID = Field(description="The assistant message ID")
    task: dict[str, Any] | None = Field(default=None, description="Task data if action affected a task")
    tasks: list[dict[str, Any]] | None = Field(default=None, description="Task list if action was list")
    language: str = Field(default="en", description="Detected/response language (en, ur, mixed) - Phase 5 US6")


class ConfirmActionRequest(BaseModel):
    """Request body for confirming a pending action."""

    conversation_id: UUID = Field(description="Conversation with pending action")
    confirmed: bool = Field(description="Whether user confirms the action")


# =============================================================================
# Routes
# =============================================================================


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    summary="Send a chat message",
    description=(
        "Send a natural language message to the AI chat assistant. "
        "The assistant will interpret the message, execute the appropriate task operation, "
        "and return a human-readable response."
    ),
)
async def send_message(
    request: ChatMessageRequest,
    session: DbSession,
    user_id: CurrentUserId,
) -> ChatMessageResponse:
    """
    Process a user chat message and return AI response.

    The message is interpreted using AI, executed via the task service,
    and the response is stored in the conversation history.

    Returns conversation_id which should be used for subsequent messages
    in the same conversation.
    """
    chat_service = ChatService(session, user_id)

    try:
        response, message = await chat_service.process_message(
            user_message=request.message,
            conversation_id=request.conversation_id,
        )

        return ChatMessageResponse(
            message=response.message,
            confidence=response.confidence,
            action=response.action,
            suggested_cli=response.suggested_cli,
            needs_confirmation=response.needs_confirmation,
            is_fallback=response.is_fallback,
            conversation_id=message.conversation_id,
            message_id=message.id,
            task=response.task,
            tasks=response.tasks,
            language=response.language,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Log the error but return a user-friendly message
        import logging
        logging.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your message. Please try again.",
        )


@router.post(
    "/confirm",
    response_model=ChatMessageResponse,
    summary="Confirm a pending action",
    description=(
        "Confirm or reject a pending action that required user confirmation. "
        "Used when the AI interpretation had medium confidence or for destructive actions."
    ),
)
async def confirm_action(
    request: ConfirmActionRequest,
    session: DbSession,
    user_id: CurrentUserId,
) -> ChatMessageResponse:
    """
    Handle user confirmation of a pending action.

    If confirmed, the action is executed. If rejected, the user is
    prompted for what they'd like to do instead.
    """
    chat_service = ChatService(session, user_id)

    try:
        response, message = await chat_service.confirm_action(
            conversation_id=request.conversation_id,
            confirmed=request.confirmed,
        )

        return ChatMessageResponse(
            message=response.message,
            confidence=response.confidence,
            action=response.action,
            suggested_cli=response.suggested_cli,
            needs_confirmation=response.needs_confirmation,
            is_fallback=response.is_fallback,
            conversation_id=message.conversation_id,
            message_id=message.id,
            task=response.task,
            tasks=response.tasks,
            language=response.language,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


__all__ = ["router"]
