"""
Response generation prompts for AI Chat.

This module contains templates for generating human-readable responses
after executing task operations.

Implements FR-005: Return human-readable responses confirming actions or explaining errors
"""

from typing import Any

from src.ai.types import CommandAction

# =============================================================================
# Response Templates
# =============================================================================

RESPONSE_TEMPLATES: dict[CommandAction, dict[str, str]] = {
    CommandAction.ADD: {
        "success": "I've created a new task: \"{title}\"{due_suffix}",
        "success_with_due": " (due {due_date})",
        "error": "I couldn't create the task. {error_message}",
        "clarification": "I'd like to create a task for you, but I need a bit more information. {question}",
    },
    CommandAction.LIST: {
        "success_with_tasks": "Here are your {filter_desc} tasks:\n{task_list}",
        "success_no_tasks": "You don't have any {filter_desc} tasks right now.",
        "error": "I couldn't retrieve your tasks. {error_message}",
    },
    CommandAction.COMPLETE: {
        "success": "Done! I've marked \"{title}\" as complete.",
        "error": "I couldn't complete that task. {error_message}",
        "not_found": "I couldn't find a task matching \"{reference}\". Try using the task ID instead.",
        "multiple_matches": "I found multiple tasks that might match. Which one did you mean?\n{task_list}",
    },
    CommandAction.UPDATE: {
        "success": "I've updated \"{old_title}\" to \"{new_title}\".",
        "success_due": "I've updated the due date for \"{title}\" to {due_date}.",
        "error": "I couldn't update that task. {error_message}",
        "not_found": "I couldn't find a task matching \"{reference}\". Try using the task ID instead.",
        "clarification": "What would you like to update about this task? (title, due date, etc.)",
    },
    CommandAction.DELETE: {
        "success": "I've deleted the task: \"{title}\"",
        "confirm": "Are you sure you want to delete \"{title}\"? This can't be undone.",
        "error": "I couldn't delete that task. {error_message}",
        "not_found": "I couldn't find a task matching \"{reference}\". Try using the task ID instead.",
        "multiple_matches": "I found multiple tasks that might match. Which one did you mean?\n{task_list}",
    },
    CommandAction.UNKNOWN: {
        "fallback": "I'm not sure what you'd like to do. Here are some things I can help with:\n"
        "- \"Add a task to buy groceries\"\n"
        "- \"Show my pending tasks\"\n"
        "- \"Mark task 3 as done\"\n"
        "- \"Delete the meeting task\"\n\n"
        "Or you can use a CLI command directly: {suggested_cli}",
        "low_confidence": "I think you want to {interpreted_action}, but I'm not certain. "
        "You can also use this command directly:\n`{suggested_cli}`",
    },
}


# =============================================================================
# Response Builders
# =============================================================================


def format_task_list(tasks: list[dict[str, Any]], show_status: bool = True) -> str:
    """
    Format a list of tasks for display in chat.

    Args:
        tasks: List of task dictionaries
        show_status: Whether to show completion status

    Returns:
        Formatted string with task list
    """
    if not tasks:
        return ""

    lines = []
    for task in tasks:
        task_id = str(task.get("id", ""))[:8]  # Short UUID
        title = task.get("title", "Untitled")
        status = ""
        if show_status:
            status = " [done]" if task.get("is_completed") else ""

        due = task.get("due")
        due_str = f" (due {due})" if due else ""

        lines.append(f"• {title}{status}{due_str} (ID: {task_id})")

    return "\n".join(lines)


def format_filter_description(status_filter: str | None) -> str:
    """Get human-readable description for a status filter."""
    if status_filter == "pending":
        return "pending"
    elif status_filter == "completed":
        return "completed"
    return ""  # "all" or None


def build_add_response(
    success: bool,
    title: str | None = None,
    due_date: str | None = None,
    error_message: str | None = None,
    clarification_question: str | None = None,
) -> str:
    """Build response for ADD action."""
    templates = RESPONSE_TEMPLATES[CommandAction.ADD]

    if clarification_question:
        return templates["clarification"].format(question=clarification_question)

    if success and title:
        due_suffix = templates["success_with_due"].format(due_date=due_date) if due_date else ""
        return templates["success"].format(title=title, due_suffix=due_suffix)

    return templates["error"].format(error_message=error_message or "Unknown error")


