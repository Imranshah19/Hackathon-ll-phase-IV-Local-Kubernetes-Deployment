<!--
Sync Impact Report
==================
Version change: 2.0.0 → 2.1.0 (Technology stack refinement)
Modified principles: none
Modified sections:
  - Phase 1: Simplified execution constraints
  - Phase 2: Clarified as "Full-Stack Web App"
  - Phase 3: Added stateless AI Chat Layer note, refined architecture
  - Technology Stack: Added OpenAI Agents SDK, MCP Server, OpenAI ChatKit
  - Dataset Schema: Normalized to 3 tables (tasks, conversations, messages)
  - Architecture: Added NLP Interpreter as explicit step
Added sections: none
Removed sections: none
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ compatible
  - .specify/templates/spec-template.md ✅ compatible
  - .specify/templates/tasks-template.md ✅ compatible
Follow-up TODOs: none
-->

# Todo App Constitution — Hackathon II Evolution

**Project**: AI-Powered Todo Chatbot
**Mode**: Spec-Driven Development (SDD)
**Tech Modes**: CLI + Web + AI Chat
**Phases**: 1 → 2 → 3
**Goal**: Build Todo App starting from console, evolve to AI-powered Chatbot

---

## Phase Evolution Model

### Phase 1: In-Memory Console App

**Objective**: Define project Constitution, create SP.Plan and SP.Task specs, establish rules and validation.

| Deliverable | Description |
|-------------|-------------|
| Constitution.md | Project principles and governance |
| SP.Plan template | Planning workflow specification |
| SP.Task template | Task execution specification |

**Execution Constraints**:
- Local console test only
- No DB, no AI

---

### Phase 2: Full-Stack Web App with Bonsai CLI

**Objective**: CRUD todos via CLI, persistent storage using JSON or DB, SP.Plan execution validation.

| Deliverable | Description |
|-------------|-------------|
| Bonsai CLI | Commands for add, update, delete, list |
| Dataset scripts | JSON or DB persistence |
| Updated Constitution | Spec compliance verified |

**Execution Rules**:
1. Bonsai CLI is the authoritative execution engine
2. User triggers commands manually
3. SP.Plan converted to Bonsai commands

**Example Commands**:
```bash
bonsai add --title "Buy milk" --due "tomorrow"
bonsai list --status pending
bonsai update --id 3 --title "Call mom tonight"
bonsai delete --id 2
```

---

### Phase 3: AI-Powered Chatbot

**Objective**: AI interprets natural language commands, generates SP.Plan → Bonsai CLI executes, maintains backward compatibility with Phase 2 CLI.

| Deliverable | Description |
|-------------|-------------|
| AI Chat Layer | Stateless console or web interface |
| NLP Interpreter | Natural language to intent parsing |
| SP.Plan Generator | Intent to structured plan conversion |
| Bonsai CLI Executor | Plan to CLI command execution (Phase 2 reuse) |
| Dataset Updater | State persistence and sync |

**Execution Flow**:
```text
1. Receive user message
2. NLP interprets command → SP.Plan
3. Validate against Constitution
4. SP.Task created
5. Bonsai CLI executes task
6. Dataset updated
7. Response returned to user
```

**Architecture**:
```text
User → AI Chat Layer → NLP Interpreter → SP.Plan Generator
    → Constitution Validation → SP.Task Builder → Bonsai CLI
    → Dataset → Response → User
```

**Example Natural Language Commands**:
| User Says | Bonsai Command Generated |
|-----------|-------------------------|
| "Add a todo for tomorrow: Buy groceries" | `bonsai add --title "Buy groceries" --due "tomorrow"` |
| "Show my pending tasks" | `bonsai list --status pending` |
| "Mark task 3 as complete" | `bonsai complete --id 3` |
| "Delete the meeting task" | `bonsai delete --id 5` |
| "Update task 1 to 'Call mom tonight'" | `bonsai update --id 1 --title "Call mom tonight"` |

**Critical Notes**:
- Phase 3 reuses Phase 2 Bonsai CLI as execution engine
- AI automation layer only interprets commands; does NOT replace CLI
- Natural language → SP.Plan → Bonsai ensures Phase 2 backward compatibility

---

## Core Principles

### I. Spec-First Development

All implementation MUST be preceded by specification artifacts. Code generation occurs exclusively through Spec-Kit + Claude Code tooling.

- Specifications MUST exist before any code is written
- Manual coding is prohibited; all code is generated from specs
- Changes to implementation require corresponding spec updates
- Spec artifacts include: spec.md, plan.md, tasks.md, contracts/

**Rationale**: Ensures traceability, consistency, and enables AI-assisted development while maintaining architectural integrity.

