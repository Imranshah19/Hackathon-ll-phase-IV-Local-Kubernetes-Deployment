"""
Urdu Language Support for AI Chatbot (Phase 5 - US6).

Provides:
- Language detection (English/Urdu)
- Urdu command patterns mapping
- Bilingual response generation
- Urdu-English translation utilities

Implements:
- FR-021: Automatic language detection
- FR-022: Respond in same language as input
- FR-023: Support all task commands in both languages
- FR-024: Store tasks in creation language

Urdu Command Mappings:
- نیا کام / کام شامل کرو → ADD (new task / add task)
- دکھاؤ / میرے کام → LIST (show / my tasks)
- مکمل / ہو گیا → COMPLETE (complete / done)
- حذف / مٹا دو → DELETE (delete / remove)
- تبدیل / بدلو → UPDATE (change / modify)
"""

import re
import unicodedata
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from src.ai.types import CommandAction


class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    URDU = "ur"
    MIXED = "mixed"


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""
    language: Language
    confidence: float
    urdu_ratio: float
    english_ratio: float


# =============================================================================
# Urdu Command Patterns
# =============================================================================

# Urdu keywords for each action
URDU_ADD_KEYWORDS = [
    "نیا کام",        # new task
    "کام شامل",       # add task
    "شامل کرو",       # add (it)
    "بناؤ",          # create
    "نیا",           # new
    "شامل",          # add
    "ڈالو",          # put/add
    "لکھو",          # write
]

URDU_LIST_KEYWORDS = [
    "دکھاؤ",         # show
    "میرے کام",       # my tasks
    "کام دکھاؤ",      # show tasks
    "فہرست",         # list
    "سب کام",        # all tasks
    "کیا کرنا ہے",    # what to do
    "باقی کام",       # remaining tasks
]

URDU_COMPLETE_KEYWORDS = [
    "مکمل",          # complete
    "ہو گیا",         # done
    "ختم",           # finished
    "کر لیا",         # did it
    "پورا",          # full/complete
    "ہو گئی",         # (feminine) done
]

URDU_DELETE_KEYWORDS = [
    "حذف",           # delete
    "مٹا دو",         # erase
    "ہٹاؤ",          # remove
    "نکالو",          # take out
    "ختم کرو",        # end it
    "مٹاؤ",          # erase
]

URDU_UPDATE_KEYWORDS = [
    "تبدیل",          # change
    "بدلو",          # change (imperative)
    "ترمیم",          # edit
    "اپڈیٹ",          # update (loan word)
    "درست",          # correct
    "ٹھیک کرو",       # fix it
]

# Priority keywords in Urdu
URDU_PRIORITY_KEYWORDS = {
    "اہم": 1,         # important (Critical)
    "ضروری": 1,       # necessary (Critical)
    "فوری": 1,        # urgent (Critical)
    "اعلی": 2,        # high
    "زیادہ": 2,       # more/high
    "درمیانی": 3,     # medium
    "کم": 4,          # low
    "عام": 5,         # normal/none
}

# Time-related Urdu words
URDU_TIME_KEYWORDS = {
    "آج": "today",
    "کل": "tomorrow",
    "اگلے ہفتے": "next week",
    "اگلے مہینے": "next month",
    "ابھی": "now",
    "جلدی": "soon",
    "فوری": "immediately",
}

# =============================================================================
# Urdu Response Templates
# =============================================================================

URDU_RESPONSES = {
    "task_created": "کام شامل ہو گیا: {title}",
    "task_completed": "کام مکمل ہو گیا: {title}",
    "task_deleted": "کام حذف ہو گیا",
    "task_updated": "کام اپڈیٹ ہو گیا: {title}",
    "tasks_list_header": "آپ کے کام ({count}):",
    "no_tasks": "کوئی کام نہیں ہے",
    "task_not_found": "کام نہیں ملا",
    "confirmation_needed": "کیا آپ واقعی '{action}' کرنا چاہتے ہیں؟",
    "clarification_needed": "براہ کرم وضاحت کریں: {question}",
    "error_occurred": "معذرت، کچھ غلط ہو گیا",
    "recurring_next": "اگلا کام بن گیا: {date}",
    "priority_set": "ترجیح سیٹ ہو گئی: {level}",
    "tags_added": "ٹیگز شامل ہو گئے: {tags}",
}

