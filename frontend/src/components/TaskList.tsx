"use client";

import { Task } from "@/lib/api";
import { TaskItem } from "./TaskItem";

interface TaskListProps {
  tasks: Task[];
  onToggle: (id: string, completed: boolean) => void;
  onDelete: (id: string) => void;
  onComplete?: (id: string) => Promise<Task | null>; // Phase 5 - US4
}

export function TaskList({ tasks, onToggle, onDelete, onComplete }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No tasks</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by creating a new task.
        </p>
      </div>
    );
  }

  const completedTasks = tasks.filter((t) => t.is_completed);
  const pendingTasks = tasks.filter((t) => !t.is_completed);

  return (
    <div className="space-y-6">
      {pendingTasks.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-700">
            Pending ({pendingTasks.length})
          </h2>
          {pendingTasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onToggle={onToggle}
              onDelete={onDelete}
              onComplete={onComplete}
            />
          ))}
        </div>
      )}

      {completedTasks.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-500">
            Completed ({completedTasks.length})
          </h2>
          {completedTasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onToggle={onToggle}
              onDelete={onDelete}
              onComplete={onComplete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
