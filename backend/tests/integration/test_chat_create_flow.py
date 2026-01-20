"""
Integration tests for create task via chat flow.

Tests the complete flow from user message to task creation.

User Story 1: Natural Language Task Creation

Flow tested:
1. User sends "Add a task to buy groceries"
2. AI interprets as ADD action
3. Executor creates task via task_service
4. Response confirms creation
5. Task exists in database
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.ai.types import CommandAction, InterpretedCommand
from src.ai.executor import CommandExecutor, ExecutionResult
from src.services.chat_service import ChatService, ChatResponse
from src.services.conversation_service import ConversationService
from src.models.task import Task
from src.models.conversation import Conversation
from src.models.message import Message, MessageRole


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db):
    """Create database session."""
    with Session(in_memory_db) as session:
        yield session


@pytest.fixture
def test_user_id():
    """Generate test user ID."""
    return uuid4()


class TestExecutorAddAction:
    """Integration tests for executor ADD action."""

    def test_execute_add_creates_task(self, session, test_user_id):
        """Test that execute ADD creates a task in database."""
        command = InterpretedCommand(
            original_text="Add a task to buy groceries",
            action=CommandAction.ADD,
            confidence=0.95,
            suggested_cli='bonsai add "buy groceries"',
            title="buy groceries",
        )

        executor = CommandExecutor(session, test_user_id)
        result = executor.execute(command)

        assert result.success is True
        assert result.action == CommandAction.ADD
        assert result.task is not None
        assert result.task["title"] == "buy groceries"

    def test_execute_add_persists_to_database(self, session, test_user_id):
        """Test that created task exists in database."""
        command = InterpretedCommand(
            original_text="Add a task to buy groceries",
            action=CommandAction.ADD,
            confidence=0.95,
            suggested_cli='bonsai add "buy groceries"',
            title="buy groceries",
        )

        executor = CommandExecutor(session, test_user_id)
        result = executor.execute(command)

        # Verify task exists in database
        from sqlmodel import select
        task = session.exec(
            select(Task).where(Task.user_id == test_user_id)
        ).first()

        assert task is not None
        assert task.title == "buy groceries"
        assert task.is_completed is False

    def test_execute_add_assigns_correct_user(self, session, test_user_id):
        """Test that created task is assigned to correct user."""
        command = InterpretedCommand(
            original_text="Add a task",
            action=CommandAction.ADD,
            confidence=0.95,
            suggested_cli='bonsai add "task"',
            title="test task",
        )

        executor = CommandExecutor(session, test_user_id)
        result = executor.execute(command)

        # Verify user_id
        from sqlmodel import select
        task = session.exec(
            select(Task).where(Task.title == "test task")
        ).first()

        assert task.user_id == test_user_id

    def test_execute_add_without_title_fails(self, session, test_user_id):
        """Test that ADD without title returns error."""
        command = InterpretedCommand(
            original_text="add something",
            action=CommandAction.ADD,
            confidence=0.4,
            suggested_cli='bonsai add ""',
            title=None,  # No title
        )

        executor = CommandExecutor(session, test_user_id)
        result = executor.execute(command)

        assert result.success is False
        assert "title" in result.error_message.lower()

    def test_execute_add_with_clarification_needed(self, session, test_user_id):
        """Test that ADD with clarification needed doesn't execute."""
        command = InterpretedCommand(
            original_text="add something",
            action=CommandAction.ADD,
            confidence=0.4,
            suggested_cli='bonsai add ""',
            title=None,
            clarification_needed="What would you like to add?",
        )

        executor = CommandExecutor(session, test_user_id)
        result = executor.execute(command)

        assert result.success is False
        assert result.error_message is not None


class TestConversationService:
    """Integration tests for conversation service."""

    def test_create_conversation(self, session, test_user_id):
        """Test creating a new conversation."""
        service = ConversationService(session, test_user_id)
        conversation = service.create_conversation()

        assert conversation is not None
        assert conversation.id is not None
        assert conversation.user_id == test_user_id

    def test_add_user_message(self, session, test_user_id):
        """Test adding a user message to conversation."""
        service = ConversationService(session, test_user_id)
        conversation = service.create_conversation()

        message = service.add_user_message(
            conversation_id=conversation.id,
            content="Add a task to buy groceries",
        )

        assert message is not None
        assert message.role == MessageRole.USER
        assert message.content == "Add a task to buy groceries"

    def test_add_assistant_message_with_metadata(self, session, test_user_id):
        """Test adding assistant message with AI metadata."""
        service = ConversationService(session, test_user_id)
        conversation = service.create_conversation()

        message = service.add_assistant_message(
            conversation_id=conversation.id,
            content="I've created a new task: \"buy groceries\"",
            generated_command='bonsai add "buy groceries"',
            confidence_score=0.95,
        )

        assert message is not None
        assert message.role == MessageRole.ASSISTANT
        assert message.generated_command == 'bonsai add "buy groceries"'
        assert message.confidence_score == 0.95

    def test_get_conversation_messages(self, session, test_user_id):
        """Test retrieving conversation messages."""
        service = ConversationService(session, test_user_id)
        conversation = service.create_conversation()

        service.add_user_message(conversation.id, "Add task 1")
        service.add_assistant_message(conversation.id, "Created task 1")
        service.add_user_message(conversation.id, "Add task 2")
        service.add_assistant_message(conversation.id, "Created task 2")

        messages = service.get_conversation_messages(conversation.id)

        assert len(messages) == 4
        assert messages[0].role == MessageRole.USER
        assert messages[1].role == MessageRole.ASSISTANT


