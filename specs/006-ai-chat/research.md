# Research: Phase 3 AI Chat

**Feature**: 006-ai-chat
**Date**: 2026-01-19
**Status**: Complete

## Research Questions

### RQ-001: AI Provider Selection

**Question**: Which AI provider should be used for natural language interpretation?

**Decision**: OpenAI API with Claude API as secondary option

**Rationale**:
- OpenAI Agents SDK specified in Constitution technology stack
- Well-documented function calling for structured command extraction
- Established patterns for intent recognition and slot filling
- Claude API available as fallback per Constitution principle X

**Alternatives Considered**:
| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| OpenAI only | Mature SDK, good docs | Single point of failure | Need fallback per Constitution |
| Claude only | Strong reasoning | Less structured output tooling | OpenAI Agents SDK in Constitution |
| Local LLM | No API costs, offline | High latency, lower accuracy | Doesn't meet 3s response target |
| Both in parallel | Redundancy | Cost, complexity | YAGNI - sequential fallback sufficient |

---

### RQ-002: Intent Extraction Approach

**Question**: How should natural language be converted to Bonsai CLI commands?

**Decision**: Function calling with structured output schema

**Rationale**:
- OpenAI function calling provides type-safe structured outputs
- Maps directly to Bonsai CLI command schema
- Confidence scores available for low-confidence fallback
- Deterministic for identical inputs (per Constitution IX)

**Implementation Pattern**:
```python
# Intent schema maps to Bonsai CLI commands
intent_schema = {
    "type": "object",
    "properties": {
        "action": {"enum": ["add", "list", "update", "delete", "complete"]},
        "title": {"type": "string"},
        "task_id": {"type": "integer"},
        "due_date": {"type": "string", "format": "date"},
        "status_filter": {"enum": ["pending", "completed", "all"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    }
}
```

**Alternatives Considered**:
| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| Regex parsing | Fast, no API calls | Brittle, limited NL understanding | Fails on varied phrasing |
| Fine-tuned model | High accuracy | Training cost, maintenance | Overkill for 5 command types |
| RAG + embedding | Flexible | Latency, complexity | Function calling simpler |

---

### RQ-003: Conversation State Management

**Question**: How should conversation history be stored and managed?

**Decision**: PostgreSQL tables (conversations, messages) with session-based context window

**Rationale**:
- Reuses existing Neon PostgreSQL infrastructure
- Constitution specifies normalized schema (3 tables)
- Session-based context avoids token bloat
- Easy to query for debugging and analytics

**Context Window Strategy**:
- Include last 10 messages in AI context
- Summarize older messages if session exceeds limit
- Clear context on explicit user request

**Alternatives Considered**:
| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| In-memory only | Fast | Lost on restart | Need persistence (FR-006) |
| Redis | Fast reads | New infrastructure | PostgreSQL sufficient |
| Full history in context | Complete context | Token costs, latency | 10-message window sufficient |

---

### RQ-004: CLI Execution Bridge

**Question**: How should the AI layer invoke Bonsai CLI commands?

**Decision**: Direct Python function calls to CLI service layer

**Rationale**:
- CLI commands are Python Click functions
- Can invoke underlying service functions directly
- Avoids subprocess overhead
- Maintains transaction context

**Implementation Pattern**:
```python
# executor.py bridges AI output to CLI services
class BonsaiExecutor:
    def execute(self, command: InterpretedCommand) -> ExecutionResult:
        if command.action == "add":
            return task_service.create_task(
                title=command.title,
                due=command.due_date,
                user_id=command.user_id
            )
        # ... other actions
```

**Alternatives Considered**:
| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| Subprocess CLI | True CLI parity | Overhead, auth complexity | Service layer cleaner |
| HTTP to own API | Decoupled | Latency, redundant | Already in same process |
| Message queue | Async, scalable | Complexity | YAGNI for hackathon scope |

---

### RQ-005: Fallback and Error Handling

**Question**: How should the system handle AI failures and low-confidence interpretations?

**Decision**: Tiered fallback with CLI command suggestions

**Rationale**:
- Constitution X mandates graceful degradation
- Users need actionable alternatives
- Logging enables debugging and accuracy improvements

**Fallback Tiers**:
1. **High confidence (>0.8)**: Execute immediately
2. **Medium confidence (0.5-0.8)**: Show interpreted command, ask confirmation
3. **Low confidence (<0.5)**: Suggest CLI command, ask for clarification
4. **AI timeout (>5s)**: Return CLI instructions immediately
5. **AI unavailable**: Direct to CLI mode with command examples

**Alternatives Considered**:
| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| Always confirm | Safer | Friction for simple commands | Confidence tiers balance safety/UX |
| Never fallback | Simpler | Constitution violation | Must provide alternatives |
| Retry on failure | May succeed | Delays, costs | 5s timeout is hard limit |

---

### RQ-006: Chat UI Architecture

**Question**: What frontend architecture should be used for the chat interface?

**Decision**: React components with HTTP polling (WebSocket deferred)

**Rationale**:
- Aligns with existing Next.js frontend
- HTTP polling meets 3-second response target
- Simpler implementation for hackathon timeline
- WebSocket can be added later without breaking changes

**Component Structure**:
- `ChatWindow`: Main container with message list
- `MessageBubble`: Individual message display (user/assistant)
- `InputBar`: Text input with send button
- `FallbackCLI`: Shows CLI alternatives when needed

**Alternatives Considered**:
| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| WebSocket | Real-time | Complexity, state management | Polling sufficient for MVP |
| Server-Sent Events | Simple streaming | Browser support varies | HTTP polling more portable |
| Third-party chat widget | Fast integration | Less control, dependencies | Custom UI preferred |

---

## Summary

All research questions resolved. No NEEDS CLARIFICATION items remain.

| RQ | Decision | Key Rationale |
|----|----------|---------------|
| RQ-001 | OpenAI + Claude fallback | Constitution stack + graceful degradation |
| RQ-002 | Function calling | Structured output, confidence scores |
| RQ-003 | PostgreSQL + session context | Reuse infra, 10-message window |
| RQ-004 | Direct service calls | Avoid subprocess overhead |
| RQ-005 | Tiered confidence fallback | Constitution X compliance |
| RQ-006 | React + HTTP polling | MVP simplicity, WebSocket later |
