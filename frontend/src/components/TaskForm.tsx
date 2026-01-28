"use client";

import { useState } from "react";
import { Tag, RecurrenceInput } from "@/lib/api";
import { PriorityPicker } from "./PriorityPicker";
import { TagPicker } from "./TagPicker";
import { RecurrencePicker } from "./RecurrencePicker";

export interface TaskFormData {
  title: string;
  description: string;
  priority: number;
  due: string | null;
  tagIds: string[];
  recurrence: RecurrenceInput | null; // Phase 5 - US4
}

interface TaskFormProps {
  initialTitle?: string;
  initialDescription?: string;
  initialPriority?: number;
  initialDue?: string | null;
  initialTagIds?: string[];
  initialRecurrence?: RecurrenceInput | null;
  availableTags?: Tag[];
  onSubmit: (data: TaskFormData) => Promise<void>;
  onCancel?: () => void;
  onCreateTag?: (name: string) => Promise<Tag>;
  submitLabel?: string;
  isLoading?: boolean;
  showRecurrence?: boolean; // Hide for editing existing tasks
}

export function TaskForm({
  initialTitle = "",
  initialDescription = "",
  initialPriority = 3,
  initialDue = null,
  initialTagIds = [],
  initialRecurrence = null,
  availableTags = [],
  onSubmit,
  onCancel,
  onCreateTag,
  submitLabel = "Create Task",
  isLoading = false,
  showRecurrence = true,
}: TaskFormProps) {
  const [title, setTitle] = useState(initialTitle);
  const [description, setDescription] = useState(initialDescription);
  const [priority, setPriority] = useState(initialPriority);
  const [due, setDue] = useState(initialDue || "");
  const [tagIds, setTagIds] = useState<string[]>(initialTagIds);
  const [recurrence, setRecurrence] = useState<RecurrenceInput | null>(initialRecurrence);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!title.trim()) {
      setError("Title is required");
      return;
    }

    if (title.length > 255) {
      setError("Title must be 255 characters or less");
      return;
    }

    try {
      await onSubmit({
        title: title.trim(),
        description: description.trim(),
        priority,
        due: due || null,
        tagIds,
        recurrence,
      });
      if (!initialTitle) {
        // Reset form only for new tasks
        setTitle("");
        setDescription("");
        setPriority(3);
        setDue("");
        setTagIds([]);
        setRecurrence(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-md bg-red-50 p-3">
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}

      <div>
        <label
          htmlFor="title"
          className="block text-sm font-medium text-gray-700"
        >
          Title <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="title"
          name="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={255}
          required
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
          placeholder="What needs to be done?"
        />
        <p className="mt-1 text-xs text-gray-500">{title.length}/255</p>
      </div>

      <div>
        <label
          htmlFor="description"
          className="block text-sm font-medium text-gray-700"
        >
          Description
        </label>
        <textarea
          id="description"
          name="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          maxLength={4000}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
          placeholder="Add more details (optional)"
        />
        <p className="mt-1 text-xs text-gray-500">{description.length}/4000</p>
      </div>

      {/* Phase 5: Priority Picker */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Priority
        </label>
        <PriorityPicker
          value={priority}
          onChange={setPriority}
          disabled={isLoading}
        />
      </div>

      {/* Phase 5: Due Date */}
      <div>
        <label
          htmlFor="due"
          className="block text-sm font-medium text-gray-700"
        >
          Due Date
        </label>
        <input
          type="datetime-local"
          id="due"
          name="due"
          value={due}
          onChange={(e) => setDue(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
        />
      </div>

      {/* Phase 5: Tags */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tags
        </label>
        <TagPicker
          selectedTagIds={tagIds}
          onChange={setTagIds}
          availableTags={availableTags}
          onCreateTag={onCreateTag}
          disabled={isLoading}
        />
      </div>

      {/* Phase 5 - US4: Recurrence */}
      {showRecurrence && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Recurrence
          </label>
          <RecurrencePicker
            value={recurrence}
            onChange={setRecurrence}
            disabled={isLoading}
          />
        </div>
      )}

      <div className="flex justify-end space-x-3">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
