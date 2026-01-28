# Implementation Plan: Phase 5 Advanced Features

**Branch**: `008-phase5-advanced-features` | **Date**: 2026-01-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-phase5-advanced-features/spec.md`

## Summary

Phase 5 extends the Todo application with advanced task management (priorities, tags, recurring tasks, reminders), event-driven architecture using Kafka/Dapr for scalability, bilingual chatbot support (English/Urdu), and production deployment to DigitalOcean Kubernetes. The approach builds incrementally on Phase 4's containerized architecture while adding new data models, event publishing, and NLP enhancements.

## Technical Context

**Language/Version**: Python 3.11 (Backend), TypeScript/Node 20 (Frontend)
**Primary Dependencies**: FastAPI, SQLModel, Next.js 14, Kafka (via Dapr), OpenAI API
**Storage**: PostgreSQL (Neon Serverless) with new tables for tags, reminders, recurrence rules
**Testing**: pytest (backend), Jest/Vitest (frontend), contract tests for new APIs
**Target Platform**: DigitalOcean Kubernetes (DOKS) with Dapr sidecar injection
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 1000 concurrent users, <1s filter response, <30s reminder delivery
**Constraints**: 7-day event retention, 99.9% uptime, stateless containers
**Scale/Scope**: ~1000 tasks per user, 100 tags max, 3 reminders per task

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-First Development | PASS | spec.md complete with 35 FRs, 10 SCs |
| II. Layered Architecture | PASS | Extends existing layers; no cross-layer violations |
| III. Test-First Development | PASS | TDD required; contract tests for new APIs |
| IV. Secure by Design | PASS | JWT auth preserved; user task isolation maintained |
| V. API-First Integration | PASS | OpenAPI contracts will be generated |
| VI. Minimal Viable Diff | PASS | Builds on Phase 4; no unnecessary refactoring |
| VII. AI as Interpreter | PASS | Urdu support extends NLP; no execution changes |
| VIII. Backward Compatibility | PASS | All existing APIs preserved; additive changes only |
| IX. Intent Preservation | PASS | Urdu commands follow same intent patterns |
| X. Graceful AI Degradation | PASS | CLI fallback preserved; event failures don't block |

**Gate Result**: PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/008-phase5-advanced-features/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── phase5-api.yaml  # OpenAPI spec for new endpoints
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── Dockerfile
├── src/
│   ├── models/
│   │   ├── task.py          # Extended with priority, recurrence
│   │   ├── tag.py           # NEW: Tag entity
│   │   ├── task_tag.py      # NEW: Many-to-many junction
│   │   ├── reminder.py      # NEW: Reminder entity
│   │   ├── recurrence.py    # NEW: RecurrenceRule entity
│   │   └── task_event.py    # NEW: Event audit entity
│   ├── services/
│   │   ├── tag_service.py       # NEW: Tag CRUD
│   │   ├── reminder_service.py  # NEW: Reminder scheduling
│   │   ├── recurrence_service.py # NEW: Recurrence logic
│   │   └── event_publisher.py   # NEW: Kafka/Dapr publisher
│   ├── api/
│   │   ├── tasks.py         # Extended with filter/sort params
│   │   ├── tags.py          # NEW: Tag endpoints
│   │   ├── reminders.py     # NEW: Reminder endpoints
│   │   └── metrics.py       # NEW: Prometheus metrics
│   ├── ai/
│   │   ├── interpreter.py   # Extended with Urdu patterns
│   │   └── prompts/
│   │       └── urdu.py      # NEW: Urdu prompt templates
│   └── events/
│       ├── publisher.py     # NEW: Dapr pub/sub client
│       ├── schemas.py       # NEW: Event payload schemas
│       └── handlers.py      # NEW: Event consumers
└── tests/
    ├── contract/
    │   └── test_phase5_api.py  # NEW: Contract tests
    ├── integration/
    │   ├── test_tags.py        # NEW
    │   ├── test_reminders.py   # NEW
    │   └── test_events.py      # NEW
    └── unit/
        ├── test_recurrence.py  # NEW
        └── test_urdu_nlp.py    # NEW

frontend/
├── Dockerfile
├── src/
│   ├── components/
│   │   ├── TaskFilters.tsx    # Extended with priority/tag filters
│   │   ├── TagManager.tsx     # NEW: Tag CRUD UI
│   │   ├── PriorityPicker.tsx # NEW: Priority selector
│   │   ├── ReminderPicker.tsx # NEW: Reminder UI
│   │   └── RecurrencePicker.tsx # NEW: Recurrence UI
│   └── app/
│       └── tasks/
│           └── page.tsx       # Extended with new filters
└── tests/

# Kubernetes/Dapr Configuration
helm/
└── todo-app/
    ├── values.yaml            # Extended with Dapr config
    └── templates/
        ├── dapr-components.yaml  # NEW: Pub/sub component
        └── kafka-deployment.yaml # NEW: Kafka for local dev

# CI/CD
.github/
└── workflows/
    └── deploy-doks.yaml       # NEW: DigitalOcean deployment
```

**Structure Decision**: Web application structure (Option 2) extended with event-driven components. Backend adds `/events/` directory for Kafka/Dapr integration. Frontend extends existing components with new pickers and filters.

## Complexity Tracking

> No Constitution violations requiring justification.

| Aspect | Complexity | Justification |
|--------|------------|---------------|
| Kafka/Dapr | Moderate | Required for FR-025 event-driven architecture; Dapr simplifies integration |
| Urdu NLP | Moderate | Extends existing interpreter; no new AI system |
| Recurring Tasks | Moderate | Standard RRULE patterns; cron-like scheduling |

---

## Phase 0: Research Complete

See [research.md](./research.md) for detailed findings.

## Phase 1: Design Complete

See:
- [data-model.md](./data-model.md) - Entity definitions
- [contracts/phase5-api.yaml](./contracts/phase5-api.yaml) - OpenAPI specification
- [quickstart.md](./quickstart.md) - Developer setup guide