ENGLISH_RESPONSES = {
    "task_created": "Task created: {title}",
    "task_completed": "Task completed: {title}",
    "task_deleted": "Task deleted",
    "task_updated": "Task updated: {title}",
    "tasks_list_header": "Your tasks ({count}):",
    "no_tasks": "No tasks found",
    "task_not_found": "Task not found",
    "confirmation_needed": "Do you want to '{action}'?",
    "clarification_needed": "Please clarify: {question}",
    "error_occurred": "Sorry, something went wrong",
    "recurring_next": "Next occurrence created: {date}",
    "priority_set": "Priority set: {level}",
    "tags_added": "Tags added: {tags}",
}


# =============================================================================
# Language Detection
# =============================================================================

def is_urdu_char(char: str) -> bool:
    """Check if a character is Urdu/Arabic script."""
    if len(char) != 1:
        return False
    try:
        name = unicodedata.name(char, "")
        return "ARABIC" in name or "URDU" in name
    except ValueError:
        return False


def is_english_char(char: str) -> bool:
    """Check if a character is English/Latin."""
    if len(char) != 1:
        return False
    return char.isascii() and char.isalpha()


def detect_language(text: str) -> LanguageDetectionResult:
    """
    Detect the language of the input text.

    Args:
        text: Input text to analyze

    Returns:
        LanguageDetectionResult with detected language and confidence
    """
    if not text or not text.strip():
        return LanguageDetectionResult(
            language=Language.ENGLISH,
            confidence=0.0,
            urdu_ratio=0.0,
            english_ratio=0.0,
        )

    urdu_count = 0
    english_count = 0
    total_chars = 0

    for char in text:
        if char.isspace() or char.isdigit() or char in ".,!?;:'\"()-":
            continue
        total_chars += 1
        if is_urdu_char(char):
            urdu_count += 1
        elif is_english_char(char):
            english_count += 1

    if total_chars == 0:
        return LanguageDetectionResult(
            language=Language.ENGLISH,
            confidence=0.5,
            urdu_ratio=0.0,
            english_ratio=0.0,
        )

    urdu_ratio = urdu_count / total_chars
    english_ratio = english_count / total_chars

    # Determine language
    if urdu_ratio > 0.7:
        language = Language.URDU
        confidence = urdu_ratio
    elif english_ratio > 0.7:
        language = Language.ENGLISH
        confidence = english_ratio
    elif urdu_ratio > english_ratio:
        language = Language.URDU if urdu_ratio > 0.3 else Language.MIXED
        confidence = urdu_ratio
    else:
        language = Language.ENGLISH if english_ratio > 0.3 else Language.MIXED
        confidence = english_ratio

    return LanguageDetectionResult(
        language=language,
        confidence=confidence,
        urdu_ratio=urdu_ratio,
        english_ratio=english_ratio,
    )


# =============================================================================
# Command Pattern Matching
# =============================================================================

def match_urdu_command(text: str) -> tuple[CommandAction | None, float]:
    """
    Match Urdu text to a command action.

    Args:
        text: Urdu text to match

    Returns:
        Tuple of (matched action, confidence) or (None, 0.0) if no match
    """
    text_lower = text.strip()

    # Check each action's keywords
    action_matches: list[tuple[CommandAction, float]] = []

    for keyword in URDU_ADD_KEYWORDS:
        if keyword in text_lower:
            action_matches.append((CommandAction.ADD, 0.9))
            break

    for keyword in URDU_LIST_KEYWORDS:
        if keyword in text_lower:
            action_matches.append((CommandAction.LIST, 0.9))
            break

    for keyword in URDU_COMPLETE_KEYWORDS:
        if keyword in text_lower:
            action_matches.append((CommandAction.COMPLETE, 0.9))
            break

    for keyword in URDU_DELETE_KEYWORDS:
        if keyword in text_lower:
            action_matches.append((CommandAction.DELETE, 0.9))
            break

    for keyword in URDU_UPDATE_KEYWORDS:
        if keyword in text_lower:
            action_matches.append((CommandAction.UPDATE, 0.9))
            break

    if not action_matches:
        return None, 0.0

    # Return highest confidence match
    action_matches.sort(key=lambda x: x[1], reverse=True)
    return action_matches[0]


