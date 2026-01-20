# Data Model: Phase 3 AI Chat

**Feature**: 006-ai-chat
**Date**: 2026-01-19
**Status**: Complete

## Entity Overview

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      User       │────<│  Conversation   │────<│    Message      │
│   (Phase 2)     │     │     (NEW)       │     │     (NEW)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │
        │
        ▼
┌─────────────────┐
│      Task       │
│   (Phase 2)     │
└─────────────────┘

Legend: ────< = one-to-many relationship
```

## Entities

### Conversation (NEW)

Represents a chat session between a user and the AI assistant.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique conversation identifier |
| user_id | UUID | FK → users.id, NOT NULL | Owner of the conversation |
| title | string | max 100 chars, nullable | Optional conversation title (auto-generated from first message) |
| created_at | timestamp | NOT NULL, default NOW() | When conversation started |
| updated_at | timestamp | NOT NULL, auto-update | Last activity timestamp |

**Indexes**:
- `idx_conversations_user_id` on (user_id)
- `idx_conversations_updated_at` on (updated_at DESC)

**Validation Rules**:
- user_id must reference a valid, active user
- Only the owning user can access their conversations (FR-013)

**State Transitions**: None (conversations are append-only)

---

### Message (NEW)

An individual message within a conversation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique message identifier |
| conversation_id | UUID | FK → conversations.id, NOT NULL | Parent conversation |
| role | enum | 'user' \| 'assistant', NOT NULL | Who sent the message |
| content | text | NOT NULL, max 2000 chars | Message content |
| generated_command | string | nullable, max 500 chars | Bonsai CLI command (assistant only) |
| confidence_score | float | nullable, 0.0-1.0 | AI interpretation confidence |
| timestamp | timestamp | NOT NULL, default NOW() | When message was sent |

**Indexes**:
- `idx_messages_conversation_id` on (conversation_id)
- `idx_messages_timestamp` on (timestamp)

**Validation Rules**:
- content must not be empty or whitespace-only
- generated_command only populated for role='assistant'
- confidence_score only populated for role='assistant'
- Messages are immutable after creation

**State Transitions**: None (messages are immutable)

---

### InterpretedCommand (Internal - Not Persisted)

Runtime representation of an AI-interpreted user intent. Used for processing pipeline only.

| Field | Type | Description |
|-------|------|-------------|
| original_text | string | User's raw input |
| action | enum | 'add' \| 'list' \| 'update' \| 'delete' \| 'complete' \| 'unknown' |
| task_id | int \| null | Target task ID (for update/delete/complete) |
| title | string \| null | Task title (for add/update) |
| due_date | date \| null | Due date (for add/update) |
| status_filter | enum \| null | 'pending' \| 'completed' \| 'all' (for list) |
| confidence | float | 0.0-1.0 interpretation confidence |
| clarification_needed | string \| null | Question to ask user if ambiguous |
| suggested_cli | string | Equivalent Bonsai CLI command |

---

### Task (Existing - Phase 2)

No changes to the Task entity from Phase 2. Referenced here for completeness.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique task identifier |
| title | string | NOT NULL, max 200 chars | Task title |
| description | text | nullable | Task details |
| status | enum | 'pending' \| 'completed' | Current status |
| due | date | nullable | Due date |
| created_at | timestamp | NOT NULL | Creation timestamp |
| updated_at | timestamp | NOT NULL | Last update timestamp |
| user_id | UUID | FK → users.id | Task owner |

---

## Relationships

### User → Conversation (1:N)
- A user can have many conversations
- Each conversation belongs to exactly one user
- Deleting a user cascades to delete all their conversations

### Conversation → Message (1:N)
- A conversation contains many messages
- Each message belongs to exactly one conversation
- Deleting a conversation cascades to delete all its messages

### User → Task (1:N) - Existing
- Unchanged from Phase 2
- AI commands operate on tasks owned by the authenticated user only

---

## Database Schema (SQLModel)

```python
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional, List

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    title: Optional[str] = Field(max_length=100, default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    messages: List["Message"] = Relationship(back_populates="conversation")

class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversations.id", nullable=False, index=True)
    role: MessageRole = Field(nullable=False)
    content: str = Field(max_length=2000, nullable=False)
    generated_command: Optional[str] = Field(max_length=500, default=None)
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
```

---

## Migration Notes

### From Phase 2
- No changes to existing `tasks` or `users` tables
- Add `conversations` table
- Add `messages` table
- Add foreign key indexes for performance

### Rollback Strategy
- Drop `messages` table first (FK dependency)
- Drop `conversations` table
- No impact on Phase 2 functionality