class TestChatServiceCreateFlow:
    """Integration tests for complete chat create flow."""

    @pytest.mark.asyncio
    async def test_full_create_flow(self, session, test_user_id):
        """Test complete flow: message -> interpret -> execute -> response."""
        # Mock the AI interpreter to return a predictable result
        mock_interpreted = InterpretedCommand(
            original_text="Add a task to buy groceries",
            action=CommandAction.ADD,
            confidence=0.95,
            suggested_cli='bonsai add "buy groceries"',
            title="buy groceries",
        )

        with patch("src.services.chat_service.get_interpreter") as mock_get_interpreter:
            mock_interpreter = MagicMock()
            mock_interpreter.interpret = AsyncMock(return_value=mock_interpreted)
            mock_get_interpreter.return_value = mock_interpreter

            # Mock AI config to have a provider
            with patch("src.services.chat_service.get_ai_config") as mock_config:
                mock_config.return_value = MagicMock(
                    has_ai_provider=True,
                    max_conversation_context=10,
                )

                chat_service = ChatService(session, test_user_id)
                response, message = await chat_service.process_message(
                    user_message="Add a task to buy groceries",
                )

                # Verify response
                assert response.action == "add"
                assert response.confidence >= 0.9
                assert "buy groceries" in response.message.lower()

                # Verify task was created
                from sqlmodel import select
                task = session.exec(
                    select(Task).where(Task.user_id == test_user_id)
                ).first()

                assert task is not None
                assert task.title == "buy groceries"

    @pytest.mark.asyncio
    async def test_create_flow_stores_conversation(self, session, test_user_id):
        """Test that create flow stores messages in conversation."""
        mock_interpreted = InterpretedCommand(
            original_text="Add task",
            action=CommandAction.ADD,
            confidence=0.95,
            suggested_cli='bonsai add "task"',
            title="task",
        )

        with patch("src.services.chat_service.get_interpreter") as mock_get_interpreter:
            mock_interpreter = MagicMock()
            mock_interpreter.interpret = AsyncMock(return_value=mock_interpreted)
            mock_get_interpreter.return_value = mock_interpreter

            with patch("src.services.chat_service.get_ai_config") as mock_config:
                mock_config.return_value = MagicMock(
                    has_ai_provider=True,
                    max_conversation_context=10,
                )

                chat_service = ChatService(session, test_user_id)
                response, assistant_message = await chat_service.process_message(
                    user_message="Add task",
                )

                # Verify conversation was created
                conv_service = ConversationService(session, test_user_id)
                conversations, _ = conv_service.list_conversations()

                assert len(conversations) >= 1

                # Verify messages were stored
                messages = conv_service.get_conversation_messages(
                    assistant_message.conversation_id
                )

                assert len(messages) >= 2  # User + Assistant
                user_msgs = [m for m in messages if m.role == MessageRole.USER]
                assistant_msgs = [m for m in messages if m.role == MessageRole.ASSISTANT]

                assert len(user_msgs) >= 1
                assert len(assistant_msgs) >= 1


class TestChatServiceAmbiguousCreate:
    """Tests for handling ambiguous create commands."""

    @pytest.mark.asyncio
    async def test_ambiguous_add_returns_clarification(self, session, test_user_id):
        """Test that ambiguous add returns clarification request."""
        mock_interpreted = InterpretedCommand(
            original_text="add something",
            action=CommandAction.ADD,
            confidence=0.3,
            suggested_cli='bonsai add ""',
            title=None,
            clarification_needed="What would you like to add?",
        )

        with patch("src.services.chat_service.get_interpreter") as mock_get_interpreter:
            mock_interpreter = MagicMock()
            mock_interpreter.interpret = AsyncMock(return_value=mock_interpreted)
            mock_get_interpreter.return_value = mock_interpreter

            with patch("src.services.chat_service.get_ai_config") as mock_config:
                mock_config.return_value = MagicMock(
                    has_ai_provider=True,
                    max_conversation_context=10,
                    confidence_threshold_low=0.5,
                    confidence_threshold_high=0.8,
                )

                chat_service = ChatService(session, test_user_id)
                response, _ = await chat_service.process_message(
                    user_message="add something",
                )

                # Should be a fallback with clarification
                assert response.is_fallback is True or response.needs_confirmation is True

                # No task should be created
                from sqlmodel import select
                tasks = session.exec(
                    select(Task).where(Task.user_id == test_user_id)
                ).all()

                assert len(tasks) == 0
