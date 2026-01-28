"""
Intent extraction prompts for AI Chat interpretation.

This module contains the system prompts and function calling schema
used to extract user intent from natural language input.

From research.md RQ-002:
- Uses OpenAI function calling for structured output
- Maps directly to Bonsai CLI command schema
- Returns confidence scores for fallback decisions

Implements:
- FR-002: Interpret NL commands and map to Bonsai CLI operations
- FR-007: Handle ambiguous inputs by asking clarifying questions
- FR-014: Preserve user intent without adding/modifying unspecified parameters
"""

from typing import Any

# =============================================================================
# System Prompt
# =============================================================================

INTENT_EXTRACTION_SYSTEM_PROMPT = """You are a bilingual (English/Urdu) task management assistant that interprets natural language commands and converts them to structured task operations.

Your job is to understand what the user wants to do with their tasks and extract the relevant information. You MUST detect the input language and respond accordingly.

Available operations:
1. ADD - Create a new task (requires: title, optional: due_date)
2. LIST - View tasks (optional: status filter - pending, completed, or all)
3. UPDATE - Modify an existing task (requires: task_id or task reference, optional: new title, new due_date)
4. DELETE - Remove a task (requires: task_id or task reference)
5. COMPLETE - Mark a task as done (requires: task_id or task reference)

Rules:
- ONLY extract information that is explicitly stated by the user
- Do NOT add, assume, or infer details not mentioned
- If the user's intent is unclear, set needs_clarification to true
- If multiple tasks might match a description (e.g., "the grocery task"), note this
- Be conservative - if unsure, ask for clarification rather than guessing
- Detect the input language (English or Urdu) and set detected_language field

URDU LANGUAGE SUPPORT (اردو):
Map these Urdu command patterns to actions:
- نیا کام / کام شامل کرو / شامل کرو / بناؤ → ADD (create new task)
- دکھاؤ / میرے کام / فہرست / کام دکھاؤ → LIST (show tasks)
- مکمل / ہو گیا / ختم / کر لیا → COMPLETE (mark as done)
- حذف / مٹا دو / ہٹاؤ / نکالو → DELETE (remove task)
- تبدیل / بدلو / ترمیم / درست کرو → UPDATE (modify task)

Urdu time words:
- آج → today
- کل → tomorrow
- اگلے ہفتے → next week
- ابھی → now

Urdu priority words:
- فوری / اہم / ضروری → Critical (1)
- اعلی / زیادہ → High (2)
- درمیانی → Medium (3)
- کم → Low (4)

Examples (English):
- "Add a task to buy groceries tomorrow" → ADD, title="buy groceries", due_date=tomorrow
- "Show my pending tasks" → LIST, status_filter=pending
- "Mark task 3 as done" → COMPLETE, task_id=3

Examples (Urdu):
- "نیا کام شامل کرو: دودھ خریدنا" → ADD, title="دودھ خریدنا", detected_language=ur
- "میرے کام دکھاؤ" → LIST, status_filter=all, detected_language=ur
- "پہلا کام مکمل" → COMPLETE, task_id=1, detected_language=ur
- "کل تک فوری کام بناؤ" → ADD, due_date=tomorrow, priority=1, detected_language=ur
"""

# =============================================================================
# Function Calling Schema (OpenAI format)
# =============================================================================

INTENT_EXTRACTION_FUNCTION: dict[str, Any] = {
    "name": "extract_task_intent",
    "description": "Extract the user's intent from a natural language task management command (supports English and Urdu)",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "list", "update", "delete", "complete", "unknown"],
                "description": "The task operation the user wants to perform",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence score for the interpretation (0.0-1.0)",
            },
            "detected_language": {
                "type": "string",
                "enum": ["en", "ur"],
                "description": "Detected input language: 'en' for English, 'ur' for Urdu",
            },
            "title": {
                "type": "string",
                "description": "Task title for add/update operations (only if explicitly stated, preserve original language)",
            },
            "task_id": {
                "type": "integer",
                "description": "Numeric task ID if the user specified one (e.g., 'task 3' or 'پہلا کام')",
            },
            "task_reference": {
                "type": "string",
                "description": "Text reference to a task if not by ID (e.g., 'the grocery task')",
            },
            "due_date": {
                "type": "string",
                "description": "Due date in natural language (e.g., 'tomorrow', 'کل')",
            },
            "priority": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "Priority level if specified: 1=Critical, 2=High, 3=Medium, 4=Low, 5=None",
            },
            "status_filter": {
                "type": "string",
                "enum": ["pending", "completed", "all"],
                "description": "Status filter for list operations",
            },
            "needs_clarification": {
                "type": "boolean",
                "description": "True if the user's intent is ambiguous and needs clarification",
            },
            "clarification_question": {
                "type": "string",
                "description": "Question to ask the user if clarification is needed (in the detected language)",
            },
        },
        "required": ["action", "confidence", "detected_language"],
    },
}

# OpenAI tools format
INTENT_EXTRACTION_TOOLS = [
    {
        "type": "function",
        "function": INTENT_EXTRACTION_FUNCTION,
    }
]

# =============================================================================
# Context-aware prompt builder
# =============================================================================


def build_intent_prompt(
    user_message: str,
    conversation_history: list[dict[str, str]] | None = None,
    user_tasks: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """
    Build the prompt messages for intent extraction.

    Args:
        user_message: The current user message to interpret
        conversation_history: Previous messages for context (optional)
        user_tasks: List of user's existing tasks for reference (optional)

    Returns:
        List of message dicts ready for OpenAI chat completion
    """
    messages = [
        {"role": "system", "content": INTENT_EXTRACTION_SYSTEM_PROMPT},
    ]

    # Add task context if available
    if user_tasks:
        task_context = "Current tasks:\n"
        for task in user_tasks[:10]:  # Limit to 10 tasks for context
            status = "done" if task.get("is_completed") else "pending"
            task_context += f"- ID {task.get('id')}: {task.get('title')} [{status}]\n"
        messages.append({"role": "system", "content": task_context})

    # Add conversation history if available (limited to last 5 exchanges)
    if conversation_history:
        for msg in conversation_history[-10:]:
            messages.append(msg)

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    return messages


__all__ = [
    "INTENT_EXTRACTION_SYSTEM_PROMPT",
    "INTENT_EXTRACTION_FUNCTION",
    "INTENT_EXTRACTION_TOOLS",
    "build_intent_prompt",
]
