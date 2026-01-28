"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ProtectedRoute } from "@/lib/auth";
import { api, Task, Tag, ApiClientError } from "@/lib/api";
import { TaskForm } from "@/components/TaskForm";

function EditTaskContent() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.id as string;

  const [task, setTask] = useState<Task | null>(null);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  const fetchTask = useCallback(async () => {
    try {
      setError("");
      const data = await api.getTask(taskId);
      setTask(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 404) {
          setError("Task not found");
        } else {
          setError(err.message);
        }
      } else {
        setError("Failed to load task");
      }
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  const fetchTags = useCallback(async () => {
    try {
      const tags = await api.getTags();
      setAvailableTags(tags);
    } catch (err) {
      console.error("Failed to fetch tags:", err);
    }
  }, []);

  useEffect(() => {
    fetchTask();
    fetchTags();
  }, [fetchTask, fetchTags]);

  const handleUpdate = async (data: {
    title: string;
    description: string;
    priority: number;
    due: string | null;
    tagIds: string[];
  }) => {
    setIsSaving(true);
    try {
      await api.updateTask(taskId, {
        title: data.title,
        description: data.description || undefined,
        priority: data.priority,
        due: data.due || undefined,
        tag_ids: data.tagIds,
      });
      router.push("/tasks");
    } catch (err) {
      if (err instanceof ApiClientError) {
        throw new Error(err.message);
      }
      throw err;
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateTag = async (name: string): Promise<Tag> => {
    const newTag = await api.createTag({ name });
    setAvailableTags((prev) => [...prev, newTag]);
    return newTag;
  };

  // Map task tag names to tag IDs for initial selection
  const getInitialTagIds = (): string[] => {
    if (!task || !task.tags) return [];
    return task.tags
      .map((tagName) => availableTags.find((t) => t.name === tagName)?.id)
      .filter((id): id is string => id !== undefined);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-2xl mx-auto px-4 py-16 sm:px-6 lg:px-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            {error || "Task not found"}
          </h1>
          <Link
            href="/tasks"
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Back to tasks
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-2xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center space-x-4">
            <Link
              href="/tasks"
              className="text-gray-500 hover:text-gray-700"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">Edit Task</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-2xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <TaskForm
            initialTitle={task.title}
            initialDescription={task.description || ""}
            initialPriority={task.priority}
            initialDue={task.due}
            initialTagIds={getInitialTagIds()}
            availableTags={availableTags}
            onSubmit={handleUpdate}
            onCancel={() => router.push("/tasks")}
            onCreateTag={handleCreateTag}
            submitLabel="Save Changes"
            isLoading={isSaving}
          />
        </div>
      </main>
    </div>
  );
}

export default function EditTaskPage() {
  return (
    <ProtectedRoute>
      <EditTaskContent />
    </ProtectedRoute>
  );
}
