# REST API Endpoints

**Version**: 1.0.0
**Base URL**: `http://localhost:8000/api`

This document consolidates all REST API endpoints across Phase 1, 2, and 3.

---

## Authentication Endpoints (Phase 2)

All protected endpoints require JWT Bearer token in Authorization header.

### POST /api/auth/register

Register a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response** (201 Created):
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2026-01-20T00:00:00Z",
    "updated_at": "2026-01-20T00:00:00Z"
  },
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /api/auth/login

Authenticate and receive access token.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### GET /api/auth/me

Get current authenticated user.

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2026-01-20T00:00:00Z",
  "updated_at": "2026-01-20T00:00:00Z"
}
```

---

## Task Endpoints (Phase 2)

All endpoints require authentication. Users can only access their own tasks.

### GET /api/tasks

List all tasks for current user.

**Query Parameters**:
- `completed` (boolean, optional): Filter by completion status
- `search` (string, optional): Search in task titles

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "is_completed": false,
    "created_at": "2026-01-20T00:00:00Z",
    "updated_at": "2026-01-20T00:00:00Z"
  }
]
```

### POST /api/tasks

Create a new task.

**Request Body**:
```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "is_completed": false
}
```

**Response** (201 Created): Task object

### GET /api/tasks/{task_id}

Get a specific task.

**Response** (200 OK): Task object

### PATCH /api/tasks/{task_id}

Update a task (partial update).

**Request Body** (all fields optional):
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "is_completed": true
}
```

**Response** (200 OK): Updated task object

### DELETE /api/tasks/{task_id}

Delete a task.

**Response** (204 No Content)

---

## Chat Endpoints (Phase 3)

AI-powered natural language task management.

### POST /api/chat/message

Send a natural language message to the AI assistant.

**Request Body**:
```json
{
  "message": "Add a task to buy groceries tomorrow",
  "conversation_id": "uuid (optional, for continuing conversation)"
}
```

**Response** (200 OK):
```json
{
  "message": "I've created a task 'buy groceries' for tomorrow.",
  "confidence": 0.95,
  "action": "add",
  "suggested_cli": "bonsai add --title \"buy groceries\" --due \"tomorrow\"",
  "needs_confirmation": false,
  "is_fallback": false,
  "conversation_id": "uuid",
  "message_id": "uuid",
  "task": { "id": "uuid", "title": "buy groceries", ... },
  "tasks": null
}
```

**Confidence Tiers**:
- `>= 0.8`: High confidence - executed immediately
- `0.5 - 0.8`: Medium confidence - needs confirmation
- `< 0.5`: Low confidence - fallback to CLI suggestion

### POST /api/chat/confirm

Confirm or reject a pending action.

**Request Body**:
```json
{
  "conversation_id": "uuid",
  "confirmed": true
}
```

**Response** (200 OK): Same as /chat/message

---

## Conversation Endpoints (Phase 3)

Manage chat conversation history.

### GET /api/conversations

List all conversations for current user.

**Query Parameters**:
- `limit` (integer, default 50): Maximum conversations to return
- `offset` (integer, default 0): Pagination offset

**Response** (200 OK):
```json
{
  "conversations": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "Task management session",
      "created_at": "2026-01-20T00:00:00Z",
      "updated_at": "2026-01-20T00:00:00Z"
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

### POST /api/conversations

Create a new conversation.

**Request Body**:
```json
{
  "title": "My new conversation (optional)"
}
```

**Response** (201 Created): Conversation object

### GET /api/conversations/{conversation_id}

Get conversation with all messages.

**Response** (200 OK):
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Task management session",
  "created_at": "2026-01-20T00:00:00Z",
  "updated_at": "2026-01-20T00:00:00Z",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Add a task to buy groceries",
      "generated_command": null,
      "confidence_score": null,
      "timestamp": "2026-01-20T00:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "I've created a task 'buy groceries'.",
      "generated_command": "bonsai add --title \"buy groceries\"",
      "confidence_score": 0.95,
      "timestamp": "2026-01-20T00:00:01Z"
    }
  ]
}
```

### PATCH /api/conversations/{conversation_id}

Update conversation title.

**Request Body**:
```json
{
  "title": "New title"
}
```

**Response** (200 OK): Updated conversation object

### DELETE /api/conversations/{conversation_id}

Delete conversation and all messages.

**Response** (204 No Content)

---

## Health Endpoint

### GET /health

Health check for load balancers.

**Response** (200 OK):
```json
{
  "status": "healthy"
}
```

---

## Error Responses

All errors follow consistent format:

```json
{
  "detail": "Error message",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format",
      "type": "value_error"
    }
  ]
}
```

**Status Codes**:
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
