# Data Model: Phase 5 Advanced Features

**Feature**: 008-phase5-advanced-features
**Date**: 2026-01-28
**Status**: Complete

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │───────│    Task     │───────│   Reminder  │
└─────────────┘  1:N  └─────────────┘  1:N  └─────────────┘
                            │ 1
                            │
                      ┌─────┴─────┐
                      │           │
                   N:M│        1:1│
                      │           │
               ┌──────▼──────┐    │
               │   TaskTag   │    │
               └──────┬──────┘    │
                      │ N:1       │
                      │           │
               ┌──────▼──────┐    │
               │     Tag     │    │
               └─────────────┘    │
                                  │
                      ┌───────────▼───────────┐
                      │    RecurrenceRule     │
                      └───────────────────────┘

┌─────────────┐
│  TaskEvent  │  (Audit log - independent)
└─────────────┘
```

---

## Entities

### Task (Extended)

Extends existing Task model with Phase 5 fields.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| user_id | UUID | FK → User, NOT NULL | Owner |
| title | VARCHAR(255) | NOT NULL | Task title |
| description | TEXT | NULLABLE | Optional details |
| status | ENUM | NOT NULL, DEFAULT 'pending' | pending, completed |
| due | TIMESTAMP | NULLABLE | Due date/time |
| **priority** | INTEGER | NOT NULL, DEFAULT 3, CHECK 1-5 | NEW: 1=Critical, 5=None |
| **recurrence_rule_id** | UUID | FK → RecurrenceRule, NULLABLE | NEW: Recurrence pattern |
| **parent_task_id** | UUID | FK → Task, NULLABLE | NEW: Parent for recurring instances |
| created_at | TIMESTAMP | NOT NULL | Creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update |

**Indexes**:
- `idx_task_user_status` (user_id, status)
- `idx_task_user_priority` (user_id, priority)
- `idx_task_user_due` (user_id, due)
- `idx_task_parent` (parent_task_id) WHERE parent_task_id IS NOT NULL

**Validation Rules**:
- priority must be 1, 2, 3, 4, or 5
- parent_task_id can only be set if task is instance of recurring
- recurrence_rule_id can only be set on template tasks (parent_task_id IS NULL)

---

### Tag (NEW)

User-defined labels for task categorization.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| user_id | UUID | FK → User, NOT NULL | Owner |
| name | VARCHAR(50) | NOT NULL | Tag name |
| color | VARCHAR(7) | NOT NULL, DEFAULT '#6B7280' | Hex color code |
| created_at | TIMESTAMP | NOT NULL | Creation time |

**Indexes**:
- `idx_tag_user_name` UNIQUE (user_id, name)

**Validation Rules**:
- name: alphanumeric, hyphens, underscores only; 1-50 characters
- color: valid hex color format (#RRGGBB)
- Maximum 100 tags per user

---

### TaskTag (NEW - Junction Table)

Many-to-many relationship between Task and Tag.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| task_id | UUID | PK, FK → Task | Task reference |
| tag_id | UUID | PK, FK → Tag | Tag reference |
| created_at | TIMESTAMP | NOT NULL | When tag was added |

**Indexes**:
- `idx_task_tag_task` (task_id)
- `idx_task_tag_tag` (tag_id)

**Cascade Rules**:
- ON DELETE Task → DELETE TaskTag rows
- ON DELETE Tag → DELETE TaskTag rows (tags removed from tasks)

---

### Reminder (NEW)

Scheduled notifications for tasks.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| task_id | UUID | FK → Task, NOT NULL | Associated task |
| user_id | UUID | FK → User, NOT NULL | Owner (denormalized for queries) |
| remind_at | TIMESTAMP | NOT NULL | When to trigger |
| message | TEXT | NULLABLE | Custom message |
| sent | BOOLEAN | NOT NULL, DEFAULT FALSE | Delivery status |
| sent_at | TIMESTAMP | NULLABLE | When delivered |
| created_at | TIMESTAMP | NOT NULL | Creation time |

**Indexes**:
- `idx_reminder_pending` (remind_at) WHERE sent = FALSE
- `idx_reminder_task` (task_id)

**Validation Rules**:
- remind_at must be in the future at creation time
- Maximum 3 reminders per task

**Cascade Rules**:
- ON DELETE Task → DELETE Reminder rows
- ON Task.status = 'completed' → UPDATE Reminder SET sent = TRUE (auto-cancel)

---

### RecurrenceRule (NEW)

Pattern definition for recurring tasks.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| frequency | ENUM | NOT NULL | daily, weekly, monthly, yearly, custom |
| interval | INTEGER | NOT NULL, DEFAULT 1, CHECK >= 1 | Every N units |
| end_type | ENUM | NOT NULL, DEFAULT 'never' | never, count, date |
| end_count | INTEGER | NULLABLE | Max occurrences (if end_type='count') |
| end_date | DATE | NULLABLE | End date (if end_type='date') |
| rrule_string | TEXT | NULLABLE | Full RRULE for complex patterns |
| created_at | TIMESTAMP | NOT NULL | Creation time |

**Indexes**:
- None (always accessed via Task.recurrence_rule_id)

**Validation Rules**:
- interval must be >= 1
- end_count must be >= 1 if end_type = 'count'
- end_date must be in future if end_type = 'date'

---

### TaskEvent (NEW)

Audit log for event-driven architecture.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Primary key (also CloudEvents ID) |
| event_type | ENUM | NOT NULL | created, updated, completed, deleted |
| task_id | UUID | NOT NULL | Task reference (may be deleted) |
| user_id | UUID | NOT NULL | User reference |
| task_snapshot | JSONB | NOT NULL | Full task state at event time |
| published | BOOLEAN | NOT NULL, DEFAULT FALSE | Sent to broker |
| published_at | TIMESTAMP | NULLABLE | When published |
| created_at | TIMESTAMP | NOT NULL | Event creation time |

**Indexes**:
- `idx_event_unpublished` (created_at) WHERE published = FALSE
- `idx_event_task` (task_id)
- `idx_event_created` (created_at) -- for 7-day retention cleanup

**Retention**:
- Events older than 7 days are deleted by scheduled cleanup job

---

## State Transitions

### Task Status

```
     ┌─────────┐
     │ pending │
     └────┬────┘
          │ complete
          ▼
   ┌──────────────┐
   │  completed   │
   └──────────────┘
