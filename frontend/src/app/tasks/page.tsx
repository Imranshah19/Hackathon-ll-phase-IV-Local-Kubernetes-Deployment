"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth, ProtectedRoute } from "@/lib/auth";
import { api, Task, Tag, ApiClientError, TaskFilterOptions } from "@/lib/api";
import { TaskList } from "@/components/TaskList";
import { TaskForm } from "@/components/TaskForm";
import { TaskFilters, TaskFilterState } from "@/components/TaskFilters";
import { TagManager } from "@/components/TagManager";

function TasksContent() {
  const { user, logout } = useAuth();
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [showTagManager, setShowTagManager] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  // Load initial filter state from session storage
  const [currentFilters, setCurrentFilters] = useState<TaskFilterState>(() => {
    if (typeof window !== "undefined") {
      const saved = sessionStorage.getItem("taskFilters");
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch {
          // Ignore parse errors, use defaults
        }
      }
    }
    return {
      status: "all",
      search: "",
      priorities: [],
      tagIds: [],
      dueFrom: null,
      dueTo: null,
      sortBy: "created_at",
      sortOrder: "desc",
    };
  });

  const fetchTasks = useCallback(async () => {
    try {
      setError("");
      const data = await api.getTasks();
      setAllTasks(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to load tasks");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchTags = useCallback(async () => {
    try {
      const tags = await api.getTags();
      setAvailableTags(tags);
    } catch (err) {
      console.error("Failed to fetch tags:", err);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    fetchTags();
  }, [fetchTasks, fetchTags]);

  // Apply filters client-side for instant feedback
  useEffect(() => {
    let result = [...allTasks];

    // Apply status filter
    if (currentFilters.status === "pending") {
      result = result.filter((t) => !t.is_completed);
    } else if (currentFilters.status === "completed") {
      result = result.filter((t) => t.is_completed);
    }

    // Apply search filter
    if (currentFilters.search) {
      const searchLower = currentFilters.search.toLowerCase();
      result = result.filter((t) =>
        t.title.toLowerCase().includes(searchLower)
      );
    }

    // Apply priority filter (Phase 5)
    if (currentFilters.priorities.length > 0) {
      result = result.filter((t) => currentFilters.priorities.includes(t.priority));
    }

    // Apply tag filter (Phase 5 - US2)
    if (currentFilters.tagIds.length > 0) {
      result = result.filter((t) =>
        currentFilters.tagIds.every((tagId) => {
          // Find the tag name for the tagId
          const tag = availableTags.find((at) => at.id === tagId);
          return tag && t.tags.includes(tag.name);
        })
      );
    }

    // Apply due date range filter (Phase 5 - US3)
    if (currentFilters.dueFrom) {
      const fromDate = new Date(currentFilters.dueFrom);
      result = result.filter((t) => {
        if (!t.due) return false;
        return new Date(t.due) >= fromDate;
      });
    }

    if (currentFilters.dueTo) {
      const toDate = new Date(currentFilters.dueTo);
      toDate.setHours(23, 59, 59, 999); // Include the entire day
      result = result.filter((t) => {
        if (!t.due) return false;
        return new Date(t.due) <= toDate;
      });
    }

    // Apply sorting (Phase 5)
    result.sort((a, b) => {
      let aVal: string | number | null;
      let bVal: string | number | null;

      switch (currentFilters.sortBy) {
        case "priority":
          aVal = a.priority;
          bVal = b.priority;
          break;
        case "due":
          aVal = a.due;
          bVal = b.due;
          break;
        case "title":
          aVal = a.title.toLowerCase();
          bVal = b.title.toLowerCase();
          break;
        case "updated_at":
          aVal = a.updated_at;
          bVal = b.updated_at;
          break;
        default:
          aVal = a.created_at;
          bVal = b.created_at;
      }

      // Handle null values (push to end)
      if (aVal === null && bVal === null) return 0;
      if (aVal === null) return 1;
      if (bVal === null) return -1;

      // Compare
      let comparison = 0;
      if (typeof aVal === "string" && typeof bVal === "string") {
        comparison = aVal.localeCompare(bVal);
      } else {
        comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      }

      return currentFilters.sortOrder === "desc" ? -comparison : comparison;
    });

    setFilteredTasks(result);
  }, [allTasks, currentFilters, availableTags]);

  const handleFilterChange = useCallback((filters: TaskFilterState) => {
    setCurrentFilters(filters);
    // Persist filters to session storage (T049)
    if (typeof window !== "undefined") {
      sessionStorage.setItem("taskFilters", JSON.stringify(filters));
    }
  }, []);

  const taskCounts = {
    all: allTasks.length,
    pending: allTasks.filter((t) => !t.is_completed).length,
    completed: allTasks.filter((t) => t.is_completed).length,
  };

  const handleCreate = async (data: {
    title: string;
    description: string;
    priority: number;
    due: string | null;
    tagIds: string[];
    recurrence: { frequency: string; interval?: number; end_type?: string; end_count?: number; end_date?: string } | null;
  }) => {
    setIsCreating(true);
    try {
      const newTask = await api.createTask({
        title: data.title,
        description: data.description || undefined,
        priority: data.priority,
        due: data.due || undefined,
        tag_ids: data.tagIds,
        recurrence: data.recurrence as any,
      });
      setAllTasks((prev) => [newTask, ...prev]);
      setShowForm(false);
    } finally {
      setIsCreating(false);
    }
  };

  // Phase 5 - US4: Complete recurring task
  const handleComplete = async (id: string): Promise<Task | null> => {
    try {
      const response = await api.completeTask(id);
      // Update the completed task
      setAllTasks((prev) =>
        prev.map((task) => (task.id === id ? response.task : task))
      );
      // Add the next instance if one was created
      if (response.next_instance) {
        setAllTasks((prev) => [response.next_instance!, ...prev]);
        return response.next_instance;
      }
      return null;
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      }
      return null;
    }
  };

  const handleCreateTag = async (name: string): Promise<Tag> => {
    const newTag = await api.createTag({ name });
    setAvailableTags((prev) => [...prev, newTag]);
    return newTag;
  };

  const handleToggle = async (id: string, completed: boolean) => {
    try {
      const updatedTask = await api.updateTask(id, { is_completed: completed });
      setAllTasks((prev) =>
        prev.map((task) => (task.id === id ? updatedTask : task))
      );
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this task?")) {
      return;
    }

    try {
      await api.deleteTask(id);
      setAllTasks((prev) => prev.filter((task) => task.id !== id));
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      }
    }
  };

  const handleTagManagerClose = () => {
    setShowTagManager(false);
    // Refresh tags after closing the manager
    fetchTags();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Tag Manager Modal */}
      {showTagManager && <TagManager onClose={handleTagManagerClose} />}

      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">My Tasks</h1>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowTagManager(true)}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Manage Tags
              </button>
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">{error}</div>
          </div>
        )}

        {/* Filters */}
        <div className="mb-6">
          <TaskFilters
            onFilterChange={handleFilterChange}
            taskCounts={taskCounts}
            availableTags={availableTags}
            initialFilters={currentFilters}
          />
        </div>

        {/* Create Task Button / Form */}
        <div className="mb-8">
          {showForm ? (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Create New Task
              </h2>
              <TaskForm
                onSubmit={handleCreate}
                onCancel={() => setShowForm(false)}
                availableTags={availableTags}
                onCreateTag={handleCreateTag}
                isLoading={isCreating}
              />
            </div>
          ) : (
            <button
              onClick={() => setShowForm(true)}
              className="w-full py-3 px-4 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-blue-500 hover:text-blue-500 transition-colors"
            >
              + Add New Task
            </button>
          )}
        </div>

        {/* Task List */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredTasks.length === 0 && (currentFilters.search || currentFilters.status !== "all" || currentFilters.priorities.length > 0 || currentFilters.tagIds.length > 0 || currentFilters.dueFrom || currentFilters.dueTo) ? (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              No tasks found
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {currentFilters.search
                ? `No tasks match "${currentFilters.search}"`
                : currentFilters.priorities.length > 0
                ? "No tasks match the selected priorities"
                : currentFilters.tagIds.length > 0
                ? "No tasks match the selected tags"
                : currentFilters.dueFrom || currentFilters.dueTo
                ? "No tasks match the selected date range"
                : `No ${currentFilters.status} tasks`}
            </p>
          </div>
        ) : (
          <TaskList
            tasks={filteredTasks}
            onToggle={handleToggle}
            onDelete={handleDelete}
            onComplete={handleComplete}
          />
        )}
      </main>
    </div>
  );
}

export default function TasksPage() {
  return (
    <ProtectedRoute>
      <TasksContent />
    </ProtectedRoute>
  );
}
