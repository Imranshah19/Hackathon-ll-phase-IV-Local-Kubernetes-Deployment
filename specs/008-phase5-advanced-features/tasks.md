# Tasks: Phase 5 Advanced Features

**Input**: Design documents from `/specs/008-phase5-advanced-features/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/phase5-api.yaml
**Branch**: `008-phase5-advanced-features`
**Date**: 2026-01-28

**Tests**: TDD is required per Constitution (Principle III). Contract tests for new APIs, integration tests for user stories.

**Organization**: Tasks grouped by user story (8 stories: 3×P1, 3×P2, 2×P3) to enable independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1-US8)
- Paths: `backend/src/`, `frontend/src/` (web app structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and base configuration

- [ ] T001 Install Phase 5 backend dependencies (APScheduler, python-dateutil, dapr-client) in backend/pyproject.toml
- [ ] T002 [P] Install Phase 5 frontend dependencies (date-fns) in frontend/package.json
- [ ] T003 [P] Create Dapr components directory at dapr/components/
- [ ] T004 [P] Create events module directory at backend/src/events/__init__.py
- [ ] T005 Create database migration for Phase 5 schema in backend/alembic/versions/phase5_advanced_features.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Extend Task model with priority field (default=3) in backend/src/models/task.py
- [ ] T007 [P] Create Tag model in backend/src/models/tag.py
- [ ] T008 [P] Create TaskTag junction model in backend/src/models/task_tag.py
- [ ] T009 [P] Create RecurrenceRule model in backend/src/models/recurrence.py
- [ ] T010 [P] Create Reminder model in backend/src/models/reminder.py
- [ ] T011 [P] Create TaskEvent model in backend/src/models/task_event.py
- [ ] T012 Update backend/src/models/__init__.py to export all new models
- [ ] T013 [P] Create event schema definitions (CloudEvents format) in backend/src/events/schemas.py
- [ ] T014 [P] Create Dapr pub/sub publisher client in backend/src/events/publisher.py
- [ ] T015 [P] Create Prometheus metrics endpoint in backend/src/api/metrics.py
- [ ] T016 [P] Configure structured JSON logging in backend/src/config/logging.py
- [ ] T017 Register metrics endpoint in backend/src/main.py

**Checkpoint**: Foundation ready - all models exist, event infrastructure configured

---

## Phase 3: User Story 1 - Task Priority Management (Priority: P1) 🎯 MVP

**Goal**: Users can assign, update, and filter tasks by priority levels (Critical/High/Medium/Low/None)

**Independent Test**: Create tasks with different priorities, verify visual indicators and filtering

### Tests for User Story 1

- [ ] T018 [P] [US1] Contract test for priority in task creation in backend/tests/contract/test_task_priority.py
- [ ] T019 [P] [US1] Contract test for priority filtering in backend/tests/contract/test_task_filters.py

### Implementation for User Story 1

- [ ] T020 [US1] Update CreateTaskRequest schema with priority field in backend/src/api/tasks.py
- [ ] T021 [US1] Update task list endpoint with priority filter param in backend/src/api/tasks.py
- [ ] T022 [US1] Update task list endpoint with sort_by=priority in backend/src/api/tasks.py
- [ ] T023 [P] [US1] Create PriorityPicker component in frontend/src/components/PriorityPicker.tsx
- [ ] T024 [US1] Integrate PriorityPicker in TaskForm in frontend/src/components/TaskForm.tsx
- [ ] T025 [US1] Add priority visual indicators (colors) in frontend/src/components/TaskItem.tsx
- [ ] T026 [US1] Add priority filter dropdown in frontend/src/components/TaskFilters.tsx

**Checkpoint**: User Story 1 complete - priority management works independently

---

## Phase 4: User Story 2 - Task Tags and Categorization (Priority: P1)

**Goal**: Users can create tags, assign to tasks, and filter by tags

**Independent Test**: Create tags, add to tasks, filter by tag to verify only matching tasks appear

### Tests for User Story 2

- [ ] T027 [P] [US2] Contract test for tag CRUD in backend/tests/contract/test_tags.py
- [ ] T028 [P] [US2] Integration test for task-tag association in backend/tests/integration/test_tags.py

### Implementation for User Story 2

- [ ] T029 [US2] Create TagService with CRUD and count logic in backend/src/services/tag_service.py
- [ ] T030 [US2] Create tag API endpoints (list, create, update, delete, suggest) in backend/src/api/tags.py
- [ ] T031 [US2] Register tag router in backend/src/main.py
- [ ] T032 [US2] Update task creation/update to handle tag_ids in backend/src/api/tasks.py
- [ ] T033 [US2] Update task list endpoint with tags filter param in backend/src/api/tasks.py
- [ ] T034 [P] [US2] Create TagManager component in frontend/src/components/TagManager.tsx
- [ ] T035 [P] [US2] Create TagPicker component (with autocomplete) in frontend/src/components/TagPicker.tsx
- [ ] T036 [US2] Integrate TagPicker in TaskForm in frontend/src/components/TaskForm.tsx
- [ ] T037 [US2] Display tags on TaskItem in frontend/src/components/TaskItem.tsx
- [ ] T038 [US2] Add tag filter in TaskFilters in frontend/src/components/TaskFilters.tsx

**Checkpoint**: User Story 2 complete - tags work independently

---

## Phase 5: User Story 3 - Task Filtering and Sorting (Priority: P1)

**Goal**: Users can filter by status, priority, due date, tags, search; sort by various fields

**Independent Test**: Create multiple tasks, apply filters/sorts, verify correct results

### Tests for User Story 3

- [ ] T039 [P] [US3] Contract test for combined filters in backend/tests/contract/test_task_filters.py
- [ ] T040 [P] [US3] Contract test for sort options in backend/tests/contract/test_task_sorting.py

### Implementation for User Story 3

- [ ] T041 [US3] Implement due_from/due_to date range filter in backend/src/api/tasks.py
- [ ] T042 [US3] Implement search text filter (title/description) in backend/src/api/tasks.py
- [ ] T043 [US3] Implement combined filter logic with AND semantics in backend/src/api/tasks.py
- [ ] T044 [US3] Implement sort_order (asc/desc) for all sort_by options in backend/src/api/tasks.py
- [ ] T045 [US3] Add database indexes for filter performance in backend/alembic/versions/phase5_indexes.py
- [ ] T046 [US3] Update TaskFilters with date range picker in frontend/src/components/TaskFilters.tsx
- [ ] T047 [US3] Add search input to TaskFilters in frontend/src/components/TaskFilters.tsx
- [ ] T048 [US3] Add sort dropdown (field + direction) in frontend/src/components/TaskFilters.tsx
- [ ] T049 [US3] Persist filter/sort state in session storage in frontend/src/app/tasks/page.tsx

**Checkpoint**: User Story 3 complete - full filtering/sorting works independently

---

## Phase 6: User Story 4 - Recurring Tasks (Priority: P2)

**Goal**: Users can create recurring tasks that regenerate on completion

**Independent Test**: Create daily recurring task, complete it, verify new instance created

### Tests for User Story 4

- [ ] T050 [P] [US4] Unit test for RRULE next occurrence calculation in backend/tests/unit/test_recurrence.py
- [ ] T051 [P] [US4] Integration test for recurring task completion in backend/tests/integration/test_recurrence.py

### Implementation for User Story 4

- [ ] T052 [US4] Create RecurrenceService with next occurrence logic in backend/src/services/recurrence_service.py
- [ ] T053 [US4] Extend Task model with recurrence_rule_id and parent_task_id in backend/src/models/task.py
- [ ] T054 [US4] Update CreateTaskRequest with optional recurrence field in backend/src/api/tasks.py
- [ ] T055 [US4] Update complete endpoint to generate next instance in backend/src/api/tasks.py
- [ ] T056 [US4] Update delete endpoint with delete_series option in backend/src/api/tasks.py
- [ ] T057 [US4] Update UpdateTaskRequest with update_series option in backend/src/api/tasks.py
- [ ] T058 [P] [US4] Create RecurrencePicker component in frontend/src/components/RecurrencePicker.tsx
- [ ] T059 [US4] Integrate RecurrencePicker in TaskForm in frontend/src/components/TaskForm.tsx
- [ ] T060 [US4] Show recurrence indicator on TaskItem in frontend/src/components/TaskItem.tsx
- [ ] T061 [US4] Handle complete response with next_instance in frontend/src/components/TaskItem.tsx

**Checkpoint**: User Story 4 complete - recurring tasks work independently

---

## Phase 7: User Story 5 - Task Reminders (Priority: P2)

**Goal**: Users can set reminders and receive web notifications

**Independent Test**: Set reminder for near-future time, verify notification triggers

### Tests for User Story 5

- [ ] T062 [P] [US5] Contract test for reminder CRUD in backend/tests/contract/test_reminders.py
- [ ] T063 [P] [US5] Integration test for reminder delivery in backend/tests/integration/test_reminders.py

### Implementation for User Story 5

- [ ] T064 [US5] Create ReminderService with scheduling logic in backend/src/services/reminder_service.py
- [ ] T065 [US5] Configure APScheduler with PostgreSQL job store in backend/src/config/scheduler.py
- [ ] T066 [US5] Create reminder API endpoints (list, create, delete) in backend/src/api/reminders.py
- [ ] T067 [US5] Create SSE stream endpoint for notifications in backend/src/api/reminders.py
- [ ] T068 [US5] Register reminder router in backend/src/main.py
- [ ] T069 [US5] Implement auto-cancel on task completion in backend/src/api/tasks.py
- [ ] T070 [P] [US5] Create ReminderPicker component in frontend/src/components/ReminderPicker.tsx
- [ ] T071 [US5] Integrate ReminderPicker in TaskForm in frontend/src/components/TaskForm.tsx
- [ ] T072 [US5] Create NotificationProvider with SSE connection in frontend/src/components/NotificationProvider.tsx
- [ ] T073 [US5] Display reminder indicators on TaskItem in frontend/src/components/TaskItem.tsx

**Checkpoint**: User Story 5 complete - reminders work independently

---

## Phase 8: User Story 6 - Bilingual Chatbot (Priority: P2)

**Goal**: Chatbot understands Urdu commands and responds in detected language

**Independent Test**: Send Urdu command, verify task created with Urdu response

### Tests for User Story 6

- [ ] T074 [P] [US6] Unit test for language detection in backend/tests/unit/test_urdu_nlp.py
- [ ] T075 [P] [US6] Integration test for Urdu task creation in backend/tests/integration/test_urdu_chat.py

### Implementation for User Story 6

- [ ] T076 [US6] Create language detection utility (Unicode script) in backend/src/ai/language.py
- [ ] T077 [US6] Create Urdu intent patterns in backend/src/ai/prompts/urdu.py
- [ ] T078 [US6] Create Urdu response templates in backend/src/ai/prompts/urdu.py
- [ ] T079 [US6] Extend interpreter with Urdu pattern matching in backend/src/ai/interpreter.py
- [ ] T080 [US6] Update chat endpoint to detect and respond in language in backend/src/api/chat.py
- [ ] T081 [US6] Add language field to chat response schema in backend/src/api/chat.py
- [ ] T082 [US6] Update ChatWindow to display RTL text for Urdu in frontend/src/components/chat/ChatWindow.tsx
- [ ] T083 [US6] Add Urdu font support in frontend/src/app/layout.tsx

**Checkpoint**: User Story 6 complete - Urdu chatbot works independently

---

## Phase 9: User Story 7 - Event-Driven Task Updates (Priority: P3)

**Goal**: Task events published to Kafka via Dapr for async processing

**Independent Test**: Create/update task, verify event appears in message broker

### Tests for User Story 7

- [ ] T084 [P] [US7] Integration test for event publishing in backend/tests/integration/test_events.py
- [ ] T085 [P] [US7] Unit test for event schema validation in backend/tests/unit/test_event_schemas.py

### Implementation for User Story 7

- [ ] T086 [US7] Create Dapr pub/sub component config in dapr/components/pubsub.yaml
- [ ] T087 [US7] Implement EventPublisher.publish() method in backend/src/events/publisher.py
- [ ] T088 [US7] Create TaskEventService for event creation/retry in backend/src/services/event_service.py
- [ ] T089 [US7] Hook event publishing into task create in backend/src/api/tasks.py
- [ ] T090 [US7] Hook event publishing into task update in backend/src/api/tasks.py
- [ ] T091 [US7] Hook event publishing into task complete in backend/src/api/tasks.py
- [ ] T092 [US7] Hook event publishing into task delete in backend/src/api/tasks.py
- [ ] T093 [US7] Implement retry logic for failed publishes in backend/src/events/publisher.py
- [ ] T094 [US7] Create scheduled job for event cleanup (7-day retention) in backend/src/services/event_service.py

**Checkpoint**: User Story 7 complete - events publish independently

---

## Phase 10: User Story 8 - Production Cloud Deployment (Priority: P3)

**Goal**: Application deployed to DigitalOcean Kubernetes with CI/CD

**Independent Test**: Deploy to DOKS, verify all features work via public URL

### Tests for User Story 8

- [ ] T095 [P] [US8] Smoke test script for deployed environment in scripts/smoke-test.sh

### Implementation for User Story 8

- [ ] T096 [US8] Create Dapr component for Kafka in helm/todo-app/templates/dapr-components.yaml
- [ ] T097 [US8] Update Helm values with Dapr sidecar injection in helm/todo-app/values.yaml
- [ ] T098 [US8] Create values-production.yaml for DOKS in helm/todo-app/values-production.yaml
- [ ] T099 [US8] Create GitHub Actions workflow for DOKS deploy in .github/workflows/deploy-doks.yaml
- [ ] T100 [US8] Configure DO Container Registry secrets in .github/workflows/deploy-doks.yaml
- [ ] T101 [US8] Add health check enhancements for Dapr readiness in backend/src/api/health.py
- [ ] T102 [US8] Create deployment documentation in docs/deployment-doks.md
- [ ] T103 [US8] Run end-to-end validation on deployed cluster

**Checkpoint**: User Story 8 complete - production deployment works

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final quality improvements across all stories

- [ ] T104 [P] Update API documentation with Phase 5 endpoints in backend/src/main.py (OpenAPI)
- [ ] T105 [P] Add error handling for all new endpoints in backend/src/api/
- [ ] T106 [P] Add request logging middleware enhancement in backend/src/middleware/logging.py
- [ ] T107 Run quickstart.md validation scenarios
- [ ] T108 Performance test filter queries with 1000 tasks
- [ ] T109 Security review: verify user isolation on all new endpoints
- [ ] T110 Update project README with Phase 5 features

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ──► Phase 2 (Foundational) ──┬──► Phase 3 (US1: Priority) 🎯 MVP
                                              ├──► Phase 4 (US2: Tags)
                                              ├──► Phase 5 (US3: Filters)
                                              ├──► Phase 6 (US4: Recurring)
                                              ├──► Phase 7 (US5: Reminders)
                                              ├──► Phase 8 (US6: Urdu)
                                              ├──► Phase 9 (US7: Events)
                                              └──► Phase 10 (US8: Deploy)
                                                            │
                                              Phase 11 (Polish) ◄──────────┘
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (Priority) | Phase 2 only | US2, US3, US4, US5, US6, US7 |
| US2 (Tags) | Phase 2 only | US1, US3, US4, US5, US6, US7 |
| US3 (Filters) | US1, US2 (for priority/tag filters) | US4, US5, US6, US7 |
| US4 (Recurring) | Phase 2 only | US1, US2, US5, US6, US7 |
| US5 (Reminders) | Phase 2 only | US1, US2, US4, US6, US7 |
| US6 (Urdu) | Phase 2 only | US1, US2, US4, US5, US7 |
| US7 (Events) | Phase 2 only | US1, US2, US4, US5, US6 |
| US8 (Deploy) | US1-US7 should be stable | None (final) |

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Backend models/services before endpoints
3. Endpoints before frontend components
4. Core implementation before integration

---

## Parallel Opportunities

### Phase 2 (Foundational) - 7 parallel tasks:
```bash
# Launch all model creations together:
T007: Create Tag model
T008: Create TaskTag model
T009: Create RecurrenceRule model
T010: Create Reminder model
T011: Create TaskEvent model
T013: Create event schemas
T014: Create Dapr publisher
T015: Create metrics endpoint
T016: Configure logging
```

### User Stories - All P1 stories can run in parallel:
```bash
# Three P1 stories can start simultaneously after Phase 2:
Developer A: US1 (Priority) - T018-T026
Developer B: US2 (Tags) - T027-T038
Developer C: US3 (Filters) - T039-T049
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T017)
3. Complete Phase 3: User Story 1 - Priority (T018-T026)
4. **STOP and VALIDATE**: Test priority independently
5. Deploy/demo - MVP complete with priority management