```

- pending → completed: via complete action
- No transition back (completed is final)

### Recurring Task Lifecycle

```
┌─────────────────┐
│ Template Task   │ (has recurrence_rule_id)
│ parent_task_id  │ = NULL
└────────┬────────┘
         │ complete
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Completed       │ ──► │ New Instance    │
│ Instance        │     │ (auto-created)  │
└─────────────────┘     └─────────────────┘
                        parent_task_id = template.id
```

### Reminder Lifecycle

```
┌──────────┐     time arrives     ┌──────────┐
│ pending  │ ──────────────────► │  sent    │
│ sent=F   │                      │ sent=T   │
└──────────┘                      └──────────┘
     │
     │ task completed/deleted
     ▼
┌──────────┐
│ cancelled│ (sent=T, sent_at=now)
└──────────┘
```

---

## Migration Strategy

### New Tables
```sql
-- Run in order
1. CREATE TABLE tag (...)
2. CREATE TABLE task_tag (...)
3. CREATE TABLE recurrence_rule (...)
4. CREATE TABLE reminder (...)
5. CREATE TABLE task_event (...)
```

### Task Table Alterations
```sql
ALTER TABLE task ADD COLUMN priority INTEGER NOT NULL DEFAULT 3;
ALTER TABLE task ADD CONSTRAINT chk_priority CHECK (priority BETWEEN 1 AND 5);
ALTER TABLE task ADD COLUMN recurrence_rule_id UUID REFERENCES recurrence_rule(id);
ALTER TABLE task ADD COLUMN parent_task_id UUID REFERENCES task(id);
```

### Backward Compatibility
- All new columns have defaults or are nullable
- Existing tasks get priority=3 (Medium)
- No data migration required for existing records
