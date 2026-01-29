"""
Chat service orchestrating AI interpretation and task execution.

This is the main orchestration layer for Phase 3 AI Chat.
It coordinates:
1. Interpreter: NLP to structured command
2. Executor: Command to task operation
3. Response: Operation result to user message

Implements the conversation flow from spec.md:
1. Receive user message
2. Fetch conversation history from DB
3. Construct message array (history + new message)
4. Store user message in DB
5. Run agent with MCP tools (interpreter + executor)
6. Store assistant response in DB
7. Return response to frontend

Implements:
- FR-002: Interpret NL commands
- FR-004: Execute via Bonsai CLI
- FR-005: Human-readable responses
- FR-006: Persist conversation history
- FR-008: CLI fallback for low confidence
- FR-010: Log AI interpretations with confidence
- FR-021: Automatic language detection (Phase 5 - US6)
- FR-022: Respond in same language as input (Phase 5 - US6)
"""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from src.ai.interpreter import AIInterpreter, get_interpreter
from src.ai.executor import CommandExecutor, ExecutionResult
from src.ai.fallback import FallbackHandler, FallbackResponse, get_fallback_handler
from src.ai.prompts.response import (
    build_add_response,
    build_list_response,
    build_complete_response,
    build_update_response,
    build_delete_response,
    build_fallback_response,
)
from src.ai.types import CommandAction, InterpretedCommand, ConfidenceLevel
from src.ai.urdu import (
    Language,
    get_response as get_urdu_response,
    format_task_list_urdu,
)
from src.config.ai_config import AIConfig, get_ai_config
from src.models.message import Message, MessagePublic
from src.models.task import Task
from src.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """Response from chat service."""

    message: str
    confidence: float
    action: str | None = None
    suggested_cli: str | None = None
    needs_confirmation: bool = False
    is_fallback: bool = False
    task: dict[str, Any] | None = None
    tasks: list[dict[str, Any]] | None = None
    language: str = "en"  # Phase 5 (US6): Response language (en/ur/mixed)


