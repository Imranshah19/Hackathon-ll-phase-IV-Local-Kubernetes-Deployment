"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { getToken, ReminderNotification } from "@/lib/api";

interface Notification {
  id: string;
  type: "reminder" | "info" | "error";
  title: string;
  message: string;
  taskId?: string;
  timestamp: Date;
}

interface NotificationContextValue {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, "id" | "timestamp">) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  isConnected: boolean;
}

const NotificationContext = createContext<NotificationContextValue | null>(null);

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotifications must be used within NotificationProvider");
  }
  return context;
}

interface NotificationProviderProps {
  children: ReactNode;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTO_DISMISS_MS = 10000; // 10 seconds

export function NotificationProvider({ children }: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  const addNotification = useCallback((notification: Omit<Notification, "id" | "timestamp">) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
    };

    setNotifications((prev) => [...prev, newNotification]);

    // Auto-dismiss after 10 seconds
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, AUTO_DISMISS_MS);
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // SSE Connection
  useEffect(() => {
    const token = getToken();
    if (!token) {
      // Not authenticated, don't connect
      return;
    }

    // Create EventSource for SSE
    // Note: EventSource doesn't support custom headers, so we pass token as query param
    // In a production app, you might use cookie-based auth for SSE
    const url = `${API_BASE_URL}/api/reminders/stream`;

    // We need to use fetch with custom headers for auth
    // Since EventSource doesn't support headers, we'll use a different approach
    let controller: AbortController | null = null;

    const connectSSE = async () => {
      controller = new AbortController();

      try {
        const response = await fetch(url, {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "text/event-stream",
          },
          signal: controller.signal,
        });

        if (!response.ok) {
          console.error("SSE connection failed:", response.status);
          return;
        }

        if (!response.body) {
          console.error("SSE response has no body");
          return;
        }

        setIsConnected(true);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Process complete messages
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data: ReminderNotification = JSON.parse(line.slice(6));

                if (data.type === "reminder" && data.data) {
                  addNotification({
                    type: "reminder",
                    title: "Task Reminder",
                    message: data.data.message,
                    taskId: data.data.task_id,
                  });
                }
              } catch {
                // Ignore parse errors (e.g., keepalive comments)
              }
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          console.error("SSE error:", err);
        }
      } finally {
        setIsConnected(false);
      }
    };

    connectSSE();

    // Cleanup on unmount
    return () => {
      controller?.abort();
    };
  }, []); // Empty deps - reconnect handled separately

  const value: NotificationContextValue = {
    notifications,
    addNotification,
    removeNotification,
    clearAll,
    isConnected,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationToastContainer
        notifications={notifications}
        onDismiss={removeNotification}
      />
    </NotificationContext.Provider>
  );
}

// Toast container component
interface ToastContainerProps {
  notifications: Notification[];
  onDismiss: (id: string) => void;
}

function NotificationToastContainer({ notifications, onDismiss }: ToastContainerProps) {
  if (notifications.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <NotificationToast
          key={notification.id}
          notification={notification}
          onDismiss={() => onDismiss(notification.id)}
        />
      ))}
    </div>
  );
}

// Individual toast component
interface ToastProps {
  notification: Notification;
  onDismiss: () => void;
}

function NotificationToast({ notification, onDismiss }: ToastProps) {
  const bgColor =
    notification.type === "error"
      ? "bg-red-50 border-red-200"
      : notification.type === "reminder"
      ? "bg-yellow-50 border-yellow-200"
      : "bg-blue-50 border-blue-200";

  const iconColor =
    notification.type === "error"
      ? "text-red-500"
      : notification.type === "reminder"
      ? "text-yellow-500"
      : "text-blue-500";

  return (
    <div
      className={`${bgColor} border rounded-lg shadow-lg p-4 flex items-start gap-3 animate-slide-in`}
    >
      {/* Bell icon for reminders */}
      {notification.type === "reminder" && (
        <svg
          className={`w-5 h-5 ${iconColor} flex-shrink-0 mt-0.5`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
      )}

      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-semibold text-gray-900">{notification.title}</h4>
        <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
        <p className="text-xs text-gray-400 mt-1">
          {notification.timestamp.toLocaleTimeString()}
        </p>
      </div>

      <button
        onClick={onDismiss}
        className="text-gray-400 hover:text-gray-600 flex-shrink-0"
        title="Dismiss"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}

// Export for use in other components
export type { Notification, NotificationContextValue };
