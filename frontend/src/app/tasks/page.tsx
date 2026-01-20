"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth, ProtectedRoute } from "@/lib/auth";
import { api, Task, ApiClientError } from "@/lib/api";
import { TaskList } from "@/components/TaskList";
import { TaskForm } from "@/components/TaskForm";
import { TaskFilters, FilterStatus } from "@/components/TaskFilters";

function TasksContent() {
  const { user, logout } = useAuth();
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [currentFilter, setCurrentFilter] = useState<FilterStatus>("all");
  const [currentSearch, setCurrentSearch] = useState("");

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

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // Apply filters client-side for instant feedback
  useEffect(() => {
    let result = [...allTasks];

    // Apply status filter
    if (currentFilter === "pending") {
      result = result.filter((t) => !t.is_completed);
    } else if (currentFilter === "completed") {
      result = result.filter((t) => t.is_completed);
    }

    // Apply search filter
    if (currentSearch) {
      const searchLower = currentSearch.toLowerCase();
      result = result.filter((t) =>
        t.title.toLowerCase().includes(searchLower)
      );
    }

    setFilteredTasks(result);
  }, [allTasks, currentFilter, currentSearch]);

  const handleFilterChange = useCallback(
    (status: FilterStatus, search: string) => {
      setCurrentFilter(status);
      setCurrentSearch(search);
    },
    []
  );

  const taskCounts = {
    all: allTasks.length,
    pending: allTasks.filter((t) => !t.is_completed).length,
    completed: allTasks.filter((t) => t.is_completed).length,
  };

  const handleCreate = async (title: string, description: string) => {
    setIsCreating(true);
    try {
      const newTask = await api.createTask({
        title,
        description: description || undefined,
      });
      setAllTasks((prev) => [newTask, ...prev]);
      setShowForm(false);
    } finally {
      setIsCreating(false);
    }
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">My Tasks</h1>
            <div className="flex items-center space-x-4">
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
        ) : filteredTasks.length === 0 && (currentSearch || currentFilter !== "all") ? (
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
              {currentSearch
                ? `No tasks match "${currentSearch}"`
                : `No ${currentFilter} tasks`}
            </p>
          </div>
        ) : (
          <TaskList
            tasks={filteredTasks}
            onToggle={handleToggle}
            onDelete={handleDelete}
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