class ChatService:
    """
    Main orchestration service for AI Chat.

    Coordinates interpretation, execution, and response generation.
    """

    def __init__(
        self,
        session: Session,
        user_id: UUID,
        config: AIConfig | None = None,
    ):
        """
        Initialize chat service.

        Args:
            session: Database session
            user_id: Current user's ID
            config: AI configuration (optional)
        """
        self.session = session
        self.user_id = user_id
        self.config = config or get_ai_config()

        self.conversation_service = ConversationService(session, user_id)
        self.interpreter = get_interpreter()
        self.fallback_handler = get_fallback_handler()

    async def process_message(
        self,
        user_message: str,
        conversation_id: UUID | None = None,
    ) -> tuple[ChatResponse, Message]:
        """
        Process a user message and return AI response.

        This is the main entry point for chat operations.

        Args:
            user_message: The user's natural language input
            conversation_id: Optional existing conversation ID

        Returns:
            Tuple of (ChatResponse, assistant Message entity)
        """
        # Step 1: Get or create conversation
        conversation = self.conversation_service.get_or_create_conversation(conversation_id)
        conv_id = conversation.id

        # Step 2: Store user message
        self.conversation_service.add_user_message(conv_id, user_message)

        # Step 3: Check for direct CLI command
        if self._is_cli_command(user_message):
            response = self._handle_cli_bypass(user_message)
            message = self._store_response(conv_id, response)
            return response, message

        # Step 4: Check if AI is available
        if not self.config.has_ai_provider:
            response = self._handle_ai_unavailable()
            message = self._store_response(conv_id, response)
            return response, message

        # Step 5: Get conversation history for context
        history = self.conversation_service.get_conversation_history_for_ai(
            conv_id,
            max_messages=self.config.max_conversation_context,
        )

        # Step 6: Get user's tasks for reference
        user_tasks = self._get_user_tasks_for_context()

        # Step 7: Interpret the message
        interpreted = await self.interpreter.interpret(
            user_message=user_message,
            user_id=self.user_id,
            conversation_history=history[:-1],  # Exclude the message we just added
            user_tasks=user_tasks,
        )

        logger.info(
            f"Interpreted: action={interpreted.action.value}, "
            f"confidence={interpreted.confidence:.2f}, "
            f"cli={interpreted.suggested_cli}"
        )

        # Step 8: Handle based on confidence
        if self.fallback_handler.should_fallback(interpreted):
            response = self._handle_fallback(interpreted)
        elif self.fallback_handler.should_confirm(interpreted):
            response = self._handle_confirmation(interpreted)
        else:
            response = await self._execute_and_respond(interpreted)

        # Step 9: Store assistant response
        message = self._store_response(
            conv_id,
            response,
            interpreted.suggested_cli,
            interpreted.confidence,
        )

        # Step 10: Auto-title conversation if first message
        self.conversation_service.auto_title_conversation(conv_id)

        return response, message

    async def confirm_action(
        self,
        conversation_id: UUID,
        confirmed: bool,
    ) -> tuple[ChatResponse, Message]:
        """
        Handle user confirmation of a pending action.

        Args:
            conversation_id: Conversation with pending action
            confirmed: Whether user confirmed

        Returns:
            Tuple of (ChatResponse, Message)
        """
        if not confirmed:
            response = ChatResponse(
                message="Okay, I won't do that. What would you like to do instead?",
                confidence=1.0,
                action=None,
            )
            message = self._store_response(conversation_id, response)
            return response, message

        # Get the last user message to re-interpret and execute
        messages = self.conversation_service.get_conversation_messages(
            conversation_id,
            limit=5,
        )

        # Find the last user message
        last_user_msg = None
        for msg in reversed(messages):
            if msg.role.value == "user":
                last_user_msg = msg.content
                break

        if not last_user_msg:
            response = ChatResponse(
                message="I couldn't find what to confirm. Please try again.",
                confidence=1.0,
            )
            message = self._store_response(conversation_id, response)
            return response, message

        # Re-interpret and force execute
        user_tasks = self._get_user_tasks_for_context()
        interpreted = await self.interpreter.interpret(
            user_message=last_user_msg,
            user_id=self.user_id,
            user_tasks=user_tasks,
        )

        # Force execute regardless of confidence
        response = await self._execute_and_respond(interpreted)
        message = self._store_response(
            conversation_id,
            response,
            interpreted.suggested_cli,
            interpreted.confidence,
        )

        return response, message

    async def _execute_and_respond(
        self,
        interpreted: InterpretedCommand,
    ) -> ChatResponse:
        """Execute command and generate response."""
        executor = CommandExecutor(self.session, self.user_id)
        result = executor.execute(interpreted)

        return self._build_response(interpreted, result)

    def _build_response(
        self,
        interpreted: InterpretedCommand,
        result: ExecutionResult,
    ) -> ChatResponse:
        """Build ChatResponse from execution result."""
        # Phase 5 (US6): Determine response language
        lang = interpreted.detected_language or Language.ENGLISH
        lang_str = lang.value if hasattr(lang, 'value') else "en"
        use_urdu = lang == Language.URDU

        if not result.success:
            error_msg = result.error_message or "Something went wrong."
            if use_urdu:
                error_msg = get_urdu_response("error_occurred", Language.URDU)
            return ChatResponse(
                message=error_msg,
                confidence=interpreted.confidence,
                action=interpreted.action.value,
                suggested_cli=interpreted.suggested_cli,
                is_fallback=True,
                language=lang_str,
            )

        # Build action-specific response
        if result.action == CommandAction.ADD:
            title = result.task.get("title") if result.task else None
            if use_urdu:
                message = get_urdu_response("task_created", Language.URDU, title=title or "")
            else:
                message = build_add_response(success=True, title=title)
            return ChatResponse(
                message=message,
                confidence=interpreted.confidence,
                action=interpreted.action.value,
                task=result.task,
                language=lang_str,
            )

        elif result.action == CommandAction.LIST:
            if use_urdu and result.tasks:
                message = format_task_list_urdu(result.tasks)
            else:
                message = build_list_response(
                    success=True,
                    tasks=result.tasks,
                    status_filter=interpreted.status_filter.value if interpreted.status_filter else None,
                )
            return ChatResponse(
                message=message,
                confidence=interpreted.confidence,
                action=interpreted.action.value,
                tasks=result.tasks,
                language=lang_str,
            )

        elif result.action == CommandAction.COMPLETE:
            already_done = result.data.get("already_completed") if result.data else False
            title = result.task.get("title") if result.task else None
            if already_done:
                message = f"Task \"{title}\" was already completed."
                if use_urdu:
                    message = f"یہ کام پہلے سے مکمل ہے: {title}"
            else:
                if use_urdu:
                    message = get_urdu_response("task_completed", Language.URDU, title=title or "")
                else:
                    message = build_complete_response(success=True, title=title)
            return ChatResponse(
                message=message,
                confidence=interpreted.confidence,
                action=interpreted.action.value,
                task=result.task,
                language=lang_str,
            )

        elif result.action == CommandAction.UPDATE:
            old_title = result.data.get("old_title") if result.data else None
            new_title = result.task.get("title") if result.task else None
            if use_urdu:
                message = get_urdu_response("task_updated", Language.URDU, title=new_title or "")
            else:
                message = build_update_response(
                    success=True,
                    old_title=old_title,
                    new_title=new_title,
                )
            return ChatResponse(
                message=message,
                confidence=interpreted.confidence,
                action=interpreted.action.value,
                task=result.task,
                language=lang_str,
            )

        elif result.action == CommandAction.DELETE:
            title = result.task.get("title") if result.task else None
            if use_urdu:
                message = get_urdu_response("task_deleted", Language.URDU)
            else:
                message = build_delete_response(success=True, title=title)
            return ChatResponse(
                message=message,
                confidence=interpreted.confidence,
                action=interpreted.action.value,
                task=result.task,
                language=lang_str,
            )

        # Default
        default_msg = "ہو گیا!" if use_urdu else "Done!"
        return ChatResponse(
            message=default_msg,
            confidence=interpreted.confidence,
            action=interpreted.action.value,
            language=lang_str,
        )

    def _handle_fallback(self, interpreted: InterpretedCommand) -> ChatResponse:
        """Handle fallback scenario."""
        lang = interpreted.detected_language or Language.ENGLISH
        lang_str = lang.value if hasattr(lang, 'value') else "en"

        fallback = self.fallback_handler.create_fallback(interpreted)

        return ChatResponse(
            message=fallback.message,
            confidence=interpreted.confidence,
            action=interpreted.action.value if interpreted.action != CommandAction.UNKNOWN else None,
            suggested_cli=fallback.suggested_cli,
            is_fallback=True,
            language=lang_str,
        )

    def _handle_confirmation(self, interpreted: InterpretedCommand) -> ChatResponse:
        """Handle confirmation request."""
        lang = interpreted.detected_language or Language.ENGLISH
        lang_str = lang.value if hasattr(lang, 'value') else "en"
        use_urdu = lang == Language.URDU

        confirmation = self.fallback_handler.create_confirmation(interpreted)

        # Use Urdu confirmation message if detected
        message = confirmation.message
        if use_urdu:
            action_name = interpreted.action.value if interpreted.action else "عمل"
            message = get_urdu_response("confirmation_needed", Language.URDU, action=action_name)

        return ChatResponse(
            message=message,
            confidence=interpreted.confidence,
            action=interpreted.action.value,
            suggested_cli=confirmation.suggested_cli,
            needs_confirmation=True,
            language=lang_str,
        )

    def _handle_ai_unavailable(self) -> ChatResponse:
        """Handle AI service unavailable."""
        fallback = self.fallback_handler.create_ai_unavailable()

        return ChatResponse(
            message=fallback.message,
            confidence=0.0,
            suggested_cli=fallback.suggested_cli,
            is_fallback=True,
        )

    def _handle_cli_bypass(self, user_message: str) -> ChatResponse:
        """Handle direct CLI command."""
        return ChatResponse(
            message=(
                "I see you've entered a CLI command. "
                "Please use the terminal to run Bonsai CLI commands directly, "
                "or describe what you'd like to do in natural language."
            ),
            confidence=1.0,
            suggested_cli=user_message,
            is_fallback=True,
        )

    def _is_cli_command(self, message: str) -> bool:
        """Check if message is a direct CLI command."""
        message_lower = message.lower().strip()
        return (
            message_lower.startswith("bonsai ")
            or message_lower.startswith("/cli")
            or message_lower == "/cli"
        )

    def _get_user_tasks_for_context(self) -> list[dict[str, Any]]:
        """Get user's tasks for AI context."""
        tasks = self.session.exec(
            select(Task)
            .where(Task.user_id == self.user_id)
            .order_by(Task.created_at.desc())  # type: ignore
            .limit(20)
        ).all()

        return [
            {
                "id": str(task.id),
                "title": task.title,
                "is_completed": task.is_completed,
            }
            for task in tasks
        ]

    def _store_response(
        self,
        conversation_id: UUID,
        response: ChatResponse,
        cli_command: str | None = None,
        confidence: float | None = None,
    ) -> Message:
        """Store assistant response as message."""
        return self.conversation_service.add_assistant_message(
            conversation_id=conversation_id,
            content=response.message,
            generated_command=cli_command or response.suggested_cli,
            confidence_score=confidence or response.confidence,
        )


__all__ = ["ChatService", "ChatResponse"]
