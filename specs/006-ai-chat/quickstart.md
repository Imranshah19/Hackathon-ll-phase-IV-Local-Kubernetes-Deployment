# Quickstart: Phase 3 AI Chat

**Feature**: 006-ai-chat
**Date**: 2026-01-19

## Prerequisites

Before starting Phase 3 development:

1. **Phase 2 Complete**: Bonsai CLI must be functional
   ```bash
   bonsai list --status all  # Should work without errors
   ```

2. **Environment Variables**: Add to `.env`:
   ```bash
   # AI Provider (choose one)
   OPENAI_API_KEY=sk-...
   # or
   ANTHROPIC_API_KEY=sk-ant-...

   # Existing Phase 2 variables should already be set
   DATABASE_URL=postgresql://...
   JWT_SECRET=...
   ```

3. **Dependencies**: Install new packages:
   ```bash
   # Backend
   cd backend
   pip install openai anthropic  # AI providers

   # Frontend (already has React)
   cd frontend
   npm install  # No new dependencies needed
   ```

## Development Setup

### 1. Database Migration

Run migration to add conversation and message tables:

```bash
cd backend
alembic upgrade head
```

Verify tables exist:
```bash
psql $DATABASE_URL -c "\dt"
# Should show: conversations, messages (in addition to existing tables)
```

### 2. Start Backend

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

Verify AI chat endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Show my tasks"}'
```

### 3. Start Frontend

```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:3000/chat` to use the chat interface.

## Testing the Feature

### Manual Testing Checklist

1. **Create task via chat**:
   - Type: "Add a task to buy groceries tomorrow"
   - Verify: Task appears in task list with correct title and due date

2. **List tasks via chat**:
   - Type: "Show my pending tasks"
   - Verify: Only pending tasks displayed

3. **Complete task via chat**:
   - Type: "Mark task 1 as done"
   - Verify: Task status changes to completed

4. **Fallback test**:
   - Temporarily disable AI API key
   - Type any message
   - Verify: Receives CLI command alternative

### Running Automated Tests

```bash
# Backend unit tests
cd backend
pytest tests/unit/test_interpreter.py -v

# Backend integration tests
pytest tests/integration/test_chat_flow.py -v

# Frontend component tests
cd frontend
npm test -- --testPathPattern=chat

# End-to-end tests
npm run test:e2e -- --spec=chat-flow.spec.ts
```

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ ChatWindow  │  │ InputBar    │  │ FallbackCLI         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP POST /api/v1/chat/message
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ chat.py     │──│ ChatService │──│ AI Interpreter      │ │
│  │ (API)       │  │             │  │ (OpenAI/Claude)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                             │                                │
│                             ▼                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              BonsaiExecutor (CLI Bridge)                 ││
│  │  Calls existing Phase 2 CLI service functions           ││
│  └─────────────────────────────────────────────────────────┘│
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL (Neon)                         │
│  ┌───────────┐  ┌───────────────┐  ┌──────────────────────┐│
│  │  tasks    │  │ conversations │  │      messages        ││
│  │ (Phase 2) │  │    (NEW)      │  │       (NEW)          ││
│  └───────────┘  └───────────────┘  └──────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Common Issues

### AI Timeout (>5 seconds)
- Check API key is valid
- Verify network connectivity
- System will automatically suggest CLI alternative

### "Conversation not found" Error
- Ensure conversation_id is valid UUID
- Check user owns the conversation (user isolation)

### Interpretation Accuracy Issues
- Check `confidence_score` in response
- If consistently low, review prompt templates in `backend/src/ai/prompts/`

## Next Steps

After completing Phase 3:
1. Run full test suite: `npm run test:all`
2. Verify Constitution compliance via checklist
3. Create PR for review