def extract_urdu_priority(text: str) -> int | None:
    """
    Extract priority level from Urdu text.

    Args:
        text: Urdu text to analyze

    Returns:
        Priority level (1-5) or None if not found
    """
    for keyword, priority in URDU_PRIORITY_KEYWORDS.items():
        if keyword in text:
            return priority
    return None


def extract_urdu_time(text: str) -> str | None:
    """
    Extract time reference from Urdu text.

    Args:
        text: Urdu text to analyze

    Returns:
        English time reference or None if not found
    """
    for urdu_time, english_time in URDU_TIME_KEYWORDS.items():
        if urdu_time in text:
            return english_time
    return None


def extract_task_title_urdu(text: str, action: CommandAction) -> str | None:
    """
    Extract task title from Urdu command text.

    For ADD commands, tries to extract the task description.

    Args:
        text: Urdu command text
        action: The detected action

    Returns:
        Extracted title or None
    """
    if action != CommandAction.ADD:
        return None

    # Remove common command prefixes
    title = text
    for keyword in URDU_ADD_KEYWORDS:
        title = title.replace(keyword, "").strip()

    # Remove punctuation and clean up
    title = re.sub(r'[:\-،۔]', ' ', title).strip()

    # If we have something left, return it
    if title and len(title) > 1:
        return title

    return None


# =============================================================================
# Response Generation
# =============================================================================

def get_response(
    key: str,
    language: Language,
    **kwargs
) -> str:
    """
    Get a localized response string.

    Args:
        key: Response template key
        language: Target language
        **kwargs: Format arguments

    Returns:
        Formatted response string
    """
    templates = URDU_RESPONSES if language == Language.URDU else ENGLISH_RESPONSES
    template = templates.get(key, ENGLISH_RESPONSES.get(key, key))

    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def format_task_list_urdu(tasks: list[dict]) -> str:
    """
    Format a task list in Urdu.

    Args:
        tasks: List of task dictionaries

    Returns:
        Formatted Urdu string
    """
    if not tasks:
        return URDU_RESPONSES["no_tasks"]

    lines = [URDU_RESPONSES["tasks_list_header"].format(count=len(tasks))]

    for i, task in enumerate(tasks, 1):
        status = "✓" if task.get("is_completed") else "○"
        title = task.get("title", "بغیر عنوان")
        lines.append(f"  {i}. {status} {title}")

    return "\n".join(lines)


# =============================================================================
# Bilingual Prompt Enhancement
# =============================================================================

URDU_SYSTEM_PROMPT_ADDITION = """
You also understand Urdu (اردو). When the user writes in Urdu:
1. Detect the language and respond in the SAME language
2. Map Urdu commands to actions:
   - نیا کام / شامل کرو → ADD (create new task)
   - دکھاؤ / میرے کام → LIST (show tasks)
   - مکمل / ہو گیا → COMPLETE (mark as done)
   - حذف / مٹا دو → DELETE (remove task)
   - تبدیل / بدلو → UPDATE (modify task)
3. Extract task titles from Urdu text
4. Map Urdu time words: آج (today), کل (tomorrow), اگلے ہفتے (next week)
5. Map Urdu priorities: فوری/اہم (urgent/important=1), اعلی (high=2), درمیانی (medium=3), کم (low=4)

Example Urdu commands:
- "نیا کام شامل کرو: دودھ خریدنا" → ADD task "دودھ خریدنا"
- "میرے کام دکھاؤ" → LIST all tasks
- "پہلا کام مکمل" → COMPLETE task 1
- "کل تک فوری کام بناؤ" → ADD urgent task due tomorrow
"""


__all__ = [
    "Language",
    "LanguageDetectionResult",
    "detect_language",
    "match_urdu_command",
    "extract_urdu_priority",
    "extract_urdu_time",
    "extract_task_title_urdu",
    "get_response",
    "format_task_list_urdu",
    "URDU_SYSTEM_PROMPT_ADDITION",
    "URDU_RESPONSES",
    "ENGLISH_RESPONSES",
]