### Incremental Delivery (P1 Stories)

1. Setup + Foundational → Foundation ready
2. Add US1 (Priority) → Test → Deploy (MVP!)
3. Add US2 (Tags) → Test → Deploy
4. Add US3 (Filters) → Test → Deploy
5. P1 features complete - core task management enhanced

### Full Feature Delivery

1. Complete P1 stories (US1-US3)
2. Add P2 stories in parallel (US4, US5, US6)
3. Add P3 stories (US7, US8)
4. Polish phase
5. Production deployment validated

---

## Task Summary

| Phase | Story | Tasks | Parallel |
|-------|-------|-------|----------|
| 1 | Setup | 5 | 3 |
| 2 | Foundational | 12 | 9 |
| 3 | US1 Priority | 9 | 3 |
| 4 | US2 Tags | 12 | 4 |
| 5 | US3 Filters | 11 | 2 |
| 6 | US4 Recurring | 12 | 3 |
| 7 | US5 Reminders | 12 | 3 |
| 8 | US6 Urdu | 10 | 2 |
| 9 | US7 Events | 11 | 2 |
| 10 | US8 Deploy | 9 | 1 |
| 11 | Polish | 7 | 3 |
| **Total** | | **110** | **35** |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to user story for traceability
- Each user story is independently testable after completion
- Constitution Principle III (TDD) enforced: tests before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