### II. Layered Architecture

The system MUST maintain clean separation between architectural layers with no cross-layer dependencies that bypass interfaces.

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| Presentation | Next.js (App Router) | Web UI, user interaction |
| Application | FastAPI | Business logic, API endpoints |
| Data | PostgreSQL (Neon Serverless) | Persistence via SQLModel ORM |
| Auth | Better Auth + JWT | Authentication, authorization |

- Each layer communicates only through defined interfaces (REST API)
- Frontend MUST NOT directly access database
- Backend MUST be stateless; session state lives in JWT tokens
- ORM layer abstracts all database operations

**Rationale**: Enables independent scaling, testing, and replacement of components.

### III. Test-First Development (NON-NEGOTIABLE)

All features MUST follow Test-Driven Development (TDD) methodology.

- Tests are written FIRST and MUST fail before implementation
- Red-Green-Refactor cycle is strictly enforced
- Contract tests validate API boundaries
- Integration tests verify cross-layer communication
- No code merges without passing test suite

**Rationale**: Ensures correctness, provides living documentation, and enables safe refactoring.

### IV. Secure by Design

Security MUST be built into every layer, not added as an afterthought.

- JWT-based authentication for all protected endpoints
- Multi-user task isolation: users MUST NOT access other users' data
- Secrets and tokens stored in environment variables (`.env`), never hardcoded
- All inputs validated and sanitized at API boundaries
- HTTPS required for all production traffic

**Rationale**: Protects user data and ensures compliance with security best practices.

### V. API-First Integration

REST API contracts define all communication between frontend and backend.

- OpenAPI/Swagger specifications document all endpoints
- Contracts are versioned and backward-compatible where possible
- Breaking changes require major version bumps and migration plans
- Error responses follow consistent taxonomy with proper HTTP status codes

**Rationale**: Enables parallel frontend/backend development and clear interface boundaries.

### VI. Minimal Viable Diff

Every change MUST be the smallest possible modification to achieve the goal.

- No speculative features (YAGNI principle)
- No refactoring of unrelated code
- One concern per commit
- Complexity MUST be justified in plan.md if Constitution Check is violated

**Rationale**: Reduces risk, simplifies reviews, and maintains focus on delivery.

### VII. AI as Interpreter, Not Executor

The AI Chat Layer MUST only interpret natural language and generate SP.Plans. Execution authority remains with the Bonsai CLI.

- AI MUST NOT directly modify data or state
- All AI outputs MUST be validated against Constitution rules before execution
- AI interpretation failures MUST NOT corrupt dataset
- AI MUST preserve user intent without hallucinating commands
- Fallback to manual CLI input MUST always be available

**Rationale**: Ensures auditability, maintains single execution path, and prevents AI-induced data corruption.

### VIII. Backward Compatibility Across Phases

Each phase MUST maintain compatibility with all prior phases.

- Phase 3 MUST work with Phase 2 Bonsai CLI without modification
- Phase 2 CLI commands MUST remain valid entry points
- Dataset format MUST be consistent across phases
- API contracts established in Phase 2 MUST NOT break in Phase 3
- Users can bypass AI and use CLI directly at any time

**Rationale**: Protects user investment, enables gradual adoption, and simplifies testing.

### IX. Intent Preservation

Natural language interpretation MUST preserve user intent with high fidelity.

- Ambiguous inputs MUST prompt for clarification, not guess
- Command generation MUST be deterministic for identical inputs
- AI MUST NOT add, modify, or remove parameters not specified by user
- Interpretation confidence MUST be logged for debugging
- Low-confidence interpretations MUST request confirmation

**Rationale**: Prevents user frustration and ensures AI assistance enhances rather than hinders productivity.

### X. Graceful AI Degradation

AI features MUST NOT block core functionality when unavailable.

- If AI service is down, system MUST fall back to CLI mode
- If NLP interpretation fails, user MUST receive clear error with CLI alternative
- Timeout on AI operations: 5 seconds maximum before fallback
- All AI failures MUST be logged with context for debugging
- Core CRUD operations MUST work without any AI dependency

**Rationale**: Ensures system reliability and user productivity regardless of AI service status.

## Technology Stack

### Core Stack (Phases 1-3)

| Component | Technology | Version/Notes |
|-----------|------------|---------------|
| Frontend Framework | Next.js / OpenAI ChatKit | App Router or console UI |
| Backend Framework | FastAPI | Python async API |
| Database | PostgreSQL | Neon Serverless or JSON |
| ORM | SQLModel | Type-safe Python ORM |
| Authentication | Better Auth | JWT token-based |
| API Protocol | REST | JSON payloads |
| Testing (Backend) | pytest | Contract + Integration tests |
| Testing (Frontend) | Jest/Vitest | Component + E2E tests |

