"""
AI Configuration for Phase 3 AI Chat.

Loads AI provider credentials and settings from environment variables.
Supports OpenAI as primary provider with Anthropic as fallback.

Environment Variables:
- OPENAI_API_KEY: OpenAI API key (primary provider)
- ANTHROPIC_API_KEY: Anthropic API key (fallback provider)
- AI_TIMEOUT_SECONDS: Timeout for AI operations (default: 5)
- AI_CONFIDENCE_THRESHOLD_HIGH: Execute immediately (default: 0.8)
- AI_CONFIDENCE_THRESHOLD_LOW: Request clarification below this (default: 0.5)
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class AIConfig(BaseSettings):
    """
    AI service configuration.

    Follows Constitution Principle X (Graceful AI Degradation):
    - 5-second timeout for AI operations
    - Fallback to CLI when AI unavailable
    """

    # API Keys
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key for primary AI provider",
    )

    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key for fallback AI provider",
    )

    # Timeouts (Constitution Principle X: 5 seconds max)
    ai_timeout_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Timeout for AI operations in seconds",
    )

    # Confidence Thresholds (from research.md RQ-005)
    confidence_threshold_high: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Execute immediately if confidence >= this value",
    )

    confidence_threshold_low: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Suggest CLI fallback if confidence < this value",
    )

    # Model Configuration
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use for intent extraction",
    )

    anthropic_model: str = Field(
        default="claude-3-haiku-20240307",
        description="Anthropic model to use as fallback",
    )

    # Context Window
    max_conversation_context: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of messages to include in AI context",
    )

    model_config = {
        "env_prefix": "",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def primary_provider(self) -> Literal["openai", "anthropic", "none"]:
        """Determine which AI provider is available."""
        if self.openai_api_key:
            return "openai"
        elif self.anthropic_api_key:
            return "anthropic"
        return "none"

    @property
    def has_ai_provider(self) -> bool:
        """Check if any AI provider is configured."""
        return self.primary_provider != "none"


@lru_cache
def get_ai_config() -> AIConfig:
    """
    Get cached AI configuration.

    Returns:
        AIConfig instance with values loaded from environment.
    """
    return AIConfig()


__all__ = ["AIConfig", "get_ai_config"]
