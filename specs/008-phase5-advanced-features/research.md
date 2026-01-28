# Research: Phase 5 Advanced Features

**Feature**: 008-phase5-advanced-features
**Date**: 2026-01-28
**Status**: Complete

---

## Research Topics

### 1. Event-Driven Architecture with Dapr

**Decision**: Use Dapr pub/sub component with Kafka as the message broker

**Rationale**:
- Dapr provides a sidecar pattern that abstracts message broker specifics
- Allows switching brokers (Kafka → Redis → RabbitMQ) without code changes
- Built-in retry and dead-letter queue support
- Native Kubernetes integration with automatic sidecar injection
- CloudEvents format ensures interoperability

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| Direct Kafka client (confluent-kafka) | Tight coupling; harder to test locally |
| Redis Pub/Sub | No persistence; messages lost if subscriber offline |
| AWS SQS/SNS | Vendor lock-in; complicates local development |

**Implementation Pattern**:
```python
# Dapr pub/sub via HTTP
POST http://localhost:3500/v1.0/publish/todo-pubsub/task-events
Content-Type: application/cloudevents+json

{
  "specversion": "1.0",
  "type": "todo.task.created",
  "source": "/tasks",
  "id": "uuid",
  "data": { ... }
}
```

---

### 2. Recurring Task Implementation

**Decision**: Use dateutil RRULE with simplified patterns stored as JSON

**Rationale**:
- python-dateutil's rrule is battle-tested and handles edge cases (leap years, DST)
- Storing simplified pattern in JSON allows frontend display without parsing
- Next occurrence calculated on-demand when task completed
- RRULE string stored for complex pattern support in future

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| Cron expressions | Not human-readable; overkill for simple patterns |
| Custom recurrence logic | Error-prone; reinventing the wheel |
| Celery Beat | External dependency; complicates deployment |

**Data Model**:
```python
class RecurrenceRule:
    frequency: str  # "daily", "weekly", "monthly", "yearly", "custom"
    interval: int   # e.g., 2 for "every 2 weeks"
    end_type: str   # "never", "count", "date"
    end_value: Optional[Union[int, date]]  # count or end date
    rrule_str: str  # Full RRULE for complex patterns
```

---

### 3. Reminder Scheduling

**Decision**: Background task scheduler using APScheduler with PostgreSQL job store

**Rationale**:
- APScheduler integrates with FastAPI async
- PostgreSQL job store survives container restarts
- Jobs persist across deployments
- Supports both interval and date-based triggers

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| Celery | Requires Redis/RabbitMQ broker; adds complexity |
| Kubernetes CronJobs | Per-reminder CronJob is not scalable |
| In-memory scheduler | Jobs lost on restart |

**Delivery Mechanism**:
- Web notifications via Server-Sent Events (SSE)
- Fallback: Notification stored for next page load
- No external push notification services (out of scope)

---

### 4. Urdu Language Detection and NLP

**Decision**: Unicode script detection + GPT-4 for intent parsing

**Rationale**:
- Urdu uses Arabic script (Unicode range 0600-06FF)
- Simple regex can detect script with high accuracy
- GPT-4 already handles Urdu; extend system prompts
- No need for separate NLP model

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| langdetect library | Overkill for binary English/Urdu detection |
| Separate Urdu NLP model | Unnecessary; GPT-4 handles it |
| Translation to English | Loses nuance; user expects Urdu response |

**Detection Pattern**:
```python
import re

def detect_language(text: str) -> str:
    urdu_pattern = re.compile(r'[\u0600-\u06FF]')
    if urdu_pattern.search(text):
        return "urdu"
    return "english"
```

**Urdu Intent Patterns**:
| Intent | English Pattern | Urdu Pattern |
|--------|----------------|--------------|
| Add task | "add", "create", "new" | "شامل", "نیا", "بناؤ" |
| List tasks | "show", "list", "display" | "دکھاؤ", "فہرست" |
| Complete | "complete", "done", "finish" | "مکمل", "ختم" |
| Delete | "delete", "remove" | "حذف", "ہٹاؤ", "مٹاؤ" |

---

### 5. DigitalOcean Kubernetes Deployment

**Decision**: DOKS with Helm + GitHub Actions CI/CD

**Rationale**:
- DOKS provides managed control plane (no master node costs)
- Helm charts already exist from Phase 4
- GitHub Actions integrates with DO container registry
- Dapr can be installed via Helm

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| AWS EKS | Higher cost; more complex IAM |
| GKE | Good option but DOKS simpler for small teams |
| Self-managed K8s | Operational burden too high |

**CI/CD Pipeline**:
1. Push to main → GitHub Action triggers
2. Build images → Push to DO Container Registry
3. Helm upgrade → Rolling deployment to DOKS
4. Health checks → Rollback on failure

---

### 6. Tag Implementation Best Practices

**Decision**: Dedicated Tag table with junction table for many-to-many

**Rationale**:
- Proper normalization allows tag reuse
- Junction table enables efficient queries
- Tag counts computed via COUNT query
- Deletion cascades tag associations only

**Data Model**:
```
Tag (id, user_id, name, color, created_at)
TaskTag (task_id, tag_id)  -- Junction table
```

**Query Patterns**:
- Get tags with counts: `SELECT tag.*, COUNT(task_tag.task_id) FROM tag LEFT JOIN task_tag...`
- Filter by tag: `SELECT task.* FROM task JOIN task_tag ON... WHERE task_tag.tag_id = ?`

---

### 7. Filtering and Sorting Performance

**Decision**: Database-level filtering with indexed columns

**Rationale**:
- PostgreSQL handles filtering efficiently with proper indexes
- Avoid loading all tasks into memory
- Compound indexes for common filter combinations

**Indexes Required**:
```sql
CREATE INDEX idx_task_user_status ON task(user_id, status);
CREATE INDEX idx_task_user_priority ON task(user_id, priority);
CREATE INDEX idx_task_user_due ON task(user_id, due);
CREATE INDEX idx_task_tag_tag_id ON task_tag(tag_id);
```

**Query Pattern**:
```sql
SELECT * FROM task
WHERE user_id = ?
  AND status = ?
  AND priority <= ?
  AND due BETWEEN ? AND ?
ORDER BY due ASC, priority ASC
LIMIT 50 OFFSET 0;
```

---

### 8. Observability Stack

**Decision**: Prometheus metrics + JSON structured logging

**Rationale**:
- Prometheus is de facto standard for Kubernetes
- FastAPI has prometheus-fastapi-instrumentator
- JSON logs work with any log aggregator
- No vendor lock-in

**Metrics Exposed**:
| Metric | Type | Description |
|--------|------|-------------|
| http_requests_total | Counter | Total requests by endpoint, method, status |
| http_request_duration_seconds | Histogram | Request latency percentiles |
| task_events_published_total | Counter | Events published to Kafka |
| reminder_delivered_total | Counter | Reminders successfully delivered |

**Log Format**:
```json
{
  "timestamp": "2026-01-28T10:30:00Z",
  "level": "INFO",
  "message": "Task created",
  "task_id": "uuid",
  "user_id": "uuid",
  "request_id": "trace-uuid"
}
```

---

## Summary

All technical decisions align with Constitution principles:
- Event-driven architecture enables scalability without breaking existing code
- Urdu support extends AI interpreter without changing execution path
- Cloud deployment reuses Phase 4 containerization
- All new features are additive; backward compatibility preserved
