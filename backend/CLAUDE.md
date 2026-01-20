# Backend Development Guidelines

## Technology Stack

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Database**: PostgreSQL (Neon) / SQLite (dev)
- **ORM**: SQLModel
- **Auth**: JWT (python-jose) + Argon2 passwords
- **AI**: OpenAI API for NLP interpretation

## Project Structure

```
backend/
├── src/
│   ├── api/                 # FastAPI routers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── tasks.py         # Task CRUD endpoints
│   │   ├── chat.py          # AI Chat endpoints (Phase 3)
│   │   └── conversations.py # Conversation CRUD (Phase 3)
│   ├── models/              # SQLModel entities
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── conversation.py  # Phase 3
│   │   └── message.py       # Phase 3
│   ├── services/            # Business logic
│   │   ├── task_service.py
│   │   ├── chat_service.py  # Phase 3 orchestrator
│   │   └── conversation_service.py
│   ├── ai/                  # AI integration (Phase 3)
│   │   ├── types.py         # InterpretedCommand, enums
│   │   ├── interpreter.py   # NLP → Command conversion
│   │   ├── executor.py      # Command → Task operation
│   │   ├── fallback.py      # Graceful degradation
│   │   └── prompts/         # LLM prompt templates
│   ├── auth/                # JWT and password handling
│   ├── config/              # Configuration management
│   ├── db.py                # Database connection
│   └── main.py              # FastAPI app entry
└── tests/
    ├── unit/                # Isolated unit tests
    ├── integration/         # Cross-layer tests
    └── contract/            # API schema tests
```

## Coding Conventions

### API Routers

- One router per domain (auth, tasks, chat, conversations)
- Use dependency injection for session and user_id
- Pydantic models for request/response schemas
- Consistent error handling

```python
@router.post("/", response_model=TaskPublic, status_code=201)
async def create_task(
    data: TaskCreate,
    session: DbSession,
    user_id: CurrentUserId,
) -> TaskPublic:
    service = TaskService(session, user_id)
    return service.create_task(data)
```

### Services

- Business logic lives in services, not routers
- Services receive session and user_id in constructor
- Return domain objects, not HTTP responses
- Raise ValueError for business rule violations

```python
class TaskService:
    def __init__(self, session: Session, user_id: UUID):
        self.session = session
        self.user_id = user_id

    def create_task(self, data: TaskCreate) -> Task:
        task = Task(user_id=self.user_id, **data.model_dump())
        self.session.add(task)
        self.session.commit()
        return task
```

### Models

- SQLModel for database entities
- Separate schemas: Base, Create, Public, Update
- UUID primary keys with auto-generation
- Timestamps with UTC timezone

```python
class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    title: str = Field(max_length=255)
```

### Phase 3 AI Layer

**Principle**: AI as Interpreter, Not Executor

```
User Message → AIInterpreter → InterpretedCommand
                                    ↓
                              CommandExecutor → TaskService
                                    ↓
                              FallbackHandler (if low confidence)
```

**AIInterpreter** (`ai/interpreter.py`):
- Converts natural language to InterpretedCommand
- Uses OpenAI function calling for intent extraction
- 5-second timeout with fallback
- Returns confidence score (0.0-1.0)

**CommandExecutor** (`ai/executor.py`):
- Executes InterpretedCommand via TaskService
- Maps actions to CRUD operations
- Returns execution result

**FallbackHandler** (`ai/fallback.py`):
- Handles low confidence scenarios
- Generates CLI command suggestions
- Provides graceful degradation

**Confidence Thresholds**:
- `>= 0.8`: Execute immediately
- `0.5 - 0.8`: Request confirmation
- `< 0.5`: Suggest CLI fallback

### Error Handling

- Raise HTTPException for API errors
- Raise ValueError for business logic errors
- Log errors with context
- Never expose internal details to clients

### Environment Variables

Load from `.env` file:
```
DATABASE_URL=sqlite:///./dev.db
JWT_SECRET_KEY=your-secret
OPENAI_API_KEY=sk-...
AI_TIMEOUT_SECONDS=5
```

## Testing

### Test Categories

- **Unit tests** (`tests/unit/`): Isolated, no database
- **Integration tests** (`tests/integration/`): With database
- **Contract tests** (`tests/contract/`): API schema validation

### Test Fixtures

```python
@pytest.fixture
def session():
    # In-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

### TDD Workflow

1. Write test that fails (Red)
2. Implement minimal code to pass (Green)
3. Refactor if needed (Refactor)

## Don'ts

- Don't put business logic in routers
- Don't access database without user isolation check
- Don't hardcode secrets
- Don't skip input validation
- Don't let AI directly modify database
- Don't ignore timeout handling for AI calls
