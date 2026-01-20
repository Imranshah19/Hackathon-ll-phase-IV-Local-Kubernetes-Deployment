---
id: 004
title: Phase-3 Implementation Foundation
stage: green
date: 2026-01-19
surface: agent
model: claude-opus-4-5-20251101
feature: 006-ai-chat
branch: 006-ai-chat
user: developer
command: implement phase-3
labels: ["ai-chat", "implementation", "openai", "mcp", "phase-3"]
links:
  spec: specs/006-ai-chat/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/ai/interpreter.py
  - backend/src/ai/executor.py
  - backend/src/ai/fallback.py
  - backend/src/ai/__init__.py
  - backend/src/services/chat_service.py
  - backend/src/services/conversation_service.py
  - backend/src/services/__init__.py
  - backend/src/api/chat.py
  - backend/src/api/conversations.py
  - backend/src/main.py
  - frontend/src/lib/api.ts
  - frontend/src/components/chat/ChatWindow.tsx
  - frontend/src/components/chat/MessageBubble.tsx
  - frontend/src/components/chat/InputBar.tsx
  - frontend/src/components/chat/FallbackCLI.tsx
  - frontend/src/components/chat/index.ts
  - frontend/src/app/chat/page.tsx
  - backend/tests/unit/test_ai_types.py
  - backend/tests/unit/test_fallback.py
  - backend/tests/conftest.py
tests:
  - backend/tests/unit/test_ai_types.py
  - backend/tests/unit/test_fallback.py
---

## Prompt

# Phase-3: AI-Powered Todo Chatbot (Full Spec & Plan)

User requested implementation of Phase-3 AI-Powered Todo Chatbot including:
- Phase Evolution Declaration
- Dataset format
- JSON Schema for tasks
- Backward execution policy

Requested deliverables:
1. SP.Plan document
2. Tasks breakdown for Phase-3
3. Directory structure (ai/, nlp/, chat/, tests/)
4. JSON schemas for tasks/messages/conversations
5. Chatbot-ready code + configuration

Constraints:
- Maintain backward compatibility with Phase-2
- Implement all MCP tools: add_task, list_tasks, complete_task, delete_task, update_task
- Use OpenAI Agents SDK + MCP server
- Apply confidence scoring: HIGH (>0.8), MEDIUM (0.5-0.8), LOW (<0.5)
- Stateless server with conversation persistence

## Response snapshot

Implemented Phase-3 AI Chat foundation with:

**Backend AI Layer:**
- `AIInterpreter` - OpenAI function calling for NL interpretation
- `CommandExecutor` - Bridge to task service via CRUD operations
- `FallbackHandler` - Confidence-based CLI fallback per Principle X

**Services:**
- `ChatService` - Main orchestration (interpret → execute → respond)
- `ConversationService` - Conversation/message CRUD with user isolation

**API Endpoints:**
- `POST /api/chat/message` - Send message, get AI response
- `POST /api/chat/confirm` - Confirm pending actions
- `GET/POST/PATCH/DELETE /api/conversations` - Conversation CRUD

**Frontend:**
- `ChatWindow` - Main chat interface with conversation list
- `MessageBubble` - Message display with confidence indicators
- `InputBar` - Text input with keyboard shortcuts
- `FallbackCLI` - CLI command display with copy functionality
- Chat page at `/chat` with sidebar navigation

**Tests:**
- Unit tests for AI types and fallback handler
- Test fixtures in conftest.py

## Outcome

- ✅ Impact: Phase-3 foundation complete with full AI interpretation pipeline
- 🧪 Tests: Unit tests for types and fallback handler created
- 📁 Files: 20 files created/modified across backend and frontend
- 🔁 Next prompts: Write integration tests, implement remaining user stories (US2-US6)
- 🧠 Reflection: Followed spec-driven approach, maintained backward compatibility with Phase-2

## Evaluation notes (flywheel)

- Failure modes observed: None - clean implementation following existing patterns
- Graders run and results (PASS/FAIL): Manual review PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add integration tests for chat flow
