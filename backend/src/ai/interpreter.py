"""
AI Interpreter for natural language task commands.

This module implements intent extraction using OpenAI function calling.
It converts natural language input into structured InterpretedCommand objects.

Implements:
- FR-002: Interpret NL commands and map to Bonsai CLI operations
- FR-007: Handle ambiguous inputs by asking clarifying questions
- FR-011: 5-second timeout on AI operations
- FR-014: Preserve user intent without adding/modifying unspecified parameters

Architecture (Constitution Principle VII - AI as Interpreter):
    User Message -> Interpreter -> InterpretedCommand -> Executor -> Response
"""

import asyncio
import json
import logging
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI

from src.ai.prompts.intent import (
    INTENT_EXTRACTION_TOOLS,
    build_intent_prompt,
)
from src.ai.types import CommandAction, InterpretedCommand, StatusFilter
from src.config.ai_config import AIConfig, get_ai_config

logger = logging.getLogger(__name__)


class AIInterpreter:
    """
    Natural language interpreter using OpenAI function calling.

    Converts user messages into structured InterpretedCommand objects
    that can be executed by the Executor.
    """

    def __init__(self, config: AIConfig | None = None):
        """
        Initialize the interpreter.

        Args:
            config: AI configuration. If None, loads from environment.
        """
        self.config = config or get_ai_config()
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazy-initialize the OpenAI client."""
        if self._client is None:
            if not self.config.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self._client = AsyncOpenAI(api_key=self.config.openai_api_key)
        return self._client

    async def interpret(
        self,
        user_message: str,
        user_id: UUID,
        conversation_history: list[dict[str, str]] | None = None,
        user_tasks: list[dict[str, Any]] | None = None,
    ) -> InterpretedCommand:
        """
        Interpret a natural language message into a structured command.

        Args:
            user_message: The user's natural language input
            user_id: The user's ID for context
            conversation_history: Previous messages for context
            user_tasks: User's existing tasks for reference matching

        Returns:
            InterpretedCommand with action, confidence, and extracted parameters

        Raises:
            asyncio.TimeoutError: If AI takes longer than configured timeout
        """
        # Build prompt with context
        messages = build_intent_prompt(
            user_message=user_message,
            conversation_history=conversation_history,
            user_tasks=user_tasks,
        )

        try:
            # Call OpenAI with timeout (Constitution Principle X)
            response = await asyncio.wait_for(
                self._call_openai(messages),
                timeout=self.config.ai_timeout_seconds,
            )

            # Parse the function call response
            return self._parse_response(user_message, response, user_tasks)

        except asyncio.TimeoutError:
            logger.warning(f"AI interpretation timed out after {self.config.ai_timeout_seconds}s")
            return self._create_timeout_fallback(user_message)
        except Exception as e:
            logger.error(f"AI interpretation failed: {e}")
            return self._create_error_fallback(user_message, str(e))

    async def _call_openai(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """
        Call OpenAI API with function calling.

        Args:
            messages: The prompt messages

        Returns:
            The function call arguments from the response
        """
        response = await self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=messages,  # type: ignore
            tools=INTENT_EXTRACTION_TOOLS,  # type: ignore
            tool_choice={"type": "function", "function": {"name": "extract_task_intent"}},
            temperature=0.1,  # Low temperature for consistent extraction
        )

        # Extract the function call
        tool_call = response.choices[0].message.tool_calls
        if tool_call and len(tool_call) > 0:
            args_json = tool_call[0].function.arguments
            return json.loads(args_json)

        # No function call - return unknown
        return {"action": "unknown", "confidence": 0.0}

    def _parse_response(
        self,
        original_text: str,
        response: dict[str, Any],
        user_tasks: list[dict[str, Any]] | None = None,
    ) -> InterpretedCommand:
        """
        Parse OpenAI response into InterpretedCommand.

        Args:
            original_text: The original user message
            response: The parsed function call arguments
            user_tasks: User's tasks for reference resolution

        Returns:
            InterpretedCommand instance
        """
        action_str = response.get("action", "unknown")
        try:
            action = CommandAction(action_str)
        except ValueError:
            action = CommandAction.UNKNOWN

        confidence = float(response.get("confidence", 0.0))

        # Extract optional fields
        title = response.get("title")
        task_id = None
        task_reference = response.get("task_reference")

        # Handle task_id - might be integer from AI
        raw_task_id = response.get("task_id")
        if raw_task_id is not None:
            # If it's an integer, we need to resolve it from user tasks
            if isinstance(raw_task_id, int) and user_tasks:
                task_id = self._resolve_task_by_index(raw_task_id, user_tasks)
            elif isinstance(raw_task_id, str):
                try:
                    task_id = UUID(raw_task_id)
                except ValueError:
                    pass

        # Parse due date
        due_date = self._parse_due_date(response.get("due_date"))

        # Parse status filter
        status_filter = None
        if response.get("status_filter"):
            try:
                status_filter = StatusFilter(response.get("status_filter"))
            except ValueError:
                pass

        # Handle clarification
        clarification_needed = None
        if response.get("needs_clarification"):
            clarification_needed = response.get(
                "clarification_question",
                "Could you please provide more details?"
            )

        # Build suggested CLI command
        suggested_cli = self._build_cli_command(action, title, task_id, due_date, status_filter)

        # Handle multiple matches for task references
        multiple_matches: list[UUID] = []
        if task_reference and user_tasks and not task_id:
            matches = self._find_matching_tasks(task_reference, user_tasks)
            if len(matches) > 1:
                multiple_matches = matches
                clarification_needed = f"Multiple tasks match '{task_reference}'. Please specify which one by ID."
            elif len(matches) == 1:
                task_id = matches[0]

        return InterpretedCommand(
            original_text=original_text,
            action=action,
            confidence=confidence,
            suggested_cli=suggested_cli,
            task_id=task_id,
            title=title,
            due_date=due_date,
            status_filter=status_filter,
            clarification_needed=clarification_needed,
            multiple_matches=multiple_matches,
        )

    def _resolve_task_by_index(
        self,
        index: int,
        user_tasks: list[dict[str, Any]],
    ) -> UUID | None:
        """Resolve a task index to UUID."""
        # The AI might use 1-based indexing
        if 1 <= index <= len(user_tasks):
            task = user_tasks[index - 1]
            task_id = task.get("id")
            if task_id:
                return UUID(str(task_id)) if isinstance(task_id, str) else task_id
        return None

    def _find_matching_tasks(
        self,
        reference: str,
        user_tasks: list[dict[str, Any]],
    ) -> list[UUID]:
        """Find tasks matching a text reference."""
        matches = []
        reference_lower = reference.lower()

        for task in user_tasks:
            title = task.get("title", "").lower()
            if reference_lower in title or title in reference_lower:
                task_id = task.get("id")
                if task_id:
                    uuid_val = UUID(str(task_id)) if isinstance(task_id, str) else task_id
                    matches.append(uuid_val)

        return matches

    def _parse_due_date(self, due_str: str | None) -> date | None:
        """Parse natural language due date into date object."""
        if not due_str:
            return None

        due_lower = due_str.lower().strip()
        today = date.today()

        # Handle common natural language dates
        if due_lower in ("today", "now"):
            return today
        elif due_lower == "tomorrow":
            return today + timedelta(days=1)
        elif due_lower == "next week":
            return today + timedelta(weeks=1)
        elif "day" in due_lower:
            # "in 3 days", "3 days"
            try:
                num = int("".join(c for c in due_lower if c.isdigit()))
                return today + timedelta(days=num)
            except ValueError:
                pass

        # Try ISO format
        try:
            return date.fromisoformat(due_str)
        except ValueError:
            pass

        return None

    def _build_cli_command(
        self,
        action: CommandAction,
        title: str | None,
        task_id: UUID | None,
        due_date: date | None,
        status_filter: StatusFilter | None,
    ) -> str:
        """Build the equivalent Bonsai CLI command."""
        if action == CommandAction.ADD:
            cmd = f'bonsai add "{title or "task"}"'
            if due_date:
                cmd += f" --due {due_date.isoformat()}"
            return cmd

        elif action == CommandAction.LIST:
            cmd = "bonsai list"
            if status_filter == StatusFilter.PENDING:
                cmd += " --pending"
            elif status_filter == StatusFilter.COMPLETED:
                cmd += " --completed"
            return cmd

        elif action == CommandAction.COMPLETE:
            if task_id:
                return f"bonsai complete {task_id}"
            return "bonsai complete <task_id>"

        elif action == CommandAction.UPDATE:
            if task_id:
                cmd = f"bonsai update {task_id}"
                if title:
                    cmd += f' --title "{title}"'
                if due_date:
                    cmd += f" --due {due_date.isoformat()}"
                return cmd
            return "bonsai update <task_id> --title <new_title>"

        elif action == CommandAction.DELETE:
            if task_id:
                return f"bonsai delete {task_id}"
            return "bonsai delete <task_id>"

        return "bonsai help"

    def _create_timeout_fallback(self, original_text: str) -> InterpretedCommand:
        """Create fallback command when AI times out."""
        return InterpretedCommand(
            original_text=original_text,
            action=CommandAction.UNKNOWN,
            confidence=0.0,
            suggested_cli="bonsai help",
            clarification_needed="I'm taking too long to process. Please try using a CLI command directly.",
        )

    def _create_error_fallback(self, original_text: str, error: str) -> InterpretedCommand:
        """Create fallback command when AI fails."""
        return InterpretedCommand(
            original_text=original_text,
            action=CommandAction.UNKNOWN,
            confidence=0.0,
            suggested_cli="bonsai help",
            clarification_needed=f"I encountered an error. Please try using a CLI command directly.",
        )


# Singleton instance for dependency injection
_interpreter: AIInterpreter | None = None


def get_interpreter() -> AIInterpreter:
    """Get the singleton interpreter instance."""
    global _interpreter
    if _interpreter is None:
        _interpreter = AIInterpreter()
    return _interpreter


__all__ = ["AIInterpreter", "get_interpreter"]