### Phase 3 AI Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| AI Provider | Claude API / OpenAI | Natural language understanding |
| Agents Framework | OpenAI Agents SDK | Agent orchestration and tools |
| MCP Server | Official MCP SDK | Model Context Protocol integration |
| NLP Interpreter | Custom + LLM | Intent extraction and slot filling |
| SP.Plan Generator | Template engine | Structured plan generation |
| Bonsai CLI | Python Click | Command execution engine (Phase 2 reuse) |
| Conversation Store | JSON/PostgreSQL | Chat history persistence |

### Project Structure

```text
backend/
├── src/
│   ├── models/       # SQLModel entities
│   ├── services/     # Business logic
│   ├── api/          # FastAPI routes
│   ├── auth/         # JWT/Better Auth integration
│   ├── ai/           # Phase 3: AI integration layer
│   │   ├── chat.py           # AI Chat handler
│   │   ├── interpreter.py    # NLP intent extraction
│   │   ├── plan_generator.py # SP.Plan generation
│   │   └── prompts/          # LLM prompt templates
│   └── cli/          # Bonsai CLI commands
│       ├── add.py
│       ├── list.py
│       ├── update.py
│       ├── delete.py
│       └── complete.py
└── tests/
    ├── contract/     # API contract tests
    ├── integration/  # Cross-layer tests
    ├── unit/         # Isolated unit tests
    └── ai/           # AI interpretation tests

frontend/
├── src/
│   ├── app/          # Next.js App Router pages
│   ├── components/   # React components
│   │   └── chat/     # Phase 3: Chat UI components
│   └── services/     # API client services
└── tests/
    ├── component/    # Component tests
    └── e2e/          # End-to-end tests
```

## Development Workflow

### Spec-to-Implementation Flow

1. **Specify** (`/sp.specify`): Define feature requirements in spec.md
2. **Plan** (`/sp.plan`): Create architectural plan in plan.md
3. **Tasks** (`/sp.tasks`): Generate implementation tasks in tasks.md
4. **Implement** (`/sp.implement`): Execute tasks following TDD

### Quality Gates

- [ ] Spec.md exists and is approved
- [ ] Plan.md passes Constitution Check
- [ ] Tasks.md generated from plan
- [ ] Tests written and failing (Red)
- [ ] Implementation makes tests pass (Green)
- [ ] Code refactored if needed (Refactor)
- [ ] All tests pass in CI

### Branching Strategy

- `main`: Production-ready code only
- `feature/<name>`: Feature development branches
- All changes via Pull Request with passing tests

## Governance

This Constitution supersedes all other development practices for this project.

### Amendment Procedure

1. Propose change via Pull Request to constitution.md
2. Document rationale and impact assessment
3. Update version following semantic versioning:
   - **MAJOR**: Principle removal or incompatible redefinition
   - **MINOR**: New principle or section added
   - **PATCH**: Clarifications and wording improvements
4. All PRs MUST verify compliance with Constitution principles

### Compliance Review

- Every PR reviewer MUST check Constitution alignment
- Complexity violations MUST be documented in plan.md
- ADRs capture significant architectural decisions

## Bonsai CLI Command Reference

The Bonsai CLI is the authoritative execution engine for all task operations. All AI-generated commands MUST map to these primitives.

### Core Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `add` | `bonsai add --title "<title>" [--due "<date>"] [--priority <1-5>]` | Create new task |
| `list` | `bonsai list [--status <pending\|completed\|all>] [--due <today\|week>]` | List tasks |
| `update` | `bonsai update --id <id> [--title "<title>"] [--due "<date>"]` | Modify task |
| `delete` | `bonsai delete --id <id>` | Remove task |
| `complete` | `bonsai complete --id <id>` | Mark task done |

### Dataset Schema

The dataset is normalized into three tables/files for clean separation of concerns.

#### tasks.json (or tasks table)

```json
{
  "id": "uuid",
  "title": "string (required)",
  "description": "string (optional)",
  "status": "pending | completed",
  "due": "ISO 8601 date (optional)",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp",
  "user_id": "uuid (multi-user isolation)"
}
```

#### conversations.json (Phase 3)

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp"
}
```

#### messages.json (Phase 3)

```json
{
  "id": "uuid",
  "conversation_id": "uuid (FK → conversations)",
  "role": "user | assistant",
  "content": "string",
  "timestamp": "ISO 8601",
  "generated_command": "string (optional, for assistant messages)"
}
```

**Version**: 2.1.0 | **Ratified**: 2026-01-12 | **Last Amended**: 2026-01-19
