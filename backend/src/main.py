"""
FastAPI application entry point.

Configures the main application with:
- CORS middleware for frontend integration
- Error handlers for consistent API responses
- Database lifecycle management
- API routers for auth and tasks
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
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
    Shutdown: Cleanup resources if needed.
    """
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (cleanup if needed)


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
        description="AI Full-Stack Scaffold Engine - Todo Backend",
        version="0.1.0",
        lifespan=lifespan,
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
    # Health Check
    # -------------------------------------------------------------------------

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint for load balancers and monitoring."""
        return {"status": "healthy"}

    # -------------------------------------------------------------------------
    # API Routers
    # -------------------------------------------------------------------------

    from src.api.auth import router as auth_router
    from src.api.tasks import router as tasks_router
    from src.api.chat import router as chat_router
    from src.api.conversations import router as conversations_router

    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    app.include_router(conversations_router, prefix="/api/conversations", tags=["Conversations"])

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
