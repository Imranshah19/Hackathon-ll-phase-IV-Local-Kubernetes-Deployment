"""
Models package.

Exports commonly used models and enums.
"""

from src.models.failure_mode import (
    STANDARD_FAILURE_MODES,
    FailureCode,
    FailureDetails,
    FailureModeDefinition,
    FailureResponse,
    Severity,
)
from src.models.skill import SkillCategory

# User models (Data Schemas Phase-2)
from src.models.user import User, UserBase, UserCreate, UserPublic

# Task models (Data Schemas Phase-2)
from src.models.task import Task, TaskBase, TaskCreate, TaskPublic, TaskUpdate

# Conversation and Message models (Phase 3 AI Chat)
from src.models.conversation import (
    Conversation,
    ConversationCreate,
    ConversationList,
    ConversationPublic,
)
from src.models.message import (
    AssistantMessageCreate,
    Message,
    MessageCreate,
    MessagePublic,
    MessageRole,
)

# Base utilities
from src.models.base import utc_now

# Phase 5: Tag models
from src.models.tag import Tag, TagBase, TagCreate, TagPublic, TagUpdate

# Phase 5: TaskTag junction model
from src.models.task_tag import TaskTag

# Phase 5: Recurrence models
from src.models.recurrence import (
    RecurrenceEndType,
    RecurrenceFrequency,
    RecurrenceRule,
    RecurrenceRuleBase,
    RecurrenceRuleCreate,
    RecurrenceRulePublic,
)

# Phase 5: Reminder models
from src.models.reminder import Reminder, ReminderBase, ReminderCreate, ReminderPublic

# Phase 5: TaskEvent models
from src.models.task_event import TaskEvent, TaskEventPublic, TaskEventType

__all__ = [
    # Skill enums
    "SkillCategory",
    # Failure mode enums and models
    "FailureCode",
    "Severity",
    "FailureModeDefinition",
    "FailureDetails",
    "FailureResponse",
    "STANDARD_FAILURE_MODES",
    # User models
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
    # Task models
    "Task",
    "TaskBase",
    "TaskCreate",
    "TaskPublic",
    "TaskUpdate",
    # Conversation models (Phase 3)
    "Conversation",
    "ConversationCreate",
    "ConversationPublic",
    "ConversationList",
    # Message models (Phase 3)
    "MessageRole",
    "Message",
    "MessageCreate",
    "AssistantMessageCreate",
    "MessagePublic",
    # Base utilities
    "utc_now",
    # Phase 5: Tag models
    "Tag",
    "TagBase",
    "TagCreate",
    "TagUpdate",
    "TagPublic",
    # Phase 5: TaskTag junction
    "TaskTag",
    # Phase 5: Recurrence models
    "RecurrenceFrequency",
    "RecurrenceEndType",
    "RecurrenceRuleBase",
    "RecurrenceRule",
    "RecurrenceRuleCreate",
    "RecurrenceRulePublic",
    # Phase 5: Reminder models
    "ReminderBase",
    "Reminder",
    "ReminderCreate",
    "ReminderPublic",
    # Phase 5: TaskEvent models
    "TaskEventType",
    "TaskEvent",
    "TaskEventPublic",
]
