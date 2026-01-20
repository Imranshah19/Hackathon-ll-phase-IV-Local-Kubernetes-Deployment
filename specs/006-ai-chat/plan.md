# Implementation Plan: Phase 3 AI Chat

**Branch**: `006-ai-chat` | **Date**: 2026-01-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-ai-chat/spec.md`

## Summary

Enable natural language task management through an AI-powered chat interface that interprets user commands and executes them via the existing Bonsai CLI. The AI layer acts as an interpreter only, maintaining backward compatibility with Phase 2 CLI commands while providing a conversational user experience.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, OpenAI Agents SDK, MCP SDK, SQLModel, Next.js
**Storage**: PostgreSQL (Neon Serverless) for tasks, conversations, messages
**Testing**: pytest (backend), Jest/Vitest (frontend)
**Target Platform**: Web application (browser) + optional console interface
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 3-second response time, 90% interpretation accuracy
**Constraints**: 5-second AI timeout, stateless chat layer, Phase 2 CLI compatibility
**Scale/Scope**: Multi-user with complete data isolation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-First Development | PASS | spec.md created and validated before planning |
| II. Layered Architecture | PASS | AI layer → API → CLI → Database separation maintained |
| III. Test-First Development | PENDING | Tests will be written first during implementation |
| IV. Secure by Design | PASS | User isolation (FR-013), JWT auth reused from Phase 2 |
| V. API-First Integration | PASS | REST contracts defined in contracts/ directory |
| VI. Minimal Viable Diff | PASS | Reuses Phase 2 Bonsai CLI, adds only AI interpretation layer |
| VII. AI as Interpreter | PASS | AI generates commands, Bonsai CLI executes (FR-004) |
| VIII. Backward Compatibility | PASS | Phase 2 CLI remains functional (FR-012) |
| IX. Intent Preservation | PASS | Clarification for ambiguous inputs (FR-007, FR-014) |
| X. Graceful AI Degradation | PASS | 5-second timeout with CLI fallback (FR-008, FR-011) |

**Gate Result**: PASS - All principles satisfied or have clear implementation path.

## Project Structure

### Documentation (this feature)

```text
specs/006-ai-chat/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Technology decisions
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Developer setup guide
├── contracts/           # Phase 1: API contracts
│   ├── chat-api.yaml    # Chat endpoint OpenAPI spec
│   └── websocket.md     # Real-time messaging protocol
└── checklists/
    └── requirements.md  # Spec quality validation
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── task.py           # Existing Phase 2 model
│   │   ├── conversation.py   # NEW: Conversation entity
│   │   └── message.py        # NEW: Message entity
│   ├── services/
│   │   ├── task_service.py   # Existing Phase 2 service
│   │   └── chat_service.py   # NEW: Chat orchestration
│   ├── api/
│   │   ├── tasks.py          # Existing Phase 2 endpoints
│   │   └── chat.py           # NEW: Chat API endpoints
│   ├── ai/                   # NEW: AI integration layer
│   │   ├── __init__.py
│   │   ├── interpreter.py    # NLP intent extraction
│   │   ├── plan_generator.py # SP.Plan generation
│   │   ├── executor.py       # Bonsai CLI bridge
│   │   └── prompts/
│   │       ├── intent.py     # Intent extraction prompts
│   │       └── response.py   # Response generation prompts
│   └── cli/                  # Existing Phase 2 CLI
│       ├── add.py
│       ├── list.py
│       ├── update.py
│       ├── delete.py
│       └── complete.py
└── tests/
    ├── contract/
    │   └── test_chat_api.py  # NEW: Chat API contract tests
    ├── integration/
    │   └── test_chat_flow.py # NEW: End-to-end chat tests
    ├── unit/
    │   ├── test_interpreter.py   # NEW: NLP interpretation tests
    │   └── test_plan_generator.py # NEW: Plan generation tests
    └── ai/
        └── test_intent_accuracy.py # NEW: Intent accuracy benchmarks

frontend/
├── src/
│   ├── app/
│   │   └── chat/
│   │       └── page.tsx      # NEW: Chat page
│   ├── components/
│   │   └── chat/             # NEW: Chat UI components
│   │       ├── ChatWindow.tsx
│   │       ├── MessageBubble.tsx
│   │       ├── InputBar.tsx
│   │       └── FallbackCLI.tsx
│   └── services/
│       └── chat-api.ts       # NEW: Chat API client
└── tests/
    ├── component/
    │   └── chat/
    │       └── ChatWindow.test.tsx
    └── e2e/
        └── chat-flow.spec.ts
```

**Structure Decision**: Web application structure (Option 2) selected. Phase 3 extends the existing backend/frontend structure from Phase 2, adding AI-specific modules in `backend/src/ai/` and chat components in `frontend/src/components/chat/`.

## Complexity Tracking

> No Constitution Check violations requiring justification.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| AI Provider Abstraction | Single provider initially | OpenAI/Claude API with fallback; abstraction layer can be added later if needed (YAGNI) |
| Real-time vs Polling | HTTP polling initially | WebSocket complexity deferred; 3-second response target achievable with polling |
| Conversation Storage | Same DB as tasks | Leverages existing PostgreSQL setup; no new infrastructure needed |
