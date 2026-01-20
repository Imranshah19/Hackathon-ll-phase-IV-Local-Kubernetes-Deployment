"""
Conversation service for Phase 3 AI Chat.

Provides CRUD operations for conversations and messages.
Implements user data isolation per FR-013.

Operations:
- Create conversation
- Get conversation with messages
- List user's conversations
- Add message to conversation
- Delete conversation
"""

import logging
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from src.models.base import utc_now
from src.models.conversation import Conversation, ConversationCreate, ConversationPublic
from src.models.message import Message, MessageRole, MessagePublic

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Service for conversation and message operations.

    All operations enforce user isolation - users can only
    access their own conversations and messages.
    """

    def __init__(self, session: Session, user_id: UUID):
        """
        Initialize service with session and user context.

        Args:
            session: Database session
            user_id: Current user's ID for isolation
        """
        self.session = session
        self.user_id = user_id

    # =========================================================================
    # Conversation Operations
    # =========================================================================

    def create_conversation(self, title: str | None = None) -> Conversation:
        """
        Create a new conversation.

        Args:
            title: Optional title for the conversation

        Returns:
            Created Conversation entity
        """
        conversation = Conversation(
            user_id=self.user_id,
            title=title,
        )

        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)

        logger.info(f"Created conversation {conversation.id} for user {self.user_id}")
        return conversation

    def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        """
        Get a conversation by ID.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Conversation if found and owned by user, else None
        """
        conversation = self.session.exec(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == self.user_id,
            )
        ).first()

        return conversation

    def get_or_create_conversation(self, conversation_id: UUID | None = None) -> Conversation:
        """
        Get existing conversation or create a new one.

        Args:
            conversation_id: Optional existing conversation ID

        Returns:
            Conversation entity
        """
        if conversation_id:
            conversation = self.get_conversation(conversation_id)
            if conversation:
                return conversation

        return self.create_conversation()

    def list_conversations(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        """
        List user's conversations.

        Args:
            limit: Maximum conversations to return
            offset: Number of conversations to skip

        Returns:
            Tuple of (conversations list, total count)
        """
        # Get total count
        count_query = select(Conversation).where(Conversation.user_id == self.user_id)
        total = len(self.session.exec(count_query).all())

        # Get paginated results
        query = (
            select(Conversation)
            .where(Conversation.user_id == self.user_id)
            .order_by(Conversation.updated_at.desc())  # type: ignore
            .offset(offset)
            .limit(limit)
        )

        conversations = list(self.session.exec(query).all())
        return conversations, total

    def delete_conversation(self, conversation_id: UUID) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Conversation to delete

        Returns:
            True if deleted, False if not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False

        self.session.delete(conversation)
        self.session.commit()

        logger.info(f"Deleted conversation {conversation_id}")
        return True

    # =========================================================================
    # Message Operations
    # =========================================================================

    def add_user_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        """
        Add a user message to a conversation.

        Args:
            conversation_id: Target conversation
            content: Message content

        Returns:
            Created Message entity
        """
        message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )

        self.session.add(message)

        # Update conversation timestamp
        self._update_conversation_timestamp(conversation_id)

        self.session.commit()
        self.session.refresh(message)

        return message

    def add_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
        generated_command: str | None = None,
        confidence_score: float | None = None,
    ) -> Message:
        """
        Add an assistant message to a conversation.

        Args:
            conversation_id: Target conversation
            content: Message content
            generated_command: The Bonsai CLI command that was executed
            confidence_score: AI interpretation confidence

        Returns:
            Created Message entity
        """
        message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            generated_command=generated_command,
            confidence_score=confidence_score,
        )

        self.session.add(message)

        # Update conversation timestamp
        self._update_conversation_timestamp(conversation_id)

        self.session.commit()
        self.session.refresh(message)

        return message

    def get_conversation_messages(
        self,
        conversation_id: UUID,
        limit: int | None = None,
    ) -> list[Message]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation to get messages for
            limit: Maximum messages to return (newest first)

        Returns:
            List of messages ordered by timestamp (oldest first for display)
        """
        # Verify user owns conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []

        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.asc())  # type: ignore
        )

        if limit:
            # Get last N messages
            all_messages = list(self.session.exec(query).all())
            return all_messages[-limit:] if len(all_messages) > limit else all_messages

        return list(self.session.exec(query).all())

    def get_conversation_history_for_ai(
        self,
        conversation_id: UUID,
        max_messages: int = 10,
    ) -> list[dict[str, str]]:
        """
        Get conversation history in format suitable for AI context.

        Args:
            conversation_id: Conversation ID
            max_messages: Maximum messages to include

        Returns:
            List of {role, content} dicts for OpenAI API
        """
        messages = self.get_conversation_messages(conversation_id, limit=max_messages)

        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

    def _update_conversation_timestamp(self, conversation_id: UUID) -> None:
        """Update conversation's updated_at timestamp."""
        conversation = self.session.exec(
            select(Conversation).where(Conversation.id == conversation_id)
        ).first()

        if conversation:
            conversation.updated_at = utc_now()
            self.session.add(conversation)

    def update_conversation_title(
        self,
        conversation_id: UUID,
        title: str,
    ) -> Conversation | None:
        """
        Update conversation title.

        Args:
            conversation_id: Conversation to update
            title: New title

        Returns:
            Updated conversation or None if not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        conversation.title = title
        conversation.updated_at = utc_now()

        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)

        return conversation

    def auto_title_conversation(self, conversation_id: UUID) -> Conversation | None:
        """
        Auto-generate conversation title from first user message.

        Args:
            conversation_id: Conversation to title

        Returns:
            Updated conversation or None
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation or conversation.title:
            return conversation

        # Get first user message
        first_message = self.session.exec(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.role == MessageRole.USER,
            )
            .order_by(Message.timestamp.asc())  # type: ignore
            .limit(1)
        ).first()

        if first_message:
            # Truncate to 100 chars for title
            title = first_message.content[:97] + "..." if len(first_message.content) > 100 else first_message.content
            return self.update_conversation_title(conversation_id, title)

        return conversation


__all__ = ["ConversationService"]
