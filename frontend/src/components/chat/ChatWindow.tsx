"use client";

/**
 * ChatWindow component - main chat interface.
 *
 * Orchestrates the chat UI:
 * - Displays conversation messages
 * - Handles sending messages
 * - Shows confirmation dialogs
 * - Renders fallback CLI suggestions
 */

import { useState, useEffect, useRef } from "react";
import {
  api,
  Message,
  ChatMessageResponse,
  Task,
  ApiClientError,
} from "@/lib/api";
import { MessageBubble } from "./MessageBubble";
import { InputBar } from "./InputBar";
import { FallbackCLI } from "./FallbackCLI";

interface ChatWindowProps {
  conversationId?: string;
  onConversationCreated?: (id: string) => void;
}

interface DisplayMessage extends Message {
  task?: Task | null;
  tasks?: Task[] | null;
  suggestedCli?: string | null;
  isFallback?: boolean;
  needsConfirmation?: boolean;
  language?: string; // Phase 5 (US6): en, ur, or mixed
}

export function ChatWindow({
  conversationId: initialConversationId,
  onConversationCreated,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>(
    initialConversationId
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingConfirmation, setPendingConfirmation] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load existing conversation or reset for new chat
  useEffect(() => {
    if (initialConversationId) {
      loadConversation(initialConversationId);
    } else {
      // Reset state for new conversation
      setMessages([]);
      setConversationId(undefined);
      setError(null);
      setPendingConfirmation(false);
    }
  }, [initialConversationId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadConversation = async (id: string) => {
    try {
      setIsLoading(true);
      const conversation = await api.getConversation(id);
      setMessages(conversation.messages);
      setConversationId(id);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to load conversation");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (text: string) => {
    setError(null);
    setPendingConfirmation(false);

    // Add user message optimistically
    const userMessage: DisplayMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: text,
      generated_command: null,
      confidence_score: null,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await api.sendChatMessage({
        message: text,
        conversation_id: conversationId,
      });

      // Update conversation ID if new
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
        onConversationCreated?.(response.conversation_id);
      }

      // Add assistant response
      const assistantMessage: DisplayMessage = {
        id: response.message_id,
        role: "assistant",
        content: response.message,
        generated_command: response.suggested_cli,
        confidence_score: response.confidence,
        timestamp: new Date().toISOString(),
        task: response.task,
        tasks: response.tasks,
        suggestedCli: response.suggested_cli,
        isFallback: response.is_fallback,
        needsConfirmation: response.needs_confirmation,
        language: response.language, // Phase 5 (US6)
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Track if confirmation is needed
      if (response.needs_confirmation) {
        setPendingConfirmation(true);
      }
    } catch (err) {
      // Remove optimistic user message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));

      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to send message. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = async (confirmed: boolean) => {
    if (!conversationId) return;

    setIsLoading(true);
    setPendingConfirmation(false);

    try {
      const response = await api.confirmChatAction({
        conversation_id: conversationId,
        confirmed,
      });

      // Add confirmation response
      const assistantMessage: DisplayMessage = {
        id: response.message_id,
        role: "assistant",
        content: response.message,
        generated_command: response.suggested_cli,
        confidence_score: response.confidence,
        timestamp: new Date().toISOString(),
        task: response.task,
        tasks: response.tasks,
        language: response.language, // Phase 5 (US6)
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to process confirmation");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 && !isLoading && (
          <WelcomeMessage />
        )}

        {messages.map((message) => (
          <div key={message.id}>
            <MessageBubble
              message={message}
              task={message.task}
              tasks={message.tasks}
              language={message.language}
            />

            {/* Show fallback CLI if applicable */}
            {message.role === "assistant" &&
              message.isFallback &&
              message.suggestedCli && (
                <div className="ml-4">
                  <FallbackCLI command={message.suggestedCli} />
                </div>
              )}
          </div>
        ))}

        {/* Confirmation buttons */}
        {pendingConfirmation && (
          <ConfirmationButtons
            onConfirm={() => handleConfirm(true)}
            onCancel={() => handleConfirm(false)}
            disabled={isLoading}
          />
        )}

        {/* Loading indicator */}
        {isLoading && <LoadingIndicator />}

        {/* Error message */}
        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <InputBar
        onSend={handleSend}
        disabled={isLoading}
        placeholder="Ask me to manage your tasks..."
      />
    </div>
  );
}

function WelcomeMessage() {
  return (
    <div className="text-center py-8">
      <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
        Welcome to Todo Chat
      </h2>
      <p className="text-gray-500 dark:text-gray-400 mb-4">
        I can help you manage your tasks using natural language.
      </p>
      <div className="text-left max-w-md mx-auto space-y-2 text-sm text-gray-600 dark:text-gray-400">
        <p>Try saying:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>&quot;Add a task to buy groceries&quot;</li>
          <li>&quot;Show my pending tasks&quot;</li>
          <li>&quot;Mark task 1 as done&quot;</li>
          <li>&quot;Delete the meeting task&quot;</li>
        </ul>
      </div>
    </div>
  );
}

function ConfirmationButtons({
  onConfirm,
  onCancel,
  disabled,
}: {
  onConfirm: () => void;
  onCancel: () => void;
  disabled: boolean;
}) {
  return (
    <div className="flex gap-2 justify-center py-2">
      <button
        onClick={onConfirm}
        disabled={disabled}
        className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg
                   font-medium transition-colors disabled:opacity-50"
      >
        Yes, do it
      </button>
      <button
        onClick={onCancel}
        disabled={disabled}
        className="px-4 py-2 bg-gray-300 hover:bg-gray-400 dark:bg-gray-700 dark:hover:bg-gray-600
                   text-gray-800 dark:text-gray-200 rounded-lg font-medium transition-colors
                   disabled:opacity-50"
      >
        No, cancel
      </button>
    </div>
  );
}

function LoadingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
        </div>
      </div>
    </div>
  );
}

function ErrorMessage({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <div className="flex justify-center mb-4">
      <div className="bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded-lg px-4 py-2 flex items-center gap-2">
        <span>{message}</span>
        <button
          onClick={onDismiss}
          className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-200"
        >
          ×
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;
