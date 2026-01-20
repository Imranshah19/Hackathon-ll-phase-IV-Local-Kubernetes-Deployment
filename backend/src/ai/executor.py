"""
Executor bridge between AI interpretation and Bonsai CLI operations.

This module executes interpreted commands through the existing task service,
maintaining Constitution Principle VII (AI as Interpreter, Not Executor).

The executor:
1. Receives InterpretedCommand from the interpreter
2. Calls the appropriate task service method
3. Returns execution results for response generation

Implements:
- FR-004: Execute validated commands through existing Bonsai CLI (task service)
- FR-013: User data isolation enforced at service layer
"""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlmodel import Session

from src.ai.types import CommandAction, InterpretedCommand, StatusFilter
from src.models.base import utc_now
from src.models.task import Task, TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of command execution."""

    success: bool
    action: CommandAction
    data: dict[str, Any] | None = None
    error_message: str | None = None
    task: dict[str, Any] | None = None
    tasks: list[dict[str, Any]] | None = None


class CommandExecutor:
    """
    Executes interpreted commands via the task service layer.

    This is the bridge between AI interpretation and actual task operations.
    All operations respect user isolation.
    """

    def __init__(self, session: Session, user_id: UUID):
        """
        Initialize executor with session and user context.

        Args:
            session: Database session
            user_id: Current user's ID for isolation
        """
        self.session = session
        self.user_id = user_id

    def execute(self, command: InterpretedCommand) -> ExecutionResult:
        """
        Execute an interpreted command.

        Args:
            command: The interpreted command to execute

        Returns:
            ExecutionResult with success status and relevant data
        """
        if command.needs_clarification:
            return ExecutionResult(
                success=False,
                action=command.action,
                error_message=command.clarification_needed,
            )

        if command.action == CommandAction.ADD:
            return self._execute_add(command)
        elif command.action == CommandAction.LIST:
            return self._execute_list(command)
        elif command.action == CommandAction.COMPLETE:
            return self._execute_complete(command)
        elif command.action == CommandAction.UPDATE:
            return self._execute_update(command)
        elif command.action == CommandAction.DELETE:
            return self._execute_delete(command)
        else:
            return ExecutionResult(
                success=False,
                action=command.action,
                error_message="Unknown action. Please try rephrasing your request.",
            )

    def _execute_add(self, command: InterpretedCommand) -> ExecutionResult:
        """Execute ADD action - create a new task."""
        if not command.title:
            return ExecutionResult(
                success=False,
                action=CommandAction.ADD,
                error_message="Please specify a title for the task.",
            )

        try:
            task = Task(
                title=command.title,
                description=None,
                is_completed=False,
                user_id=self.user_id,
            )

            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)

            return ExecutionResult(
                success=True,
                action=CommandAction.ADD,
                task=self._task_to_dict(task),
            )
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            self.session.rollback()
            return ExecutionResult(
                success=False,
                action=CommandAction.ADD,
                error_message="Failed to create task. Please try again.",
            )

    def _execute_list(self, command: InterpretedCommand) -> ExecutionResult:
        """Execute LIST action - retrieve user's tasks."""
        try:
            from sqlmodel import select

            query = select(Task).where(Task.user_id == self.user_id)

            # Apply status filter
            if command.status_filter == StatusFilter.PENDING:
                query = query.where(Task.is_completed == False)  # noqa: E712
            elif command.status_filter == StatusFilter.COMPLETED:
                query = query.where(Task.is_completed == True)  # noqa: E712

            # Order by creation date
            query = query.order_by(Task.created_at.desc())  # type: ignore

            tasks = self.session.exec(query).all()

            return ExecutionResult(
                success=True,
                action=CommandAction.LIST,
                tasks=[self._task_to_dict(t) for t in tasks],
            )
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return ExecutionResult(
                success=False,
                action=CommandAction.LIST,
                error_message="Failed to retrieve tasks. Please try again.",
            )

    def _execute_complete(self, command: InterpretedCommand) -> ExecutionResult:
        """Execute COMPLETE action - mark a task as done."""
        task = self._get_task(command.task_id)
        if not task:
            return ExecutionResult(
                success=False,
                action=CommandAction.COMPLETE,
                error_message="Task not found. Please check the task ID.",
            )

        if task.is_completed:
            return ExecutionResult(
                success=True,
                action=CommandAction.COMPLETE,
                task=self._task_to_dict(task),
                data={"already_completed": True},
            )

        try:
            task.is_completed = True
            task.updated_at = utc_now()

            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)

            return ExecutionResult(
                success=True,
                action=CommandAction.COMPLETE,
                task=self._task_to_dict(task),
            )
        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            self.session.rollback()
            return ExecutionResult(
                success=False,
                action=CommandAction.COMPLETE,
                error_message="Failed to complete task. Please try again.",
            )

    def _execute_update(self, command: InterpretedCommand) -> ExecutionResult:
        """Execute UPDATE action - modify a task."""
        task = self._get_task(command.task_id)
        if not task:
            return ExecutionResult(
                success=False,
                action=CommandAction.UPDATE,
                error_message="Task not found. Please check the task ID.",
            )

        # Check if there's anything to update
        if not command.title and not command.due_date:
            return ExecutionResult(
                success=False,
                action=CommandAction.UPDATE,
                error_message="Please specify what to update (title or due date).",
            )

        try:
            old_title = task.title

            if command.title:
                task.title = command.title

            task.updated_at = utc_now()

            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)

            return ExecutionResult(
                success=True,
                action=CommandAction.UPDATE,
                task=self._task_to_dict(task),
                data={"old_title": old_title},
            )
        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            self.session.rollback()
            return ExecutionResult(
                success=False,
                action=CommandAction.UPDATE,
                error_message="Failed to update task. Please try again.",
            )

    def _execute_delete(self, command: InterpretedCommand) -> ExecutionResult:
        """Execute DELETE action - remove a task."""
        task = self._get_task(command.task_id)
        if not task:
            return ExecutionResult(
                success=False,
                action=CommandAction.DELETE,
                error_message="Task not found. Please check the task ID.",
            )

        try:
            task_dict = self._task_to_dict(task)

            self.session.delete(task)
            self.session.commit()

            return ExecutionResult(
                success=True,
                action=CommandAction.DELETE,
                task=task_dict,
            )
        except Exception as e:
            logger.error(f"Failed to delete task: {e}")
            self.session.rollback()
            return ExecutionResult(
                success=False,
                action=CommandAction.DELETE,
                error_message="Failed to delete task. Please try again.",
            )

    def _get_task(self, task_id: UUID | None) -> Task | None:
        """Get a task by ID, ensuring user ownership."""
        if not task_id:
            return None

        from sqlmodel import select

        task = self.session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == self.user_id)
        ).first()

        return task

    def _task_to_dict(self, task: Task) -> dict[str, Any]:
        """Convert task to dictionary for response generation."""
        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "is_completed": task.is_completed,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }


__all__ = ["CommandExecutor", "ExecutionResult"]
