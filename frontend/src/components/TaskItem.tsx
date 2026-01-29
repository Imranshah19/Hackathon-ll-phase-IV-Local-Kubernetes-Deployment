"use client";

import Link from "next/link";
import { format, isPast, isToday } from "date-fns";
import { Task, PRIORITY_CONFIG, PriorityLevel } from "@/lib/api";
import { PriorityBadge } from "./PriorityPicker";

interface TaskItemProps {
  task: Task;
  onToggle: (id: string, completed: boolean) => void;
  onDelete: (id: string) => void;
  onComplete?: (id: string) => Promise<Task | null>; // Returns next instance if recurring
  reminderCount?: number; // Phase 5 - US5: Number of pending reminders
}

// Recurrence indicator component
function RecurrenceIndicator() {
  return (
    <span
      className="inline-flex items-center text-blue-500"
      title="Recurring task"
    >
      <svg
        className="w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
        />
      </svg>
    </span>
  );
}

// Reminder indicator component (Phase 5 - US5)
function ReminderIndicator({ count }: { count: number }) {
  return (
    <span
      className="inline-flex items-center text-yellow-500"
      title={`${count} reminder${count > 1 ? 's' : ''} set`}
    >
      <svg
        className="w-4 h-4"
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
      {count > 1 && (
        <span className="text-xs ml-0.5">{count}</span>
      )}
    </span>
  );
}

export function TaskItem({ task, onToggle, onDelete, onComplete, reminderCount = 0 }: TaskItemProps) {
  const priorityConfig = PRIORITY_CONFIG[task.priority as PriorityLevel] || PRIORITY_CONFIG[3];
  const isRecurring = task.recurrence_rule_id !== null;
  const hasReminders = reminderCount > 0;

  // Handle checkbox change - use onComplete for recurring tasks
  const handleToggle = async () => {
    if (!task.is_completed && isRecurring && onComplete) {
      // For recurring tasks, use the complete endpoint
      await onComplete(task.id);
    } else {
      // For regular tasks or uncompleting, use toggle
      onToggle(task.id, !task.is_completed);
    }
  };

  // Format due date with visual indicators
  const formatDueDate = (dueDate: string | null) => {
    if (!dueDate) return null;
    const date = new Date(dueDate);
    const isOverdue = isPast(date) && !task.is_completed;
    const isDueToday = isToday(date);

    return {
      text: format(date, "MMM d, yyyy h:mm a"),
      isOverdue,
      isDueToday,
    };
  };

  const dueInfo = formatDueDate(task.due);

  return (
    <div
      className="flex items-center justify-between p-4 bg-white border rounded-lg shadow-sm hover:shadow-md transition-shadow"
      style={{ borderLeftWidth: "4px", borderLeftColor: priorityConfig.color }}
    >
      <div className="flex items-center space-x-4 flex-1">
        <input
          type="checkbox"
          checked={task.is_completed}
          onChange={handleToggle}
          className="h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3
              className={`text-lg font-medium truncate ${
                task.is_completed ? "line-through text-gray-400" : "text-gray-900"
              }`}
            >
              {task.title}
            </h3>
            {/* Priority Badge */}
            {task.priority !== 5 && (
              <PriorityBadge priority={task.priority} showLabel={task.priority <= 2} />
            )}
            {/* Recurrence Indicator */}
            {isRecurring && <RecurrenceIndicator />}
            {/* Reminder Indicator (Phase 5 - US5) */}
            {hasReminders && <ReminderIndicator count={reminderCount} />}
          </div>
          {task.description && (
            <p
              className={`text-sm truncate ${
                task.is_completed ? "text-gray-300" : "text-gray-500"
              }`}
            >
              {task.description}
            </p>
          )}
          {/* Due Date Display */}
          {dueInfo && (
            <p
              className={`text-xs mt-1 ${
                dueInfo.isOverdue
                  ? "text-red-600 font-medium"
                  : dueInfo.isDueToday
                  ? "text-orange-600"
                  : "text-gray-400"
              }`}
            >
              {dueInfo.isOverdue ? "Overdue: " : dueInfo.isDueToday ? "Due today: " : "Due: "}
              {dueInfo.text}
            </p>
          )}
          {/* Tags Display */}
          {task.tags && task.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {task.tags.map((tagName) => (
                <span
                  key={tagName}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600"
                >
                  {tagName}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-2 ml-4">
        <Link
          href={`/tasks/${task.id}/edit`}
          className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
        >
          Edit
        </Link>
        <button
          onClick={() => onDelete(task.id)}
          className="px-3 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
