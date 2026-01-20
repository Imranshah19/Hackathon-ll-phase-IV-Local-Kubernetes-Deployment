# Database Schema

**Version**: 1.0.0
**Database**: PostgreSQL (Neon Serverless) / SQLite (development)
**ORM**: SQLModel

This document consolidates all database tables across Phase 1, 2, and 3.

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │    tasks    │       │conversations│
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │◄──┬───│ user_id (FK)│   ┌───│ id (PK)     │
│ email       │   │   │ id (PK)     │   │   │ user_id (FK)│──┐
│ password_   │   │   │ title       │   │   │ title       │  │
│   hash      │   │   │ description │   │   │ created_at  │  │
│ created_at  │   │   │ is_completed│   │   │ updated_at  │  │
│ updated_at  │   │   │ created_at  │   │   └─────────────┘  │
└─────────────┘   │   │ updated_at  │   │                    │
                  │   └─────────────┘   │   ┌─────────────┐  │
                  │                     │   │  messages   │  │
                  │                     │   ├─────────────┤  │
                  │                     └───│conversation_│  │
                  │                         │   id (FK)   │  │
                  │                         │ id (PK)     │  │
                  │                         │ role        │  │
                  │                         │ content     │  │
                  │                         │ generated_  │  │
                  │                         │   command   │  │
                  │                         │ confidence_ │  │
                  │                         │   score     │  │
                  │                         │ timestamp   │  │
                  └─────────────────────────└─────────────┘
```

---

## Tables

### users (Phase 2)

Core user authentication table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Unique user identifier |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | User email address |
| `password_hash` | VARCHAR(255) | NOT NULL | Argon2id hashed password |
| `created_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Account creation time |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Last update time |

**Indexes**:
- `PRIMARY KEY (id)`
- `UNIQUE INDEX idx_users_email ON users(email)`

**Validation Rules**:
- Email must be valid RFC 5322 format
- Password minimum 8 characters (before hashing)

---

### tasks (Phase 2)

User task items.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Unique task identifier |
| `user_id` | UUID | FK → users.id, NOT NULL | Owner user |
| `title` | VARCHAR(255) | NOT NULL | Task title |
| `description` | TEXT | NULLABLE | Optional description |
| `is_completed` | BOOLEAN | NOT NULL, DEFAULT FALSE | Completion status |
| `created_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Task creation time |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Last update time |

**Indexes**:
- `PRIMARY KEY (id)`
- `INDEX idx_tasks_user_id ON tasks(user_id)`
- `INDEX idx_tasks_is_completed ON tasks(is_completed)`

**Foreign Keys**:
- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`

**Validation Rules**:
- Title: 1-255 characters
- Description: max 4000 characters

---

### conversations (Phase 3)

Chat conversation sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Unique conversation identifier |
| `user_id` | UUID | FK → users.id, NOT NULL | Owner user |
| `title` | VARCHAR(100) | NULLABLE | Optional conversation title |
| `created_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Conversation start time |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Last activity time |

**Indexes**:
- `PRIMARY KEY (id)`
- `INDEX idx_conversations_user_id ON conversations(user_id)`
- `INDEX idx_conversations_updated_at ON conversations(updated_at DESC)`

**Foreign Keys**:
- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`

---

### messages (Phase 3)

Individual chat messages within conversations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Unique message identifier |
| `conversation_id` | UUID | FK → conversations.id, NOT NULL | Parent conversation |
| `role` | VARCHAR(20) | NOT NULL, CHECK IN ('user', 'assistant') | Message sender |
| `content` | VARCHAR(2000) | NOT NULL | Message text |
| `generated_command` | VARCHAR(500) | NULLABLE | CLI command (assistant only) |
| `confidence_score` | FLOAT | NULLABLE, CHECK 0.0-1.0 | AI confidence (assistant only) |
| `timestamp` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Message time |

**Indexes**:
- `PRIMARY KEY (id)`
- `INDEX idx_messages_conversation_id ON messages(conversation_id)`
- `INDEX idx_messages_timestamp ON messages(timestamp)`

**Foreign Keys**:
- `FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE`

**Validation Rules**:
- Content: 1-2000 characters, not whitespace-only
- Role: must be 'user' or 'assistant'
- Confidence score: only for assistant messages, 0.0 to 1.0

---

## Relationships

### One-to-Many

| Parent | Child | Cascade |
|--------|-------|---------|
| users | tasks | DELETE CASCADE |
| users | conversations | DELETE CASCADE |
| conversations | messages | DELETE CASCADE |

### Data Isolation

- Users can ONLY access their own tasks
- Users can ONLY access their own conversations
- Users can ONLY access messages in their own conversations

---

## Migration Notes

### Phase 2 → Phase 3

Add the following tables:
1. `conversations` - new table
2. `messages` - new table

No changes to existing `users` and `tasks` tables.

### SQLite Development Mode

For local development without PostgreSQL:
- UUID stored as TEXT
- Timestamps stored as TEXT in ISO 8601 format
- No native UUID generation (use Python uuid4)

---

## SQLModel Definitions

```python
# backend/src/models/user.py
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    tasks: list["Task"] = Relationship(back_populates="user", cascade_delete=True)
    conversations: list["Conversation"] = Relationship(back_populates="user", cascade_delete=True)

# backend/src/models/task.py
class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    is_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: "User" = Relationship(back_populates="tasks")

# backend/src/models/conversation.py
class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: "User" = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(back_populates="conversation", cascade_delete=True)

# backend/src/models/message.py
class Message(SQLModel, table=True):
    __tablename__ = "messages"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversations.id", index=True)
    role: MessageRole  # Enum: user, assistant
    content: str = Field(max_length=2000)
    generated_command: str | None = Field(default=None, max_length=500)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=utc_now, index=True)

    conversation: "Conversation" = Relationship(back_populates="messages")
```