def build_list_response(
    success: bool,
    tasks: list[dict[str, Any]] | None = None,
    status_filter: str | None = None,
    error_message: str | None = None,
) -> str:
    """Build response for LIST action."""
    templates = RESPONSE_TEMPLATES[CommandAction.LIST]
    filter_desc = format_filter_description(status_filter)

    if not success:
        return templates["error"].format(error_message=error_message or "Unknown error")

    if not tasks:
        return templates["success_no_tasks"].format(filter_desc=filter_desc)

    task_list = format_task_list(tasks, show_status=(status_filter != "pending"))
    return templates["success_with_tasks"].format(filter_desc=filter_desc, task_list=task_list)


def build_complete_response(
    success: bool,
    title: str | None = None,
    reference: str | None = None,
    error_message: str | None = None,
    multiple_matches: list[dict[str, Any]] | None = None,
) -> str:
    """Build response for COMPLETE action."""
    templates = RESPONSE_TEMPLATES[CommandAction.COMPLETE]

    if multiple_matches:
        task_list = format_task_list(multiple_matches, show_status=False)
        return templates["multiple_matches"].format(task_list=task_list)

    if success and title:
        return templates["success"].format(title=title)

    if error_message and "not found" in error_message.lower():
        return templates["not_found"].format(reference=reference or "that task")

    return templates["error"].format(error_message=error_message or "Unknown error")


def build_update_response(
    success: bool,
    old_title: str | None = None,
    new_title: str | None = None,
    due_date: str | None = None,
    reference: str | None = None,
    error_message: str | None = None,
    needs_field_clarification: bool = False,
) -> str:
    """Build response for UPDATE action."""
    templates = RESPONSE_TEMPLATES[CommandAction.UPDATE]

    if needs_field_clarification:
        return templates["clarification"]

    if success:
        if new_title and old_title:
            return templates["success"].format(old_title=old_title, new_title=new_title)
        if due_date and old_title:
            return templates["success_due"].format(title=old_title, due_date=due_date)

    if error_message and "not found" in error_message.lower():
        return templates["not_found"].format(reference=reference or "that task")

    return templates["error"].format(error_message=error_message or "Unknown error")


def build_delete_response(
    success: bool,
    title: str | None = None,
    reference: str | None = None,
    error_message: str | None = None,
    needs_confirmation: bool = False,
    multiple_matches: list[dict[str, Any]] | None = None,
) -> str:
    """Build response for DELETE action."""
    templates = RESPONSE_TEMPLATES[CommandAction.DELETE]

    if multiple_matches:
        task_list = format_task_list(multiple_matches, show_status=False)
        return templates["multiple_matches"].format(task_list=task_list)

    if needs_confirmation and title:
        return templates["confirm"].format(title=title)

    if success and title:
        return templates["success"].format(title=title)

    if error_message and "not found" in error_message.lower():
        return templates["not_found"].format(reference=reference or "that task")

    return templates["error"].format(error_message=error_message or "Unknown error")


def build_fallback_response(
    suggested_cli: str,
    interpreted_action: str | None = None,
    low_confidence: bool = False,
) -> str:
    """Build response for UNKNOWN action or low confidence."""
    templates = RESPONSE_TEMPLATES[CommandAction.UNKNOWN]

    if low_confidence and interpreted_action:
        return templates["low_confidence"].format(
            interpreted_action=interpreted_action,
            suggested_cli=suggested_cli,
        )

    return templates["fallback"].format(suggested_cli=suggested_cli)


__all__ = [
    "RESPONSE_TEMPLATES",
    "format_task_list",
    "format_filter_description",
    "build_add_response",
    "build_list_response",
    "build_complete_response",
    "build_update_response",
    "build_delete_response",
    "build_fallback_response",
]
