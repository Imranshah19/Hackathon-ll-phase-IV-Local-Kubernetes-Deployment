# Phase 3: AI Integration + Deployment

## Overview

Phase 3 added the AI-powered natural language interface for task management, enabling users to create, list, update, and delete tasks using conversational commands.

## AI Architecture

```
User Message (Natural Language)
    ↓
AIInterpreter (OpenAI GPT-4 Function Calling)
    ├─ Intent Extraction
    ├─ Parameter Extraction
    └─ Confidence Scoring (0.0-1.0)
    ↓
InterpretedCommand
    ↓
CommandExecutor
    ├─ High Confidence (≥0.8) → Execute Immediately
    ├─ Medium Confidence (0.5-0.8) → Request Confirmation
    └─ Low Confidence (<0.5) → Suggest CLI Fallback
    ↓
TaskService (CRUD Operations)
    ↓
Response + Conversation History
```

## Backend Implementation

### New Files
```
backend/src/
├── ai/
│   ├── types.py        # InterpretedCommand, enums
│   ├── interpreter.py  # NLP → Command conversion
│   ├── executor.py     # Command → Task operation
│   ├── fallback.py     # Graceful degradation
│   └── prompts/
│       ├── intent.py   # Intent extraction prompts
│       └── response.py # Response generation
├── api/
│   ├── chat.py         # Chat endpoints
│   └── conversations.py # Conversation CRUD
├── models/
│   ├── conversation.py # Conversation entity
│   └── message.py      # Message entity
└── services/
    ├── chat_service.py # Chat orchestration
    └── conversation_service.py
```

### Database Schema (Phase 3)

**Conversations Table**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, CASCADE |
| title | VARCHAR(100) | nullable |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

**Messages Table**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| conversation_id | UUID | FK → conversations.id, CASCADE |
| role | VARCHAR | 'user' or 'assistant' |
| content | VARCHAR(2000) | NOT NULL |
| generated_command | VARCHAR(500) | nullable |
| confidence_score | FLOAT | 0.0-1.0, nullable |
| timestamp | TIMESTAMP | NOT NULL |

### API Endpoints

**Chat**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/message` | Send message, get AI response |
| POST | `/api/chat/confirm` | Confirm pending action |

**Conversations**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations` | List conversations |
| POST | `/api/conversations` | Create conversation |
| GET | `/api/conversations/{id}` | Get with messages |
| PATCH | `/api/conversations/{id}` | Update title |
| DELETE | `/api/conversations/{id}` | Delete conversation |

### Supported Commands

| Action | Example Messages |
|--------|------------------|
| ADD | "Add task to buy groceries" |
| LIST | "Show my tasks", "What's pending?" |
| COMPLETE | "Mark task 1 as done" |
| UPDATE | "Change task 2 to call mom" |
| DELETE | "Delete the grocery task" |

## Frontend Implementation

### New Files
```
frontend/src/
├── app/
│   └── chat/page.tsx      # Chat interface
└── components/chat/
    ├── ChatWindow.tsx     # Main orchestrator
    ├── MessageBubble.tsx  # Message display
    ├── InputBar.tsx       # Text input
    └── FallbackCLI.tsx    # CLI suggestion
```

### Chat UI Features
- Conversation sidebar
- Real-time message display
- Confidence indicators
- Action confirmation dialogs
- CLI fallback display
- Loading states

## Configuration

### Environment Variables
```env
# AI Configuration
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o-mini
AI_TIMEOUT_SECONDS=5

# Confidence Thresholds
AI_CONFIDENCE_THRESHOLD_HIGH=0.8
AI_CONFIDENCE_THRESHOLD_LOW=0.5
```

## Deployment Guide

### Backend (Render)

1. Create new Web Service
2. Connect GitHub repository
3. Set environment variables:
   ```
   DATABASE_URL=postgresql://...
   JWT_SECRET_KEY=...
   OPENAI_API_KEY=sk-...
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```
4. Build command: `pip install -e .`
5. Start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel)

1. Import from GitHub
2. Set environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```
3. Deploy

### Database (Neon)

1. Create PostgreSQL database
2. Copy connection string
3. Run migrations:
   ```bash
   DATABASE_URL=postgresql://... alembic upgrade head
   ```

## Success Criteria

- [x] AI interpretation working
- [x] Confidence scoring implemented
- [x] CLI fallback functional
- [x] Conversation history persisted
- [x] Chat UI complete
- [x] Database migrations created
- [x] Backend deployed
- [x] Frontend deployed

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Chat response time | <3s | ✅ |
| AI accuracy | >90% | ✅ |
| AI timeout | 5s max | ✅ |
| Page load | <3s | ✅ |
