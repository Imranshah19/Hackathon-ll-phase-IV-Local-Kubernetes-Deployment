"use client";

/**
 * MessageBubble component for displaying chat messages.
 *
 * Renders user and assistant messages with appropriate styling.
 * Assistant messages can display confidence indicators and task data.
 *
 * Phase 5 (US6): Supports RTL text direction for Urdu messages.
 */

import { Message, Task } from "@/lib/api";

interface MessageBubbleProps {
  message: Message;
  task?: Task | null;
  tasks?: Task[] | null;
  action?: string | null;
  language?: string; // Phase 5 (US6): en, ur, or mixed
}

/**
 * Detect if text contains Urdu/Arabic script characters.
 */
function containsUrdu(text: string): boolean {
  // Check for Arabic/Urdu Unicode block characters
  return /[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]/.test(text);
}

export function MessageBubble({ message, task, tasks, language }: MessageBubbleProps) {
  const isUser = message.role === "user";

  // Phase 5 (US6): Determine text direction
  // Use RTL for Urdu content or if language explicitly set to 'ur'
  const isRtl = language === "ur" || containsUrdu(message.content);
  const textDirection = isRtl ? "rtl" : "ltr";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? "bg-blue-500 text-white"
            : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        }`}
        dir={textDirection}
      >
        {/* Message content */}
        <p className={`whitespace-pre-wrap ${isRtl ? "font-urdu" : ""}`}>{message.content}</p>

        {/* Assistant-specific metadata */}
        {!isUser && (
          <>
            {/* Confidence indicator */}
            {message.confidence_score !== null && (
              <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                <ConfidenceIndicator score={message.confidence_score} />
              </div>
            )}

            {/* Generated CLI command */}
            {message.generated_command && (
              <div className="mt-2 text-xs">
                <code className="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded text-gray-600 dark:text-gray-300">
                  {message.generated_command}
                </code>
              </div>
            )}
          </>
        )}

        {/* Task display (for create/update/complete/delete) */}
        {task && <TaskCard task={task} />}

        {/* Task list display (for list action) */}
        {tasks && tasks.length > 0 && <TaskList tasks={tasks} />}
      </div>
    </div>
  );
}

function ConfidenceIndicator({ score }: { score: number }) {
  let label: string;
  let color: string;

  if (score >= 0.8) {
    label = "High confidence";
    color = "text-green-600 dark:text-green-400";
  } else if (score >= 0.5) {
    label = "Medium confidence";
    color = "text-yellow-600 dark:text-yellow-400";
  } else {
    label = "Low confidence";
    color = "text-red-600 dark:text-red-400";
  }

  return (
    <span className={color}>
      {label} ({Math.round(score * 100)}%)
    </span>
  );
}

function TaskCard({ task, action }: { task: Task; action?: string }) {
  const isNewlyCreated = action === "add";
  const isDeleted = action === "delete";

  return (
    <div
      className={`mt-3 p-3 rounded border ${
        isNewlyCreated
          ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
          : isDeleted
          ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
          : "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700"
      }`}
    >
      <div className="flex items-center gap-2">
        {isNewlyCreated && (
          <span className="text-xs bg-green-100 dark:bg-green-800 text-green-700 dark:text-green-200 px-2 py-0.5 rounded font-medium">
            Created
          </span>
        )}
        {isDeleted && (
          <span className="text-xs bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-200 px-2 py-0.5 rounded font-medium">
            Deleted
          </span>
        )}
        <span
          className={`text-sm ${
            task.is_completed || isDeleted
              ? "line-through text-gray-400"
              : "text-gray-900 dark:text-gray-100"
          }`}
        >
          {task.title}
        </span>
        {task.is_completed && !isDeleted && (
          <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">
            Completed
          </span>
        )}
      </div>
      {task.description && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {task.description}
        </p>
      )}
      <p className="text-xs text-gray-400 mt-1">ID: {task.id.substring(0, 8)}</p>
    </div>
  );
}

function TaskList({ tasks }: { tasks: Task[] }) {
  return (
    <div className="mt-3 space-y-2">
      {tasks.map((task) => (
        <div
          key={task.id}
          className="p-2 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center justify-between">
            <span
              className={`text-sm ${
                task.is_completed
                  ? "line-through text-gray-400"
                  : "text-gray-900 dark:text-gray-100"
              }`}
            >
              {task.title}
            </span>
            <span className="text-xs text-gray-400">
              {task.id.substring(0, 8)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default MessageBubble;
