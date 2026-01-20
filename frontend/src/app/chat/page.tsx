"use client";

/**
 * Chat page for Phase 3 AI-Powered Todo Chatbot.
 *
 * Provides a conversational interface for managing tasks
 * using natural language commands.
 */

import { useEffect, useState, useCallback } from "react";
import { useAuth, ProtectedRoute } from "@/lib/auth";
import { api, Conversation, ApiClientError } from "@/lib/api";
import { ChatWindow } from "@/components/chat";
import Link from "next/link";

function ChatContent() {
  const { user, logout } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>();
  const [showSidebar, setShowSidebar] = useState(true);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);

  const fetchConversations = useCallback(async () => {
    try {
      const data = await api.getConversations({ limit: 50 });
      setConversations(data.conversations);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    } finally {
      setIsLoadingConversations(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleConversationCreated = (id: string) => {
    setSelectedConversationId(id);
    // Refresh conversations list
    fetchConversations();
  };

  const handleNewChat = () => {
    setSelectedConversationId(undefined);
  };

  const handleDeleteConversation = async (id: string) => {
    if (!confirm("Delete this conversation?")) return;

    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (selectedConversationId === id) {
        setSelectedConversationId(undefined);
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 shadow flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="lg:hidden p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <MenuIcon />
              </button>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Todo Chat
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/tasks"
                className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Tasks View
              </Link>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {user?.email}
              </span>
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Conversation List */}
        <aside
          className={`${
            showSidebar ? "w-64" : "w-0"
          } flex-shrink-0 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 overflow-hidden transition-all duration-300 lg:w-64`}
        >
          <div className="h-full flex flex-col">
            {/* New Chat Button */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <button
                onClick={handleNewChat}
                className="w-full py-2 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
              >
                + New Chat
              </button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto p-2">
              {isLoadingConversations ? (
                <div className="flex justify-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                </div>
              ) : conversations.length === 0 ? (
                <p className="text-center py-4 text-sm text-gray-500 dark:text-gray-400">
                  No conversations yet
                </p>
              ) : (
                <div className="space-y-1">
                  {conversations.map((conv) => (
                    <ConversationItem
                      key={conv.id}
                      conversation={conv}
                      isSelected={conv.id === selectedConversationId}
                      onClick={() => setSelectedConversationId(conv.id)}
                      onDelete={() => handleDeleteConversation(conv.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* Chat Window */}
        <main className="flex-1 flex flex-col min-w-0">
          <ChatWindow
            conversationId={selectedConversationId}
            onConversationCreated={handleConversationCreated}
          />
        </main>
      </div>
    </div>
  );
}

function ConversationItem({
  conversation,
  isSelected,
  onClick,
  onDelete,
}: {
  conversation: Conversation;
  isSelected: boolean;
  onClick: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
        isSelected
          ? "bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100"
          : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
      }`}
      onClick={onClick}
    >
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">
          {conversation.title || "New conversation"}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {formatDate(conversation.updated_at)}
        </p>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
        title="Delete conversation"
      >
        <TrashIcon />
      </button>
    </div>
  );
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } else if (days === 1) {
    return "Yesterday";
  } else if (days < 7) {
    return date.toLocaleDateString([], { weekday: "short" });
  } else {
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  }
}

function MenuIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="3" y1="12" x2="21" y2="12"></line>
      <line x1="3" y1="6" x2="21" y2="6"></line>
      <line x1="3" y1="18" x2="21" y2="18"></line>
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="3 6 5 6 21 6"></polyline>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
    </svg>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatContent />
    </ProtectedRoute>
  );
}
