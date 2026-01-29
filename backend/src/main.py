"""
FastAPI application entry point.

Configures the main application with:
- CORS middleware for frontend integration
- Error handlers for consistent API responses
- Database lifecycle management
- API routers for auth and tasks
- Phase 5: Prometheus metrics and structured logging
- Phase 5: Background task for reminder notifications
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure structured logging early
from src.config.logging import configure_logging
configure_logging()
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.db import create_db_and_tables

# =============================================================================
# Application Lifespan
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Startup: Creates database tables if they don't exist.
             Starts background reminder checker.
    Shutdown: Cleanup resources if needed.
    """
    # Startup
    create_db_and_tables()

    # Start background reminder checker (Phase 5)
    from src.config.scheduler import check_due_reminders
    reminder_task = asyncio.create_task(check_due_reminders())

    yield

    # Shutdown - cancel background tasks
    reminder_task.cancel()
    try:
        await reminder_task
    except asyncio.CancelledError:
        pass


# =============================================================================
# Application Factory
# =============================================================================


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="AutoSaaS Todo API",
        description="""
AI Full-Stack Scaffold Engine - Todo Backend

## Phase 5 Advanced Features

### Task Management
- **Priority Management**: Assign priority levels (1-5) to tasks with visual indicators
- **Tags & Categorization**: Create and assign tags to organize tasks
- **Advanced Filtering**: Filter by status, priority, due date, tags, and search text
- **Sorting**: Sort tasks by created_at, updated_at, priority, due date, or title

### Recurring Tasks
- Create tasks with recurrence patterns (daily, weekly, monthly, yearly)
- Automatic generation of next instance on completion
- Series update/delete options

### Reminders
- Schedule up to 3 reminders per task
- Real-time notifications via Server-Sent Events (SSE)
- Auto-cancel on task completion

### Bilingual Support
- Urdu/Roman Urdu natural language processing
- RTL text display support

### Cloud-Native
- Event-driven architecture with Dapr pub/sub
- Prometheus metrics endpoint
- Kubernetes-ready health checks
""",
        version="0.5.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Health", "description": "Health check endpoints for Kubernetes"},
            {"name": "Metrics", "description": "Prometheus metrics endpoint"},
            {"name": "Authentication", "description": "User registration and JWT authentication"},
            {"name": "Tasks", "description": "Task CRUD with priority, due dates, tags, and recurrence"},
            {"name": "Tags", "description": "Tag management for task categorization"},
            {"name": "Reminders", "description": "Task reminders with SSE notifications"},
            {"name": "Chat", "description": "AI-powered natural language task management"},
            {"name": "Conversations", "description": "Chat conversation history management"},
        ],
    )

    # -------------------------------------------------------------------------
    # CORS Configuration
    # -------------------------------------------------------------------------

    # Get allowed origins from environment, default to localhost for dev
    allowed_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------------------------

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors with consistent format."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": errors,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        """Handle ValueError with 400 Bad Request."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    # -------------------------------------------------------------------------
    # API Routers
    # -------------------------------------------------------------------------

    from src.api.auth import router as auth_router
    from src.api.tasks import router as tasks_router
    from src.api.chat import router as chat_router
    from src.api.conversations import router as conversations_router
    from src.api.health import router as health_router
    from src.api.metrics import router as metrics_router
    from src.api.tags import router as tags_router

    # Health endpoints (no prefix for Kubernetes compatibility)
    app.include_router(health_router, tags=["Health"])

    # Phase 5: Prometheus metrics endpoint
    app.include_router(metrics_router, tags=["Metrics"])

    # API endpoints
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    app.include_router(conversations_router, prefix="/api/conversations", tags=["Conversations"])

    # Phase 5: Tags endpoint
    app.include_router(tags_router, prefix="/api/tags", tags=["Tags"])

    # Phase 5: Reminders endpoint
    from src.api.reminders import router as reminders_router
    app.include_router(reminders_router, prefix="/api/reminders", tags=["Reminders"])

    return app


# Create the application instance
app = create_app()


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
