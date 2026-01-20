"""
AI Integration Layer for Phase 3 AI Chat.

This module provides natural language interpretation and command execution
for the AI-powered chat interface. It follows Constitution Principle VII
(AI as Interpreter, Not Executor) - AI generates commands, Bonsai CLI executes.

Components:
- interpreter: NLP intent extraction using OpenAI/Claude function calling
- executor: Bridge to Bonsai CLI service layer
- fallback: Confidence-based fallback to CLI commands
- types: Data types for interpreted commands

Architecture:
    User Message -> Interpreter -> InterpretedCommand -> Executor -> Response
                              |
                              v
                        (If confidence < threshold)
                              |
                              v
                         Fallback -> CLI Suggestion
"""

from src.ai.types import InterpretedCommand, CommandAction, ConfidenceLevel, StatusFilter
from src.ai.interpreter import AIInterpreter, get_interpreter
from src.ai.executor import CommandExecutor, ExecutionResult
from src.ai.fallback import FallbackHandler, FallbackResponse, get_fallback_handler

__all__ = [
    # Types
    "InterpretedCommand",
    "CommandAction",
    "ConfidenceLevel",
    "StatusFilter",
    # Interpreter
    "AIInterpreter",
    "get_interpreter",
    # Executor
    "CommandExecutor",
    "ExecutionResult",
    # Fallback
    "FallbackHandler",
    "FallbackResponse",
    "get_fallback_handler",
]
